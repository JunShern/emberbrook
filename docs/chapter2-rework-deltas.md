# Chapter 2 rework deltas — scaffold-town paintings vs. script §(a) + expansion §(a)

The Dellhollow scaffold-town rebuild is final. Every painting is anchored to the approved
master `public/assets/refs/dellhollow-master-6b.png` (BINDING: stone ONLY in the dam/locks
masonry; the village is painted timber on rickety interleaved scaffold platforms; hull-paint
colors, laundry, bunting, lantern-strings; autumn light; ordinary lamps only; no
Heartlight/shrine; no people, no text). Where the paintings landed POIs/exits at different
coordinates than `docs/chapter2-dellhollow-script.md` §(a) or
`docs/chapter2-expansion-script.md` §(a), THESE values override both docs **and override
`docs/chapter2-scene-deltas.md` + `docs/chapter2-expansion-deltas.md` for the reworked
scenes** (`dellhollow`, `stairs`, `cottage`, `vista`). Old coordinates for these four scenes
are VOID, including the previously "proven" (210, 110) dellhollow west-entry spawn (that was
the rope-bridge deck of the retired painting — now open water/village). `descent`,
`lockfive`, `landing` are untouched; their delta docs stand.

Pre-rework paintings, maskraws and bake.json files are parked in each scene's
`candidates/pre-rework-*`.

## ⚠ THE COTTAGE ENTRANCE HAS MOVED — engine edits required (read first)

The keepers' house is no longer a door on the stair-street. In the reworked `dellhollow`
painting the keepers' house is a **stilt-house standing on tall trestles directly over the
lock tailwater** (880–1075, 330–495), with a railed deck at (890–1070, 440–495). The
`cottage` interior connects HERE, not to `stairs`.

1. **`stairs` loses its cottage exit** — expansion §(a) `stairs.exits[2]` (the cottage door)
   is VOID. There is no keeper door in the stairs painting.
2. **`dellhollow` gains the cottage exit** — see the dellhollow exit table below.
3. **Maren's supper-call line MUST change** (expansion §c `playSupperCall`):
   `'It's the low door on the stair-street — the one with the gates carved over.'`
   → suggested: `'It's the house over the locks — the one up on the trestles. You can't miss
   it; the river runs right under the floor.'`
4. **Vesper's cottage-door deniedLine** (`'A door with lock-gates carved over it. Keepers
   live here. We haven't been asked.'`) — no carved lintel is readable at painting scale.
   Suggested: `'A keeper's house, on keeper's stilts, over the keeper's own water. We
   haven't been asked.'` The `cottagedoor` interact texts referencing the carved
   lock-gate lintel need the same surgery.
5. **storyMarker for `supperCalled && !supperDone`**: mark the keeper deck in `dellhollow`
   at **(985, 445)**; the stairs-scene marker from expansion §(d) is VOID.
6. Supper-exit player placements (expansion §c run block) move to the keeper deck in
   `dellhollow`: vesper **(940, 470, 'down')**, lake **(1020, 475, 'down')** — then down the
   deck stair; `Field.enter('dellhollow')`, not `('stairs')`.

## dellhollow — the gorge town (KEPT: prior agent's rework painting, verified)

Painting: plank-street town on scaffold platforms; black-masonry lockhead center; the only
stone in frame is the dam/locks. Same palette/architecture as master-6b (green hall = the
master's green house family, blue row upper-right, red houses lower-right, bunting strings,
autumn rims).

Exits (all mouths mask-verified green):
- **West → `stairs`** (the stair-street): zone `{ x: 0, y: 660, w: 50, h: 108 }` at the
  lower-dock west edge; spawn arriving from stairs: **(85, 700, 'right')**. The doc'd
  west-bridge zone {0,90,60,70} and spawn (210,110) are VOID (no bridge in this painting).
  Night denial + Maren's "up the switchbacks" line live on the STAIRS top exit, per
  expansion §(a).
- **Deep stairs → `lockfive`**: stairhead at (1000–1150, 550–620), broad painted staircase
  descending off the bottom edge; zone `{ x: 980, y: 700, w: 150, h: 68 }`; spawn arriving
  from lockfive: **(1050, 620, 'up')**. (Lockfive-side zone/spawn unchanged.)
- **Keeper door → `cottage`**: door on the stilt-house face at (960–1010, 400–455); exit
  zone `{ x: 950, y: 428, w: 80, h: 62 }` (players stop visually at the door — the deck in
  front is walkable); enabled per expansion supper gating; spawn arriving from cottage:
  **(985, 480, 'down')** on the keeper deck.

POIs (painted reality; interact mouths BFS-verified):
- **Upper pool + rafted queue**: (440–680, 170–290) — moored boats/barges lashed together
  below the far cliff, bunting strung over. **Pumpkin barge** at (520–580, 200–230), barge
  (505–590, 195–235); interact from the quay walk **(505, 275)**, r80. More pumpkins piled
  at the market bins (195–335, 285–363) — Hobb's offloaded overflow, sells the 19 days.
- **Lockhead**: black stone lock towers (620–840, 230–560) with timber gates, ladders at
  (700–780, 300–560), waterfalls (590–840, 400–660). **Waterwheels** at (555–645, 495–620)
  and (855–935, 380–480), turning in the bypass races.
- **THE TALLY BEAM**: the great balance beam spanning (560–810, 205–245) over the lock-top
  crossing, **chalk tally marks clearly painted** along (610–800, 210–240) — big hand's row
  and smaller marks. Interact from the crossing below: **(700, 290)**, r80. Beat 4 cam:
  `{ x: 700, y: 250, viewH: 420 }` frames the marks.
- **Guildhall / guild-deck**: the green timber hall (100–350, 40–260) with railed gallery
  (185–345, 190–235); door + steps at (240–300, 270–310). **Odessa's ruling stages on the
  market forecourt** at **(340, 440)** (cam angles up at the hall, then down the gorge —
  `{ x: 700, y: 400, viewH: 620 }` for the lock reveal). The gallery itself is dressing
  (not masked).
- **Market row / plank-street**: crate stalls (390–570, 400–500) on the main platform;
  chestnut **brazier** (295–387, 352–422, steaming, blocked); awning stalls to the west
  edge (0–200, 280–520). Market stage point **(445, 525)**. **Eel-stall**: no signage
  painted (no-text rule) — nearest analog is the market stall crates at (500–570, 410–480),
  interact **(510, 505)**, r75; engine text carries the eels (Mochi's fixation unharmed).
- **Lamp-pole** (Pell's station): pole with lantern at (245–265, 415–545), head **(255,
  430)**, interact base **(270, 545)**, r70. Ladder-and-wick-knife texts carry as-is.
- **Dock edge + bench**: lower dock (60–450, 640–768); **bench** at (185–300, 675–745),
  interact **(280, 680)**, r75. **Night dock scene stages here**: seat marks (250, 690) and
  (310, 695), Mochi between; cam `{ x: 320, y: 640, viewH: 460 }`. Dock lamp on piling at
  (675–700, 595–665), head (688, 610).
- **Keeper's house**: stilt-house (880–1075, 330–495) over the tailwater; deck (890–1070,
  440–495); deck stage point **(985, 470)**. See the relocation block above.
- **East terrace**: (1180–1330, 400–470), linked by the painted stair (1080–1180, 405–465);
  stage point (1230, 435) (useful for crowd staging; blue-house row above is dressing).
- **Rope bridge / crane / notice board from the old delta doc: VOID** — not in this
  painting. The `ropebridge` interact (expansion §c) is VOID; suggested replacement at the
  same slot: `queueline` at the quay walk (505, 275) is already the barge interact — or
  simply cut.
- Lamps (ordinary, no id, lit at night): heads **(255, 430), (600, 320), (688, 610)**;
  lantern-string/bunting glow lines across the upper gorge at (450–700, 120–180) and the
  east terrace bunting (1030–1200, 260–300) — suggested string glow points (500, 150),
  (620, 160), (1100, 280).

Mask: bake center [250, 480]. Authored corridors (the scaffold-scene recipe): quay walk
(420–620 × 262–310), lock-top crossing (600–860 × 255–310), east trestle stair down
(830–905 × 272–467 — hugs the painted trestles; crosses the wheel-race spray for ~40px,
accepted), keeper's deck (875–1080 × 442–497), deck-to-stairhead (995–1050 × 470–590), deep
stairs (980–1100 × 560–768), market-to-dock gangway (330–400 × 540–720), lower dock front
(100–660 × 668–720), south boardwalk (640–1060 × 712–760), west dock mouth (0–110 ×
670–730), east terrace stair (1080–1190 × 405–465). blockedRects: pumpkin bins, brazier.

## stairs — the scaffold vertical connector (KEPT: prior agent's rework painting, verified)

Painting: the town *around* you at boot height — one big zigzag plank stair between tiers,
decks over decks, ladders and trestles, the black lock masonry mid-right (the only stone),
bakery house left, vendor deck right. Same town as the master (bunting, blue row upper
right, autumn rims, gorge behind).

Exits (mouths mask-verified green):
- **Top → `descent`**: stair climbing to the top edge at (940–1050, 0–110); zone
  `{ x: 940, y: 0, w: 110, h: 70 }`; spawn arriving from descent: **(990, 120, 'down')**.
  Night denial + Maren's deniedLine here, per expansion §(a). (Expansion's arch at
  (740–880, 0–120) is VOID — no arch painted.)
- **Bottom → `dellhollow`**: the foreground deck runs off the bottom edge at (340–620,
  700–768); zone `{ x: 340, y: 700, w: 280, h: 68 }`; spawn arriving from dellhollow:
  **(470, 690, 'up')**.
- **No cottage door** — see the relocation block. Expansion `stairs.exits[2]` VOID.

POIs / interacts (mouths BFS-verified):
- **Sorrel's bread-window**: warm-lit hinged counter (95–290, 380–560), loaves on the
  shelf, striped awning above (100–330, 260–360), green bakery door (200–285, 300–440).
  Sorrel's station behind the counter **(190, 500)** (off-mask, Poppy pattern, larger
  radius); player mouth **(300, 650)**, r85.
- **Public cistern**: spout-fed water barrel (760–880, 505–700), timber pipe (690–800,
  480–515), hanging pan — reads perfectly as the bypass-race cistern; the tin-cup text
  lands. Interact **(880, 650)**, r75 (barrel is a blockedRect). The stone-basin wording
  from the expansion deltas is VOID (it's a barrel now — engine text says "cistern", fine).
- **Vendor spots (deck-mounted)**: fish-drying racks (1090–1300, 480–620), goods crate
  (995–1085, 530–590), pepper strings (1060–1130, 370–500), tri-color awning (1090–1344,
  280–410), rope coil (1280–1344, 580–660). Vendor-deck stage/interact **(1150, 620)**,
  r80. Suggested stations: Old Creel **(1160, 650)** by the rope coil (his splices, his
  step); Nib **(1010, 690)** by the chalk gull.
- **Kids' chalk**: hop-grid on the lower deck (360–560, 630–760), interact **(460, 680)**,
  r70; **rude (but accurate) chalk gull** at (1030–1180, 680–750), interact **(1100,
  700)**, r70 — this absorbs the hoist-wall gull line.
- **Laundry/bunting overhead**: strings at (590–780, 90–180), flag line over the lock
  (830–1050, 330–390), pennants (1050–1344, 0–45). Look-up interact from the mid landing
  **(400, 390)**, r70.
- **Landings** (social floors, all masked): mid landing (330–550, 290–400), upper walkway
  (560–880, 175–240), lower deck (90–700, 560–768), vendor deck (940–1344, 480–768),
  cistern platform (640–980, 620–730).
- **Lock bridge**: trestle footbridge (930–1100, 425–500) crossing toward the black lock
  masonry — dressing route, no exit; stage point (1000, 460).
- **VOID interacts from expansion §(a)/(c)**: `gullrail` (no live gulls painted — the
  chalk gull replaces it; retext or cut) and `hoist` (no barrel-hoist painted — its rude
  gull drawing moved to the deck chalk; cut the interact, keep the line in the chalk-gull
  text if wanted).
- Lamps (no id, lit at night): posts along the upper walkway, heads **(475, 125),
  (605, 112), (742, 130)**; string glow points suggested (650, 150), (950, 350) under the
  lock flag-line. Night: same painting + tint, windows warm, bread-window dark.

Mask: bake center [450, 620]. Authored corridors: top exit stair (940–1050 × 0–130), upper
stair link (850–970 × 95–215), upper walkway (560–880 × 175–240), upper zigzag flight
(450–670 × 215–320), mid landing (330–550 × 290–400), lower flights to deck (440–670 ×
370–600), cistern platform join (640–980 × 620–730), lock bridge deck (930–1100 × 430–500),
bridge-to-vendor steps (1000–1090 × 490–600), quay-gate mouth (340–620 × 700–768).
blockedRects: cistern barrel, planter box.

## cottage — the keeper's stilt-house interior (PAINTED: 1 roll, accepted)

Timber walls, timber floor, hearth-lit, the river under the boards — and an **open deck
over dark moving water** built into the layout: the right wall opens through a full-height
doorway (1040–1344, 80–720) onto a railed deck (rail 1080–1344 × 300–500, deck floor
1050–1344 × 500–730) over the gorge water, tiny boats below. **Accepted deviation: the
hearth chimney-breast is masonry** (505–700, 30–460) — the one stone thing in a timber
house, fire-safety logic, same grey-black family as the locks; walls/floor are all timber
per the binding rule.

Exit: front door left (30–180, 80–560); zone `{ x: 40, y: 570, w: 190, h: 120 }` →
`dellhollow`, spawn **(985, 480, 'down')** on the keeper deck. Spawn arriving from
dellhollow: **(140, 600, 'right')**.

ALL FIVE storytelling props painted and verified in-frame:
- **Height-tally doorframe**: small tick marks climb the door's RIGHT inner frame
  (183–196, 130–330), **stopping well below the lintel**. Interact **(195, 560)**, r75.
  Supper cam for the marks: `{ x: 380, y: 400, viewH: 520 }` (the expansion's
  {420,480,460} clips them — use this instead).
- **Father's oilskin coat**: on the peg board (215–330, 185–470), hung square, **empty
  hook beside it** (300–320, 188–210) for Lake's cloth. Interact **(275, 540)**, r70.
- **Locked chart drawer**: nightstand/dresser (340–508, 372–517), brass-keyhole drawer
  face (390–480, 400–450), keyhole at (438, 413); PLUS a keyholed gate-green chest sitting
  on top (405–465, 335–375) that reads as the chart case. **No key painted anywhere
  (verified).** Interact **(430, 560)**, r75.
- **Eel-spears + winch parts**: spears racked (885–990, 55–330) beside gears + chain
  (780–885, 130–370) and long tools (700–780, 100–420). Interact mouth **(1000, 690)**,
  r80 — NOTE: the floor at the wall's base is behind the table (blocked wholesale, stage-3
  rule); the player looks from south-east of the table.
- **Table + seats**: round table (665–975, 400–580); **two dark worn chairs + one pale
  stool (742–850, 565–693), visibly the newest wood in the room** — the old painting's
  four-seat deviation is gone; this matches §(a) exactly. Interact **(880, 700)**, r80.
- **Hearth**: stew-pot on its hook (600–655, 355–440), fire lit. Interact **(530, 570)**,
  r80 — still the supper trigger.

Color spec landed: teal/red glazed bowls + jug on the table (770–895, 370–455), red bowl on
the nightstand shelf, gate-green tin, striped rag rug (60–330, 535–660), dried peppers
(445–495, 100–290), autumn window (325–435, 115–280). The kept things (tallies, coat,
drawer, stool) are bare oiled wood, per spec.

Staging (walkable, around the blockedRects): Odessa at the pot **(530, 560, 'up')**;
supper: vesper **(620, 690, 'up')**, lake **(980, 690, 'up')**, maren THE STOOL **(800,
720, 'up')**, mochi the doorstep **(120, 640, 'right')**. Checkpoint-4 players **(450,
680) / (660, 720)**. Deck stage point (moonlight/deck beats if wanted): **(1180, 620)**.

Mask: bake center [700, 650]; corridors: door threshold, deck doorway; blockedRects:
table, both chairs, stool, nightstand.

## vista — the valley from above (PAINTED: 4 rolls; roll 4 accepted; cutscene-only, NO mask)

Re-matched to the scaffold town: same architecture/palette as master-6b at a mile out.
Do **not** add `vista` to the bake list; no mask.png/maskraw.png/bake.json exists (by
design). Layout (positions for the `playValley` pan):

- **River in from the south, upper-left**: calm water entering behind the upper pool.
  **Rafted queue pooled ABOVE the locks**: colorful hulls lashed together (330–560,
  195–300); **pumpkin barges at the head of the queue** at the lockhead (455–660, 310–400)
  — orange rows clearly readable; the barges below the locks are plain/empty (nothing has
  passed the jam — verified).
- **Lock staircase, clearly stepped, 3 explicit chambers**: top gate row + falls (415–560,
  290–390); mid chamber with balance beams + falls (540–830, 390–510); lower falls
  (600–830, 500–630) into the steaming tailwater basin (700–1000, 560–700); further steps
  implied down-gorge, dissolving right into layered golden haze.
- **Village ribbons down BOTH walls**: near/west wall scaffold stacks (0–430, 60–620), far/
  east wall (720–1344, 0–620) — stilts, platform-on-platform, ladders, hull-paint red/
  green/teal/ochre/blue flecks; laundry + bunting threads; stone only in the dams.
- **Woodsmoke** columns leaning one way (right): ~(230, 90), (460, 180), (690, 140),
  (860, 240), (1240, 400).
- **River out north**: winds off the top-right (1050–1344, 80–260) into haze. Tiny plain
  barges on the lower river (1040–1140, 360–560).
- **Foreground rim anchor** bottom-left: rock, wind-bent grass, wheel-rut road (0–520,
  560–768). No figures, no text (verified; small pale gulls only).

**Pan path (REPLACES both prior tables — clamped, viewH-safe):**

| Order | Camera rect (`cam`) | What it frames |
|---|---|---|
| start | `{ x: 470, y: 290, viewH: 520 }` | river in, rafted queue, pumpkin barges, top lock |
| mid | `{ x: 672, y: 420, viewH: 560 }` | the lock staircase, town down both walls |
| end | `{ x: 1040, y: 400, viewH: 560 }` | tailwater steam, lower river, the north haze |

## Gate B numbers (final baked masks)

- `dellhollow`: coverage **27%**, 4 components, largest holds **97%** of green (3 satellite
  specks, none holding a POI/spawn); all 3 exit mouths green; **0 clearance carves**.
- `stairs`: coverage **32%**, **1 component = 100%** of green; both exit mouths green;
  **0 clearance carves**.
- `cottage`: coverage **28%**, **1 component = 100%** of green; exit mouth green;
  **0 clearance carves**.
- All three ≥ the 25% floor (no waiver needed this time).

## BFS results (final mask.png, 4-connected, ±3-cell tolerance as in the baker)

- `dellhollow` — 13 points, 78 pairs, **ALL CONNECT** (single main component): west mouth
  (25,700), quay/barge (505,275), tally beam (700,290), guild forecourt (340,440), market
  (445,525), eel-stall (510,505), lamp-pole (270,545), bench (280,680), dock stage
  (400,690), keeper deck (985,470), stairhead (1050,590), deep mouth (1040,720), east
  terrace (1230,435).
- `stairs` — 10 points, 45 pairs, **ALL CONNECT**: top mouth (990,60), quay mouth
  (470,720), bread (300,650), cistern (880,650), vendor (1150,620), hop-grid (460,680),
  chalk gull (1100,700), mid landing (400,390), upper walkway (640,210), lock bridge
  (1000,460).
- `cottage` — 8 points, 28 pairs, **ALL CONNECT**: door mouth (110,600), tallies (195,560),
  coat (275,540), drawer (430,560), hearth (530,570), table (880,700), toolwall (1000,690),
  deck (1180,620).
- No hand-edited masks; everything is `tools/bakemask.py` output from the authored
  `bake.json` in each scene dir. Composite overlays (mask over painting) checked by eye:
  walkability follows decks/stairs/quays; brazier, bins, cistern barrel, planter and all
  cottage furniture blocked; no leaks onto roofs, water or the gorge (the east-trestle
  corridor clips ~40px of wheel-race spray while hugging the painted trestles — accepted).

## Rolls / verification summary

- `dellhollow` main.png: prior agent's rework painting **KEPT** (judged vs master-6b: same
  town, same palette, scaffold logic holds; all story needs present — market, lockhead +
  painted chalk TALLY BEAM, rafted queue + pumpkin barge, guild hall + forecourt, deep
  stairs, dock bench, lamp-pole, keeper's stilt-house with reachable deck/door).
- `stairs` main.png: prior agent's rework painting **KEPT** (vertical connector reads; all
  needs present — tiered plank stairs/ladders, bread-window, cistern, vendor deck, top and
  bottom exits).
- `cottage` main.png: prior agent's unjudged `candidates/rework-roll1.png` **ACCEPTED and
  promoted** (all five props + open deck verified; masonry hearth = accepted deviation).
- `vista` main.png: 4 rolls this session — roll 1 rejected (master re-render, one dam step,
  no valley); roll 2 rejected (same failure, ref-locked); roll 3 (style-translation of the
  parked pre-rework vista composition) good but pumpkin cargo below the locks; roll 4 =
  roll 3 + queue/cargo corrective edit, **ACCEPTED**.
- maskraws: 1 roll each (dellhollow, stairs, cottage), all accepted first try.
- Generations charged this session: **7** (4 vista + 3 maskraw), under the 10 cap.
- `public/js/bake-core.js` bake list: keep `'stairs', 'cottage'` (already present per the
  expansion), NOT `vista`. Manifest rebuilt via `node tools/build-manifest.mjs`.
