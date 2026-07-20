# CHAPTER TWO — "Dellhollow" — complete script

Design + script source for the new `public/js/chapter2.js` (the current Lanternstead
implementation becomes Chapter Three; its script now lives at
`docs/chapter3-lanternstead-script.md`). Written against the Chapter One vocabulary
(`public/js/chapter1.js`), the story bible (`STORY.md` — §7 register rules are law), and the
ratified Dellhollow outline, which is authoritative over the copy of STORY.md on disk (a
concurrent rewrite is landing the outline there).

**Register law, restated for this chapter:** Dellhollow is a *normal flameless town* — no
Heartlight, no keeping-flame, ordinary oil lamps lit by anyone. It is alive, loud, four
hundred years old, and holds together on nothing but people. Nobody in Dellhollow knows
lamp-lore; nobody explains anything; the town runs on human themes (rivers, manners, grief,
trade). The Stranger is never named. The quiet lower banks get one soft line and no reaction.
Vesper's fog is ordinary immigrant-parent haziness and is **never** described in Hush-anatomy
terms (forbidden before Chapter Five). Nobody in Dellhollow says the word "afraid" — the town
is *polite to the river*, and corrects anyone who suggests otherwise.

**Continuity contract, both ends:**
- *From Chapter One:* the chapter opens the morning after the gate — same pair, same cat, the
  grey road north. The old "walked until the last light of Emberbrook was gone behind them"
  narrate (written for this position) opens **this** chapter now — see Beat 1.
- *Into Chapter Three:* Dellhollow ends going **north on the river**, party of three plus cat,
  in the boat. Chapter Three (Lanternstead) cold-opens on the grey Order road on foot. The
  bridge is a river-landing narrate at the top of Chapter Three — exact proposed text and the
  full seam list are in **§(h)** at the end of this document. The engine agent must apply §(h)
  when renumbering.

Chapter flags (suggested):

```js
flags: {
  descentIntro: false, chartDone: false, strangerSeen: false,
  arrived: false, talked: {}, jamDone: false, marenDone: false,
  lockSeen: false, planMade: false, nightFallen: false, dockDone: false,
  boatDown: false, gateHalf: false, gatesOpen: false, flumeDone: false,
  marenJoined: false, ended: false, endT: 0,
  hobbTalk: 0, pellTalk: 0,
}
```

Mechanics budget (per the ratified outline — for the engine agent): **no new systems.**
Town lantern-strings reuse the engine lamp-glow FX (lamp heads with no `id`, toggled lit at
night). The co-op setpiece is `bothHold` twice. The flume run is pure cutscene vocabulary —
`shake` / `flash` / `Particles` sprays / `buzz` / `narrate`. Maren as follower reuses the
Tally follower job from the Lanternstead implementation (`updateFollowers`), offsets as Tally,
`h ≈ 112`.

---

## (a) Scene definitions sketch — for the art pipeline

All coordinates on the 1344×768 canvas, Chapter One conventions (`lamps` have a head `{x,y}`
and, only if hand-lightable, an `id` + interact `base`; exits are edge zones; the baked mask
governs walkability — the `walk` polygon is fallback only).

### `descent` — the switchbacks down from the gate

The grey road north of the Old Gate, half a morning on — and then the road steps off the edge
of the world. Grey-green wood at the top (same palette family as the Ch.1 gate exterior, moths
drifting), opening into cliff: a serious old road cut into the gorge wall in three visible
switchback terraces, top-left down to bottom-center. Along the right edge, a side-**ravine**
splits away — a sheer gap with the old rim road visible continuing on the far side (this is
where the Stranger stands). The bottom edge of the scene is the **rim vista**: a low parapet,
and beyond/below it (painted as deep background falling off the frame's lower edge) the first
glow and haze of Dellhollow — lantern-strings, smoke, the tops of the great locks. The vista
is the scene's lower edge; the reveal is a cutscene cam move, not a separate painting.

```js
descent: {
  states: { gray: 'assets/scenes/descent/main.png' }, state: 'gray',
  maskSrc: 'assets/scenes/descent/mask.png',
  viewH: 700, charH: 120, speed: 190, mothAmbience: true,
  tints: { gray: '#9aa393' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
  blocked: [],
  exits: [
    { zone: { x: 60, y: 0, w: 240, h: 80 }, to: null,               // south — back up to the Gate
      enabled: () => false,
      deniedLine: ['lake', 'Back up to the Gate? Not with the spark this side of it. The rounds only go one way now.'] },
    { zone: { x: 520, y: 704, w: 300, h: 64 }, to: 'dellhollow', spawn: [210, 165, 'down'],
      enabled: () => Chapter2.flags.strangerSeen,
      deniedLine: ['vesper', 'Not yet. The world and my sheet are having a disagreement, and I intend to referee it before we lose the light.'] },
  ],
}
```

Points of interest (must be in the painting):
- **Road path**: enters top-left at (120, 140); first terrace runs right to a hairpin at
  (1130, 300); second terrace back left to a hairpin at (240, 520); third terrace down to the
  vista parapet centered (672, 720). Dressed stone under moss — *built*, not worn.
- **The ravine**: right edge, x ≳ 1180, between y ≈ 100–380 — mask-blocked air. The far rim
  road is painted across it; the **Stranger's mark** is (1270, 210): a clear, empty, framed
  stretch of far-rim road (trees pull back). Reuses the Ch.1 `stranger` sprite at distance
  (h ≈ 110). He carries something at his side that catches the light — paint an ambiguous
  glint, **not** a readable blue lantern; the clear look at the lantern is Chapter Three's.
- **Empty lamp bracket** at (980, 280), interact base (980, 360): an Order-pattern wall
  bracket, empty, unbolted clean. (Do NOT paint a recognizable Order lamp here — Lake's
  "same pattern as ours" discovery belongs to Chapter Three, Beat 1.)
- **Chart halt** — a flat waist-high boulder at (450, 330) on the first terrace where the
  map-is-wrong beat stages; after the beat it carries an interact (Vesper's field correction).
- **Vista parapet** at (672, 730), interact radius ~90: the overlook.
- Moths drift the upper wood; **thin the ambience toward the bottom third** — the gorge is
  not moth country (design note, unremarked in dialogue: keep Dellhollow moth-free so the
  Lanternstead swarm stays the story's first).

### `dellhollow` — the gorge town

The money painting. A working river town stacked down both cliffs of the gorge, stitched
across with rope bridges, cranes, and **lantern-strings** (ordinary oil lamps — NO Heartlight,
no pedestal, nothing sacred; a lamp-pole and ladder where a shrine would be in a flame
village). The river enters top-left as the **upper pool**, where the stopped traffic waits:
**queued boats rafted together** three and four deep, including the pumpkin barge. Five great
timber locks step the water down the gorge — **paint the upper three** (gates, beams,
waterwheels), the lower two implied below the frame's lower-right, where the gorge falls into
haze. Market row runs along the quay mid-frame; the guildhall presides upper-right; the deep
stairs exit lower-right. Day state: warm autumn light in a cold gorge, woodsmoke, laundry,
gulls. Night state: same painting, night tint, lantern-strings lit (engine lamp-glow).

```js
dellhollow: {
  states: { day: 'assets/scenes/dellhollow/main.png',
            night: 'assets/scenes/dellhollow/main.png' }, state: 'day',
  maskSrc: 'assets/scenes/dellhollow/mask.png',
  viewH: 720, charH: 118, speed: 190,
  tints: { day: '#c9ab86', night: '#66708c' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
  blocked: [],
  lamps: [   // lantern-strings: ordinary lamps, engine glow only; no id (never hand-lit); lit at night
    { x: 300, y: 250, lit: false }, { x: 470, y: 285, lit: false }, { x: 640, y: 255, lit: false },
    { x: 420, y: 470, lit: false }, { x: 600, y: 500, lit: false }, { x: 780, y: 470, lit: false },
    { x: 1010, y: 350, lit: false },
  ],
  exits: [
    { zone: { x: 100, y: 0, w: 260, h: 80 }, to: 'descent', spawn: [640, 640, 'up'],
      enabled: () => !Chapter2.flags.nightFallen,
      deniedLine: ['maren', 'Up the switchbacks at THIS hour? Nothing up there but weather. Everything worth anything is down.'] },
    { zone: { x: 1180, y: 560, w: 164, h: 168 }, to: 'lockfive', spawn: [1230, 240, 'down'],
      enabled: () => Chapter2.flags.marenDone,
      deniedLine: ['odessa', 'The deep stairs are lock business. Nobody walks them without my say — or my daughter.'] },
  ],
}
```

Points of interest (must be in the painting, approximate positions):
- **Upper pool + rafted queue**, (140–430, 150–340): moored boats lashed hull to hull; gang
  planks; washing strung between masts — the queue has become a neighborhood. **Pumpkin
  barge** at (270, 320) (interact (300, 380)): low freight barge, forty tons of pumpkins in
  elegant, faintly slumping rows.
- **Lock One** gates and beam at (470, 260); **Lock Two** at (760, 400); **Lock Three** at
  (1020, 540) — each a pair of great timber gates with balance beams, chained shut, chalk
  marks on the beams. **Waterwheels** at (700, 300) and (880, 430), turning (the bypass races
  still run — the town has power, just no passage).
- **The tally beam** — Lock One's near balance beam, interact at (880, 340): a fathom of
  grey chalk tallies low down (a big hand's), fresher charcoal tallies climbing above (a
  smaller hand's). Beat 4 stages against it.
- **Market row / quay**, (350–820, 480–620): fish stalls, chestnut brazier, rope-walk, the
  **eel-stall** at (430, 540) (Mochi's fixation), crane at (820, 440).
- **Guildhall** upper-right, (960–1220, 280–440), door at (1080, 420): timber hall with a
  lock-gate carved over the lintel. No interior scene (three-scene budget) — Beat 3 stages on
  the lockhead terrace outside. **Notice board** at (1010, 480).
- **Lamp-pole** at (620, 560): Pell's station — pole, ladder, wick-knife on a string.
- **Deep stairs** lower-right, (1200, 580) down: black timber stairhead, rope handrail,
  "LOCK BUSINESS ONLY" burned into the newel.
- **Dock edge** at (540, 640): bollards and a bench — the night dock scene stages here.

### `lockfive` — the deep chamber

A wet cathedral that works for a living. Black timber walls going up out of lantern-reach,
chains hanging from the dark like bell-ropes (one set holds the shrouded shape of a small
boat, hoisted high over the water — paint it discreet, readable on second look). The flooded
lock chamber fills the left/center: still black water, and in it, visible, **THE TENANT** —
the enormous river eel, mottled moss-bronze, laid around the chamber in two easy coils, one
pale clouded eye toward the viewer. In the left wall, low over the water: the **sealed sluice
gallery** — a timber-and-iron grate with dark weed packed through its bars. In the right/rear
cliff wall, above the waterline: the **flume mouth** — a round timber-ringed tunnel, dry and
dark, big enough to swallow a boat, with **twin seized winches** crouched on the apron before
it under a century of grease and rust. Walkable area: an L-shaped stone apron along the
bottom and right of the pool. Two hooked work-lanterns light the apron (engine glow).

```js
lockfive: {
  states: { dim: 'assets/scenes/lockfive/main.png',
            night: 'assets/scenes/lockfive/main.png' }, state: 'dim',
  maskSrc: 'assets/scenes/lockfive/mask.png',
  viewH: 700, charH: 120, speed: 180,
  tints: { dim: '#5f6b70', night: '#454e5e' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs (L-shaped apron)
  blocked: [],
  lamps: [ { x: 260, y: 300, lit: true }, { x: 1140, y: 300, lit: true } ],  // work-lanterns, always lit
  exits: [
    { zone: { x: 1180, y: 60, w: 164, h: 150 }, to: 'dellhollow', spawn: [1230, 640, 'up'] },
  ],
}
```

Points of interest:
- **The pool**: water spans roughly (280–840, 380–720); mask-blocked. **The Tenant's eye** at
  (560, 540). Interact for the pool from the apron at (600, 690), radius ~90.
- **Sluice gallery grate** in the left wall at (180, 430) — viewed across the water; interact
  from the apron's near corner (310, 680), radius ~80.
- **Flume mouth** at (1120, 280); **winch L** at (990, 520); **winch R** (the "widow") at
  (1200, 560). Interacts at their bases.
- **The chains / hung boat** over the pool at (600, 220): lowered in Beat 6. THE BOAT design
  is in §(b).
- **Stairs** top-right, landing at (1240, 200), climbing off-frame.

### `landing` — the tailwater (cutscene-only backdrop) — *scope ruling, flagged*

The ratified outline names three walkable scenes; Beat 8 ("the landing below") still needs
ground under its feet for staged sprites, toasts, and the embrace. **Ruling:** one additional
*minimal, cutscene-only* scene — a single painting, flat walkable strip, no POIs, no exits;
players never free-roam it (the ending cutscene owns it start to finish, like the Ch.1 gate
finale owns its scene). Cost: one painting + trivial mask. If design rejects the fourth
painting, the fallback is staging Beat 8 as narrate-over-black — noted, and not recommended;
it is the emotional climax of the chapter.

Composition: dawn, pearl light. The tailwater pool left (steam off the water, the flume's
black mouth high in the cliffs behind), an old stone landing with mooring rings right, the
foot of the portage stair at (1050, 420) climbing away, and the river running off the frame
top-left — north. The boat moors at (450, 540).

```js
landing: {
  states: { dawn: 'assets/scenes/landing/main.png' }, state: 'dawn',
  maskSrc: 'assets/scenes/landing/mask.png',
  viewH: 700, charH: 120, speed: 190,
  tints: { dawn: '#c9c2b3' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],
  blocked: [], exits: [],    // cutscene-only; the chapter ends here
}
```

---

## (b) NPC roster — for the character pipeline

### MAREN — new, full design (canonical — verbatim for the art pipeline)

MAREN — 17, wiry, sun-browned, short choppy dark-brown hair tied back with a strip of faded
sailcloth, bright hazel eyes, big ready grin; striped river-shirt (cream/teal) with rolled
sleeves under a faded blue canvas vest, rolled canvas trousers to mid-calf, short lace boots,
cord-and-cork bracelet, CHARCOAL TALLY MARKS up her left forearm. Expressions: happy,
determined, awed. Speaker color suggestion #3fa7c9.

- `happy` — the default: the big ready grin, chin up, usually mid-motion.
- `determined` — jaw set, eyes narrowed on the water; the pilot's face.
- `awed` — eyes wide, grin gone soft; the face she only shows the river (and, twice, her
  mother).

**Speaker entry** (`assets.js`): `maren: { name: 'Maren', color: '#3fa7c9' }`.
**LOOKS row** (pixel sprite): `maren: { hair: '#4a3728', outfit: '#e8e0cd', shade: '#3f7a91',
accent: '#3fa7c9', skin: '#c98d5e', hairstyle: 'short' }` — striped shirt if the baker
supports it; the sailcloth hair-tie is the silhouette read.

### ODESSA — new, full design (canonical — verbatim for the art pipeline)

ODESSA — 50s, broad-shouldered, weathered handsome face, grey-streaked dark hair in a
rope-coil braid pinned up, long oilskin coat over a knit gansey, heavy gloves tucked in her
belt, brass whistle on a cord. Expressions: grave, warm (used once). Color #5a7a8f.

- `grave` — the default and near-only face: the harbormistress reading the river, the town,
  and you.
- `warm` — **used exactly once in this chapter** (the chart handoff, Beat 8). Guard it.

**Speaker entry**: `odessa: { name: 'Odessa', color: '#5a7a8f' }`.
**LOOKS row**: `odessa: { hair: '#5a5148', outfit: '#4f5a52', shade: '#3d4640',
accent: '#5a7a8f', skin: '#d9ab84', hairstyle: 'braid' }`.

### THE TENANT — entity, not a speaker (canonical — verbatim for the art pipeline)

THE TENANT — an enormous river eel, barge-sized, mottled moss-green and bronze, old scars,
one pale clouded eye, whiskered chin; ancient and calm, never monstrous.

Painted into the `lockfive` scene (coiled, eye at (560, 540)); she moves only in cutscene
(ripple FX + narrate, plus one close pass in the flume run — a large sprite/overlay sliding
past the boat is worth the art if cheap; otherwise the narrate carries it). She has no lines;
everything about her goes through `system` and the narrator. She is never a monster and never
a joke.

### THE BOAT — prop (canonical — verbatim for the art pipeline)

THE BOAT — small clinker-built river craft, tar-dark hull, sculling oar, rope fenders, a
lantern hook at the prow.

Appears: hung in the Lock Five chains (shrouded), lowered in Beat 6, run in Beat 7, moored at
the landing in Beat 8, and from Chapter Three's cold open onward as set dressing at the river
landing. Needs one side-on sprite/overlay at scene scale; the flume run is cutscene cam work
over spray FX, not a vehicle system.

### HOBB — the pumpkin-barge captain (sprite-first extra, brief design)

Broad, short, wind-burned; oiled wool cap, patched orange neckerchief (his one vanity, now a
professional irony), fingerless mitts, a barge-pole he leans on like a bar rail. Fifties. A
man watching forty tons of cargo soften in elegant rows, nineteen days into the five stages
of pumpkin grief. **Speaker entry**: `hobb: { name: 'Captain Hobb', color: '#b9873c' }` —
one neutral bust only (no expression variants); sprite + nameplate carry him.

### PELL — the night-watchman (sprite-first extra, brief design)

Long, dry, deliberate; oilskin cape, wide-brimmed hat, wick-knife and horn lantern on his
belt, a ladder never far away. Night-shift eyes at any hour. **Speaker entry**:
`pell: { name: 'Watchman Pell', color: '#8a9a7a' }` — one neutral bust only.

### Returning, no new art
- **stranger** — Ch.1 sprite, once, at far-ravine distance (h ≈ 110). No dialogue. Still no
  dialogue.
- **mochi** — as is. Hiss #1 happens here (text-rendered).
- **vesper, lake** — as is.

---

## (c) Beat-by-beat script

Speaker keys: `vesper / lake / maren / odessa / mochi / system`, plus minor `hobb / pell`
(sprite-first extras; see §b). Expression tags: all existing Ch.1 tags, plus `maren:happy`,
`maren:determined`, `maren:awed`, `odessa:grave`, `odessa:warm`.

### BEAT 1 — The descent: map-is-wrong, the Stranger, the vista (`playDescent`, `playChart`, `playRavine`, `playVista`)

Trigger: chapter start, both players on `descent`, `!descentIntro`. Spawns: vesper
(140, 150, 'down'), lake (200, 130, 'down'), mochi (250, 180, 'down').

```js
Cutscene.play([
  { mood: 'forestB' },
  { banner: { title: '— CHAPTER TWO —', sub: 'Dellhollow', dur: 5 } },
  { cam: { x: 300, y: 260, viewH: 520 } },
  { wait: 1.2 },
  { narrate: 'They walked until the last light of Emberbrook was gone behind them, slept badly under a bramble, and the first morning of winter came up grey and stayed that way.' },
  { narrate: 'Half a morning north of the Gate, the road — old, dressed stone, built by serious people — did something no road on any of Vesper’s charts had ever done. It stepped off the edge of the world.' },
  { move: { ent: mochi, x: 330, y: 240, speed: 150 } },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi sits down at the first switchback and looks back at them, in the manner of a guide waiting for slow clients.)'] },
  { say: ['vesper', 'Switchbacks. Cut switchbacks, Lake — that’s a month of masons per turn. Somebody needed to get down there very badly, a very long time ago.'] },
  { say: ['lake', 'Down where? All I can see is gorge.'] },
  { say: ['vesper', 'Well. That’s the other thing.'] },
  { camRelease: true },
]);
```

**Map-is-wrong** (`playChart`): triggers when either player reaches the chart halt
(y > 280 on the first terrace), `!chartDone`.

```js
Cutscene.play([
  { cam: { x: 500, y: 330, viewH: 460 } },
  { run: () => { /* stage: vesper to the boulder (450, 340), sheet spread; lake beside */ } },
  { say: ['vesper', 'Hold this corner. HOLD it, the wind is a critic.'] },
  { say: ['vesper:worried', 'This is my north sheet — forty years old, surveyed by a man with a theodolite and a reputation. It shows this road running on through open heath. Flat. Six more miles of confident little grass symbols.'] },
  { say: ['lake', 'The road disagrees.'] },
  { say: ['vesper', 'The road is going DOWNSTAIRS. There is a gorge here you could lose a cathedral district in, there is a river at the bottom of it — I can HEAR the river — and my best chart of this whole country says: heath.'] },
  { say: ['lake', 'Maybe the theodolite man never came this far.'] },
  { say: ['vesper', 'Oh, he came. He got tired, or the light went, and he guessed — and then he inked the guess like a survey. The oldest sin in cartography, and forty years of travelers have carried it since.'] },
  { say: ['vesper:determined', '(Pen. Rule of the trade: the map is corrected the day you catch it, or the lie outlives its maker.)'] },
  { say: ['lake', '(Eleven days of impossible things, and the one that finally offends her is bad surveying. Noted. It’s good to know what a person’s actually for.)'] },
  { say: ['mochi', 'Mrrp.'] },
  { run: () => { F.chartDone = true; } },
  { camRelease: true },
]);
```

**The Stranger across the ravine** (`playRavine`): triggers with `chartDone`, either player
past the first hairpin (x > 950 && y > 250), `!strangerSeen`. Canon beat: bows, gone —
**Mochi hiss #1**. No lantern read at this distance (an ambiguous glint only — the clear look
belongs to Chapter Three; see §h seams).

```js
Cutscene.play([
  { mood: 'silence' },
  { run: () => { const s = this.npcs.stranger; s.hidden = false; s.scene = 'descent'; s.x = 1270; s.y = 210; s.dir = 'down'; } },
  { cam: { x: 1130, y: 260, viewH: 520 } },
  { wait: 1.2 },
  { narrate: 'Across the ravine — a stone’s throw away, and an hour’s walk, and no way over — the old rim road ran on north. Somebody was standing on it.' },
  { say: ['vesper', 'Lake.'] },
  { say: ['lake', 'I see him.'] },
  { say: ['mochi', 'Hhhhhhhh.'] },
  { say: ['system', '(A sound is coming out of Mochi that neither of them has ever heard a cat make. Low. Level. Aimed across the gap.)'] },
  { say: ['vesper:worried', '(Tall. Hooded. Standing the way a post stands — like the road grew him. Something at his side keeps catching the light. Glass?)'] },
  { say: ['lake', 'Hello the road! Is there a crossing north?'] },
  { wait: 1.0 },
  { narrate: 'The figure did not answer, and did not wave. It turned to face them across the ravine — and bowed. Deep, and slow, and formal: a bow with rules in it, aimed low, at something carried and not at anyone carrying it.' },
  { wait: 0.8 },
  { flash: 0.4 },
  { run: () => { this.npcs.stranger.hidden = true; Net.send({ type: 'buzz', ms: 120 }); } },
  { narrate: 'Between one blink and the next, the rim road was empty.' },
  { wait: 0.8 },
  { say: ['vesper', 'Gone. There is no cover on that stretch. I am LOOKING at the absence of cover.'] },
  { say: ['lake:worried', 'He bowed. That was a real bow — a taught one. Grandmother had one like it and I never learned what it was for.'] },
  { say: ['lake', 'And he aimed it low. At my hands. At the—'] },
  { say: ['vesper', 'Don’t finish that sentence, I’m not ready to file it.'] },
  { say: ['vesper:thinking', '(Entry: one figure, far rim, hooded. Conduct: courteous. Departure: unexplained. Cat’s opinion: extensive, recorded in full.)'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['lake', 'First time in his life he’s made that sound. I’d have been happy never learning he could.'] },
  { mood: 'forestB' },
  { run: () => { F.strangerSeen = true; } },    // vista exit opens
  { camRelease: true },
]);
```

**The vista** (`playVista`): triggers with `strangerSeen`, either player y > 640, once. The
vista is the scene's lower edge; this is a cam move, not a scene change.

```js
Cutscene.play([
  { cam: { x: 672, y: 700, viewH: 768 } },     // push to the parapet; the painting's lower band is the reveal
  { wait: 1.0 },
  { narrate: 'The last switchback turned them around a shoulder of rock, and the gorge opened below like a lit window.' },
  { narrate: 'A town. Stacked down both cliffs, stitched across the river with rope and lamplight — five great timber locks stepping the water down into the haze, waterwheels turning, boats rafted thick as cobbles — and NOISE. Hammers. Gulls. Somebody laughing. Somebody selling something.' },
  { say: ['vesper', 'Not on the sheet. A whole town, Lake. Not on the sheet.'] },
  { say: ['lake', 'Listen to it.'] },
  { say: ['vesper', 'I am listening to it. …I’d forgotten what a Tuesday sounds like.'] },
  { say: ['lake', '(Two days. Two days since the square went quiet, and my ears have been ringing with it the whole way. And down there it’s just… going on. All of it. Going on.)'] },
  { camRelease: true },
]);
```

### BEAT 2 — Arrival: the town alive (`playArrival` + market talk)

Trigger: first entry to `dellhollow` (state `day`), `!arrived`. Music: `festival` placeholder
— **this is the 'dellhollow' town theme slot** (§f).

```js
Cutscene.play([
  { mood: 'festival' },                    // placeholder → forthcoming 'dellhollow' theme
  { cam: { x: 560, y: 420, viewH: 640 } },
  { narrate: 'Dellhollow, of the five locks. It smelled of tar, bread, wet rope and roasting chestnuts, and it sounded like everything Emberbrook had stopped being.' },
  { narrate: 'Nobody stared at them. A woman selling eels shouted a price at them on principle. Two children ran through the middle of the party without apology or slowing. It was wonderful.' },
  { say: ['vesper:happy', 'Market row. A guildhall. A working crane and a queue for bread. Lake — people. Uninterrupted people, doing ordinary things, at VOLUME.'] },
  { say: ['lake', '(No pedestal. No keeping-flame. I’ve walked the whole quay with my eyes twice — just oil lamps on strings, lit by whoever’s nearest, meaning nothing.)'] },
  { say: ['lake', '(And it holds. It’s loud, and it’s kind, and it holds together with no flame at all. …Grandmother, what else didn’t you tell me? Or didn’t know?)'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi has located the eel-stall. The party’s marching order has quietly changed.)'] },
  { say: ['vesper', 'Quay first. Towns are like rivers — you read them from the people at the edges. Then whoever’s in charge.'] },
  { run: () => { F.arrived = true; } },
  { camRelease: true },
]);
```

**Market voices** — `talkTo` branches, day (objective counts hobb + pell, Ch.1 Act-I style):

HOBB (pumpkin barge, first talk — sets `talked.hobb`):
```
hobb    'Don’t buy anything, don’t lean on anything, and if you’ve come to gawp at the eel
         you can gawp at forty ton of pumpkins instead. Going SOFT, the lot of them. In
         elegant rows.'
vesper  'How long have you been in the queue?'
hobb    'Nineteen days. “Cut them for pie,” my wife says. Nineteen days of my wife saying
         pie. It was a bulk contract, madam. Harvest-fair, downriver. There is no fair for a
         November pumpkin.'
lake    'I’m sorry for your cargo.'
hobb    'Don’t be sorry, be useful— no. No, forgive me. Nobody’s useful against the river.
         First thing you learn up here, last thing you believe.'
```
HOBB (repeat): `'You want north, I hear. So do forty ton of pumpkins. Get in the queue — it’s a very patient queue. We’ve named the seagulls.'`

PELL (lamp-pole, first talk — sets `talked.pell`; carries the **pale-blue-light line**):
```
pell    'Watchman. Night shift. It is presently day, which is why I’m holding a wick-knife
         and a grudge.'
lake    'You keep the lantern-strings?'
pell    'Every wick, every noon, so they’ll burn every night. No ceremony to it, friend —
         oil goes in, light comes out, and I’d thank the town to remember who carries the
         ladder.'
pell    'Odd stretch of nights, mind. Three nights back I’m on the rim walk, and there’s a
         light going north along the old high road. Steady. Didn’t bob, the way a carried
         lantern bobs. And pale — pale BLUE, like the heart of a hail-cloud.'
vesper  'Did you hail it?'
pell    'Put my own lamp up, which is the whole language I’ve got. It stopped. A long stop.
         Then it went on north, and I found I’d sat down on the wall without deciding to.'
pell    'Marsh-gas, the harbormistress says. Aye. Well. Marsh-gas doesn’t stop to look back
         at you.'
vesper:thinking  '(Filed. Next to the bow.)'
```
PELL (repeat): `'Sleep’s for the day shift. Which is now. Which is the grudge.'`

MOCHI (talkTo, in town): `system: '(Mochi is sitting at the eel-stall with the composure of a paying customer. The eel-wife has already fed him twice. Neither of them has admitted it.)'`

### BEAT 3 — The jam explained: Odessa's ruling (`playJam`)

Trigger: `talked.hobb && talked.pell`, either player approaches Odessa at the lockhead
(interact, or proximity < 110). Odessa at (1010, 400); Hobb and Pell drift in (run steps).
Carries the Emberbrook news + the **distant-catastrophe reaction** (consolidated here from
the arrival flow — the market beats stay light, the news lands where the authority is).

```js
Cutscene.play([
  { cam: { x: 960, y: 380, viewH: 540 } },
  { say: ['odessa:grave', 'Harbormistress. You’ll be the pair off the rim road — the quay’s told me twice already, with improvements. Say your business plain; I’ve a town of idle boats to keep from stupidity.'] },
  { say: ['vesper', 'Vesper — mapmaker. Lake — lamplighter. We need to go north, faster than walking. Everyone we’ve met says the river is the road.'] },
  { say: ['odessa', 'The river IS the road. The road is shut.'] },
  { say: ['odessa:grave', 'Lamplighter, you said. Off the rim road. …Emberbrook, then. The flame-village on the high valley. You’re a long way below your lamps, boy.'] },
  { say: ['lake', 'Yes. And I’ll say it to you straight, because you’ll hear it crooked off a fish-cart eventually: two nights ago our flame was taken. All of it, in a breath. The village stands — fed, housed, safe. And every soul in it has gone flat. They know their own lives like a ledger and can’t feel one line of them. We’re going north to bring the flame home.'] },
  { wait: 1.2 },
  { say: ['odessa:grave', '…I’ve heard of your lamps the way you’ve maybe heard of our floods. Neighbors’ weather.'] },
  { say: ['hobb', 'Took the— the LIGHTS? All the lights at once? Who’s minding the ovens? A village can’t just— somebody has to mind the ovens.'] },
  { say: ['odessa', 'Hobb.'] },
  { say: ['hobb', 'I’m only saying. Terrible thing. Terrible. My cousins downriver won’t believe half of it.'] },
  { say: ['vesper:thinking', '(They’re sorry the way you’re sorry for an earthquake across the sea. It’s real sorrow. It just has nowhere in them to land — and why would it? You can’t miss a warmth you never sat in.)'] },
  { say: ['odessa:grave', 'Then you have my sympathy, and my sympathy moves no water. Come to the beam. I’ll show you what shut my road.'] },
  { run: () => { /* group to the lockhead rail; cam angles down the gorge */ } },
  { cam: { x: 1050, y: 520, viewH: 620 } },
  { say: ['odessa', 'Five locks step this water down to the low country. Nineteen days ago, something moved into Lock Five and shut it better than gates ever did. An eel — river-eel, the old kind. Long as a grain-barge, patient as winter, and lying on the only water out of this gorge.'] },
  { say: ['vesper', 'And you can’t… move her along? Drive her down?'] },
  { say: ['odessa:grave', 'Mind how you talk about her in my town.'] },
  { say: ['odessa', 'This town is not frightened of an eel — carry that upriver and down, with my compliments. This town is POLITE to this river. Politeness is why Dellhollow is four hundred years old, and why the rapids are full of towns that weren’t.'] },
  { say: ['hobb', 'What she said. It isn’t fear. It’s manners.'] },
  { say: ['pell', 'And nobody who’s seen her close is in a hurry to be impolite. Which is a different thing from the other word. Which nobody has said.'] },
  { say: ['odessa:grave', 'My ruling stands as posted. No boat works Lock Five while she’s below. She came up for her own reasons; she’ll go down for her own reasons. The river asks a season — the town waits a season. Towns that argue with rivers lose.'] },
  { say: ['vesper', 'We can’t spend a season. Truly. Every day we’re slow, home gets flatter.'] },
  { say: ['odessa', 'Then walk the high road, or wait with the pumpkins. Those are the choices I’ve got to sell.'] },
  { say: ['vesper', 'The high road crossed a ravine this morning without us — there’s a gap in it you could post letters down. How far north does it actually get?'] },
  { say: ['odessa:grave', 'To the Falls Span. Which went, sixty years before I was born — a yard of it left on each rim, like a sentence somebody stopped saying. Everything north of here goes by water. That is what Dellhollow is FOR, and just now Dellhollow isn’t going either.'] },
  { say: ['vesper:thinking', '(And there’s my heath explained. The sheet was drawn while the span still stood — the road ran on, so the pen ran on. The map remembers a bridge the world forgot.)'] },
  { say: ['odessa:grave', 'I’m sorry for your village, lamplighter. I am. But I won’t drown polite strangers to save it faster, and I won’t—'] },
  { say: ['pell', 'OI! HARBORMISTRESS!'] },
  { run: () => { F.jamDone = true; this.playMarenWet(window.players); } },
]);
```

### BEAT 4 — Maren, entering wet (`playMarenWet`)

Chained from Beat 3. Pell marches Maren up from the deep stairs by the collar, dripping.
Stages at the tally beam (880, 340). The mother-daughter scene tells the father story with no
flashback — the beam, the boat, and two women's sentences carry all of it.

```js
Cutscene.play([
  { run: () => { /* pell + maren from the stairhead; maren soaked, grinning; pell's fist on her collar */ } },
  { move: { ent: maren, x: 900, y: 380, speed: 160 } },
  { say: ['pell', 'Fished this out of Five. AGAIN. Swimming, if you please. In the dark. In November. Over THAT.'] },
  { say: ['maren:happy', 'Under. “Over” implies I stayed on top. Morning, Ma.'] },
  { say: ['odessa:grave', 'Maren.'] },
  { say: ['maren', 'Before you start — she watched me the whole way down and the whole way up and she did not care. Nine dives now, and she’s never so much as turned that eye—'] },
  { say: ['odessa', 'Ten.'] },
  { say: ['maren', '…Ten. The point stands!'] },
  { say: ['odessa:grave', 'The point does not stand. The point sinks, like everything else you put in that lock. Home. Dry clothes. Now.'] },
  { say: ['maren:happy', 'Can’t. Company. …Hello! You’re the flame people — whole quay says. Is the cat part of it? The cat looks official.'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['maren:determined', 'Then before my mother says what she’s going to say: take me on. I’m the best water-eye on this quay and every captain rafted out there knows it. I’ve crewed these locks since I was five. I can read this river the way your mapmaker reads a— a map. I know what’s in Five better than any soul living. And I’m seventeen, which is grown, ask anyone who isn’t my mother.'] },
  { say: ['odessa:grave', 'No.'] },
  { say: ['maren', 'You haven’t heard the—'] },
  { say: ['odessa', 'I’ve heard every word of it since you were six and rowing the wash-tub. The answer is the answer. No child of mine works the north river.'] },
  { wait: 0.8 },
  { say: ['maren:determined', 'Say why. Out loud. In front of strangers, say the why.'] },
  { wait: 1.2 },
  { say: ['odessa:grave', '…Mind the beam when you shout. You’ll smudge your father’s marks.'] },
  { cam: { x: 880, y: 330, viewH: 420 } },
  { say: ['system', '(On the old balance beam, low down: a fathom of chalk tallies gone grey under wax — a big hand’s work, ended mid-row. Above them, climbing higher every year, fresher marks in charcoal: a smaller hand’s. Nobody has ever cleaned this beam.)'] },
  { say: ['maren', 'That’s not an answer. It’s never been an answer.'] },
  { say: ['odessa', 'It’s the whole answer. He was the best eye this river ever grew — better than you, and you’re better than everyone else alive. And the north water took him anyway. Between one heartbeat and the next, on a fair morning, in June.'] },
  { say: ['odessa:grave', 'I hauled his boat back up the portage myself. I tar it every winter. I have never once let myself ask why. And I will not stand on my own quay and watch it go north again with you in it.'] },
  { wait: 1.0 },
  { say: ['maren', '…Ma.'] },
  { say: ['odessa', 'Dry clothes. Then — since you’re the standing authority on Lock Five — take our guests down and show them what’s shut my river. SHOW, Maren. The stairs. Not the water.'] },
  { run: () => { /* odessa exits to the guildhall; pell releases the collar with ceremony */ } },
  { wait: 0.8 },
  { say: ['maren:happy', '…She tars the boat. Every winter. She thinks I don’t know.'] },
  { say: ['vesper:thinking', '(New page. “Dellhollow. Population: alive, loud, and not saying the word afraid. The harbormistress’s daughter keeps her ledger in charcoal, on herself. The beam is a ledger too.”)'] },
  { run: () => { F.marenDone = true; } },       // deep stairs open
  { camRelease: true },
]);
```

### BEAT 5 — Down to Lock Five: the Tenant (`playLockFive`)

Trigger: first entry to `lockfive` with `marenDone` (Maren walks point — place her at the
stair foot). Includes the stairs chatter (**Maren's "so where are YOU from?"** — the
friendship engine's first tooth) and the nesting deduction. The quiet-banks line is soft and
**unremarked** — nobody responds to it; the script moves on.

```js
Cutscene.play([
  { mood: 'silence' },
  { cam: { x: 1100, y: 300, viewH: 560 } },
  { narrate: 'The stairs went down past the third lock, and the fourth, into the cool black under the town — two hundred steps of wet timber, with the river talking to itself inside the walls.' },
  { say: ['maren:happy', 'Mind the forty-first step, it lies. So — Lake of Emberbrook. Vesper of— what’s yours? Everyone’s of somewhere. I’m of HERE, four generations; you can’t get rid of us with a flood, they tried.'] },
  { say: ['lake', 'Emberbrook. Born a lane off the square. I know every window.'] },
  { say: ['maren', 'And you?'] },
  { wait: 0.8 },
  { say: ['vesper', '…Around. Professionally around.'] },
  { say: ['maren', 'That’s not a somewhere.'] },
  { say: ['vesper', 'No. It isn’t. Mind your forty-first step.'] },
  { say: ['maren:happy', '(loud whisper, to Lake) Is she always—'] },
  { say: ['lake', 'Yes.'] },
  { say: ['vesper', 'The marks on your arm. You’re a ledger too.'] },
  { say: ['maren', 'Locks worked. Da chalked his on the beam; I wasn’t allowed the beam yet, so — arm. Charcoal washes off, so I redraw them every morning.'] },
  { say: ['maren:determined', 'It’s not sad. It’s bookkeeping.'] },
  { wait: 0.6 },
  { cam: { x: 620, y: 480, viewH: 700 } },
  { narrate: 'Lock Five was a cathedral that worked for a living: black timber going up out of lantern-reach, chains hanging like bell-ropes — and a flooded chamber of still, dark water, with the dark in it coiled.' },
  { say: ['system', '(She is there. She was always going to be there, and it still lands like a hand closing on the back of the neck: a body thicker than a barrel, mottled moss-and-bronze, old scars like map-lines, laid around the chamber in two easy coils. One pale eye, clouded like a lamp behind fog, is open.)'] },
  { say: ['vesper:worried', '…You swam in this.'] },
  { say: ['maren:awed', 'Ten times. Look at her. LOOK at her. She was in this river when the locks were still trees.'] },
  { say: ['lake', '(The eye moved. Not at the lantern — at us. I have never been read so thoroughly by anything, and I grew up under my grandmother.)'] },
  { say: ['maren', 'The Tenant, the quay calls her. Under Dellhollow longer than any family in it. Never once paid rent.'] },
  { say: ['maren:determined', 'Now the part nobody up top will hear me out on. She’s not hunting and she’s not lost. Eels her size hold the deep banks, the low country — they do not climb five locks for fun. And watch. Every hour, near enough, she does THAT.'] },
  { run: () => { /* ripple FX: the great body eases toward the left wall, lies against the sealed grate, eases back */ } },
  { say: ['system', '(The coils unwind by a fathom. She crosses to the left wall — to a sealed grate, timber and iron, low over the water — and lies against it a long moment, whiskered chin to the bars. Then she comes back, and settles, and watches them again.)'] },
  { say: ['vesper', 'The grate. What’s behind the grate?'] },
  { say: ['maren', 'Sluice gallery. Old workings — draws the chamber down when they need her dry. Sealed since granddad crewed.'] },
  { say: ['vesper:thinking', 'She’s not resting against it. She’s TENDING it. Circuit, wall, back — that’s not an animal loafing. That’s a round.'] },
  { say: ['lake', '…Like a keeper.'] },
  { say: ['maren:awed', 'The weed. There’s weed packed through those bars — I saw it on dive six and called it flood-trash. She CARRIED it there. She’s nesting. Eggs in my sluice gallery — that’s why she won’t go down—'] },
  { say: ['vesper', 'She won’t go anywhere. Nothing that tends leaves the thing it tends.'] },
  { say: ['maren', '(quiet) Funny, though. The old pilots always said the deep banks were thick with her kind. It’s been dead quiet down there this year. Maybe that’s why she came all the way up.'] },
  { wait: 0.8 },
  { say: ['maren:determined', 'So it’s worse than the town thinks. Eel eggs, in cold water? She could be over that gallery till spring. Ma’s season just got five months longer, and nobody knows it but the four of us.'] },
  { say: ['vesper', 'Then nobody waits her out, and nobody in their right mind moves her off a nest. Which leaves— Maren. What is that?'] },
  { cam: { x: 1100, y: 380, viewH: 520 } },
  { say: ['system', '(High in the cliff wall, above the waterline: a round timber-ringed mouth, dry and dark, big enough to swallow a boat whole. Two winches crouch on the apron before it, under a hundred years of grease and rust.)'] },
  { say: ['maren', 'The flume. High-water spillway — the old boys cut it to shoot timber and spring floods past the bottom locks, straight down to the tailwater pool. Dry since before I was born. It’s a mile of black, it drops like a stair, and the head-gate winches seized when granddad was young.'] },
  { say: ['vesper', 'But it goes DOWN. Past the locks. Past her — without opening one gate over that nest.'] },
  { say: ['maren:awed', 'It goes down. …You’d need water in it — the head-gates draw off the top of this pool; she’d feel weather, nothing worse. You’d need a boat that can take a beating. And you’d need a pilot who holds the mile of black in her head.'] },
  { say: ['maren:determined', 'You’d need me.'] },
  { say: ['lake', 'Your mother—'] },
  { say: ['maren:determined', 'Said show you Five. I’m showing you Five.'] },
  { say: ['vesper:thinking', '(For the record: the plan is insane, the pilot is seventeen, and the chart of the flume exists in exactly one living head. …I’ve been that head. New page.)'] },
  { run: () => { F.lockSeen = true; F.planMade = true; } },
  { camRelease: true },
]);
```

Returning upstairs with `planMade` fades to dusk → night (`nightFallen = true`; town state
`night`, lantern-strings lit, Maren "gone to rig chains" — hidden). Short glue narrate on the
fade: `'They came up out of the dark into the dusk, which felt like sunrise. Maren went ahead of them up the stairs, two at a time, already rigging chains in her head. Night came down the gorge, and the lantern-strings came on, one by one.'`

### BEAT 5½ — The dock, at night (`playDockNight`) — Vesper's scene

Trigger: `nightFallen && !dockDone`, both players on `dellhollow`, auto after a 2s free-roam
breath (letter-beat pattern). Stage: the dock edge bench (540, 640), lantern-strings lit,
town murmuring. This is the chapter's quiet center. **Register guard: every line here is
ordinary — family fog, immigrant haze, a filing problem. No flame-terms, no Hush-terms, no
wondering "why" beyond the human.**

```js
Cutscene.play([
  { mood: 'forest' },        // placeholder (forestA, gentle) → night-quay variant of the 'dellhollow' theme
  { cam: { x: 560, y: 590, viewH: 460 } },
  { run: () => { /* stage: vesper + lake seated at the dock edge; mochi between them */ } },
  { narrate: 'Night, on the quay. The lantern-strings burned in long swags over the water — ordinary oil, ordinary light — and under them the town went warmly about its evening as if that were nothing at all.' },
  { say: ['lake', 'Pell lit half of these and complained the whole time. A fish-wife did three while I watched — one-handed, still arguing about brill. Anyone. They just… light them.'] },
  { say: ['vesper', 'And it’s enough. That’s the thing rattling around in you tonight, isn’t it. It’s enough.'] },
  { say: ['lake', '…I’ll manage. It’s a good rattle. Ask me your real question.'] },
  { say: ['vesper', 'I don’t have a—'] },
  { say: ['lake', 'Maren asked where you’re from. You answer everything, Vesper. Usually with footnotes. You didn’t answer her.'] },
  { wait: 1.2 },
  { say: ['vesper', '…I don’t know where I’m from. That’s the whole answer. It isn’t tragic, so don’t make the face.'] },
  { say: ['lake', 'This is my listening face.'] },
  { say: ['vesper', 'We moved when I was six. The way families do — work, weather, roads. No story to it. My parents are warm people, Lake. Genuinely. Ask about last summer, you get stories — three hours of stories, my father does the voices.'] },
  { say: ['vesper', 'Ask about anything before I was born, you get weather.'] },
  { say: ['vesper', '“Where did you two meet?” — “Oh, it was a wet spring.” A wet SPRING. Twenty years of asking, and I hold a complete meteorological record of my own family and not one placename.'] },
  { say: ['lake', 'Every family has a fog somewhere. Half of Emberbrook can’t name a great-grandmother.'] },
  { say: ['vesper', 'That’s what I decided too. People move. The past gets left behind for practical reasons. Nobody owes their childhood an atlas.'] },
  { say: ['vesper', 'I remember three things from before. A well with a cracked cap. A fence with a gate that dragged. And a hill — round, bald on top, off east from a kitchen window.'] },
  { say: ['vesper', 'I remember the hill perfectly, Lake. I could draw you the hill — I HAVE drawn the hill; it’s numbered. And I feel nothing about it. People feel things about home. I’ve watched you do it all week — it costs you something every time you say “Emberbrook.” My hill is a landform.'] },
  { say: ['lake', '(She says it the way she’d report a survey error. Which, I am beginning to understand, is exactly what she thinks it is.)'] },
  { say: ['lake', '…And the routes.'] },
  { say: ['vesper', 'And the routes. Eleven years of them. Nobody commissions the routes I walk — surveyors follow the trade; I go along everything, in order. You know what you call walking every road out of every market town on a sheet, in sequence?'] },
  { say: ['lake', 'A grid.'] },
  { say: ['vesper', 'A grid. Thank you. A search would be emotional. A grid is just thorough. Somewhere there is a well, a fence, and a round bald hill that line up out a kitchen window — and the day I walk over the right rise, I’ll know it. And then I’ll finally have an answer for everyone’s favorite small question.'] },
  { say: ['vesper', 'It’s a filing problem. I file. Don’t make it a wound, or I’ll invoice you for the honeybun I know you’ve been saving.'] },
  { say: ['system', '(Lake hands over the honeybun. He had been saving it. He does not make it a wound.)'] },
  { say: ['lake', 'For the record — the day you walk over the right rise. I’d like to be there.'] },
  { say: ['vesper', '…Noted. For the record.'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi has been asleep against the woman with no somewhere for the better part of an hour. Cats file things too.)'] },
  { wait: 1.0 },
  { run: () => { const m = this.npcs.maren; m.hidden = false; m.scene = 'dellhollow'; m.x = 1150; m.y = 620; } },
  { move: { ent: maren, x: 700, y: 630, speed: 170 } },
  { say: ['maren:determined', '(low) Oi. Flame people. Tide’s slack, town’s asleep, boat’s on the chains. …Well? It’s a very good hour for being impolite quietly.'] },
  { say: ['vesper', '(One day in, and the girl who can’t leave home is smuggling us out of it. I like her enormously. This is also going to be a problem.)'] },
  { run: () => { F.dockDone = true; } },
  { camRelease: true },
]);
```

### BEAT 6 — The twin winches, and Odessa's station (`playWinches`)

Trigger: `dockDone`, both players enter `lockfive` (state `night`), auto. The co-op
setpiece: **bothHold ×2** — left winch, then the seized right winch, which opens only when
Odessa arrives mid-attempt and takes a station. Boat lowered from the chains first.

```js
Cutscene.play([
  { mood: 'silence' },
  { cam: { x: 620, y: 420, viewH: 680 } },
  { narrate: 'Lock Five at midnight was blacker than the flume it kept. The work-lanterns made two small rooms of light in a dark the size of a church. The Tenant’s eye was open. The Tenant’s eye, they were coming to understand, was always open.' },
  { say: ['maren', 'Chains first. She’s watched me rig them all week and offered no opinion — which, from her, is a permit.'] },
  { run: () => { /* the shrouded boat comes down out of the dark on its chains, to the water's edge by the apron */ } },
  { say: ['system', '(Down out of the dark comes a boat: clinker-built, tar-dark, rope fenders, a lantern hook at the prow. Small, old, and kept the way tools are loved by people who won’t say so out loud. The tar is fresh.)'] },
  { say: ['lake', '(He knows whose it is before anyone says. Somebody does this boat’s rounds.)'] },
  { say: ['maren', 'Da’s. Ma thinks it hangs down here because she hauled it here. It hangs here because I climb down and sit in it, some nights. …Don’t tell her that. She has enough weather.'] },
  { say: ['mochi', 'Mrrp?'] },
  { say: ['system', '(Mochi looks at the boat. Mochi looks at the water beneath the boat, and at the shape in the water beneath the boat. Mochi sits down to reconsider the terms of his employment.)'] },
  { say: ['maren:determined', 'Head-gates. Twin winches, twin bars. Order of operations: LEFT winch first, to half — or the flume takes her water sideways and we all learn a great deal very fast. Both of you on the bar. And don’t stop on the squeal. The squeal is it working.'] },
  { run: () => { /* stage: vesper + lake at winch L (990, 520); maren spotting the gate */ } },
  { bothHold: { prompt: 'HOLD  A — the left winch, together', dur: 2.2 } },
  { shake: 3 },
  { run: () => { AudioSys.rumble(); Net.send({ type: 'buzz', ms: 250 }); F.gateHalf = true; } },
  { say: ['system', '(A hundred years of rust lets go a degree at a time. Somewhere inside the cliff, water finds a passage it had forgotten — and the flume mouth begins, hollowly, to breathe.)'] },
  { say: ['maren:happy', 'HA! Half-gate! Hear her? That’s the flume clearing its throat. Right winch now — and the right one’s the widow. Seized since granddad. She’ll fight.'] },
  { run: () => { /* stage: both players at winch R (1200, 560); they heave — nothing */ } },
  { wait: 1.0 },
  { say: ['system', '(The right-hand bar does not move. It has spent a lifetime becoming part of the cliff, and it declines — politely, completely — to stop being cliff.)'] },
  { say: ['lake', 'It’s not rust on this one. The drum’s crowned over. We’re two pairs of hands short of—'] },
  { run: () => { /* lantern-light on the stairs, descending, unhurried */ } },
  { say: ['system', '(There is a lantern coming down the stairs. It does not hurry. It has never needed to hurry. Everyone born in this town knows the harbormistress’s step.)'] },
  { wait: 1.2 },
  { say: ['maren', '…Ma.'] },
  { say: ['odessa:grave', 'Forty years I’ve kept this gorge. Did the pack of you imagine a gate-chain moves ANYWHERE in it at midnight without my pillow hearing it?'] },
  { wait: 1.0 },
  { say: ['odessa:grave', '…That bar is cut for six hands. Move over.'] },
  { say: ['system', '(She pulls the heavy gloves from her belt — worn to the shape of exactly this work — and sets herself at the bar like a woman coming home to an argument.)'] },
  { say: ['maren:awed', 'Ma—'] },
  { say: ['odessa', 'Turn.'] },
  { bothHold: { prompt: 'HOLD  A — the widow-winch, all together', dur: 2.6 } },
  { flash: 0.6 }, { shake: 5 },
  { run: () => {
      F.gatesOpen = true;
      AudioSys.rumble(); AudioSys.chime(); Net.send({ type: 'buzz', ms: 500 });
      Particles.burst(24, () => ({ kind: 'sparkle', x: 1120 + (Math.random() - 0.5) * 140, y: 300 + (Math.random() - 0.5) * 80, vy: -8, life: 1.2 }));
    } },
  { narrate: 'The widow-winch came off her century all at once — and the river stood up and walked into the mountain. White water took the dry mile in one long swallowed roar, and the whole chamber rang like the inside of a drum.' },
  { say: ['maren:happy', 'FULL GATE! She’s running! Oh, she sounds like Da always said — like weather underground—'] },
  { say: ['odessa:grave', 'The head-gates draw off the top of the pool. Nothing below the waterline will feel more than weather — her gallery holds its level. I cut my teeth on those sums, girl; don’t look so surprised.'] },
  { wait: 1.0 },
  { say: ['odessa:grave', 'Maren.'] },
  { say: ['maren:determined', 'Say it, then. Say no.'] },
  { wait: 1.6 },
  { say: ['odessa:grave', '…Who else knows the mile of black.'] },
  { say: ['system', '(It is not permission. It is arithmetic, done out loud by the only person in Dellhollow honest enough to do it. Maren does not whoop. Somehow, she does not whoop.)'] },
  { say: ['odessa', 'Stern for you. Weight low past the eye — all of you, low, and hands inboard. I’ll take the portage stair; I’ll be at the tailwater before the sun is.'] },
  { say: ['odessa:grave', '…Don’t make me stand there long.'] },
  { say: ['system', '(Boarding order: Maren to the stern like gravity is optional. Lake amidships, the lighter warm inside his coat. Vesper to the bow, notebook triple-wrapped in oilcloth. Mochi—)'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi is not aboard. Mochi is delivering, from the apron, a position paper on boats. Lake holds open the satchel. A long negotiation occurs, at the speed of cat. Mochi boards the satchel facing backward, as if the whole arrangement were his own idea and everyone else were late.)'] },
  { run: () => { F.boatDown = true; this.playFlumeRun(window.players); } },
]);
```

### BEAT 7 — The flume run (`playFlumeRun`)

Chained from Beat 6. Pure scripted spectacle: cam work over the `lockfive` painting and
spray/shake FX, then dark-frames — **no new systems**. Two movements: the held-breath glide
past the Tenant (slow, silent), then the run (loud, fast, Maren calling timings).

```js
Cutscene.play([
  { mood: 'silence' },
  { cam: { x: 560, y: 520, viewH: 520 } },
  { narrate: 'Maren pushed off with one long stroke of the sculling oar, and the pool took them: black water, dead quiet under the roar of the filling flume, the lantern-strings of Dellhollow a hundred feet up like somebody else’s stars.' },
  { wait: 1.0 },
  { narrate: 'And then the water to starboard was not water.' },
  { run: () => { /* the Tenant rises alongside: overlay/sprite slide if available, else ripple FX; buzz 150 */ } },
  { say: ['system', '(She has risen. Not at them — beside them: a wall of moss-and-bronze sliding past at arm’s reach, old scars like map-lines, and the one pale eye, huge and calm, level with the gunwale. Watching.)'] },
  { say: ['maren', '(whisper) Oars in. Weight low. Nobody row — we’re guests.'] },
  { say: ['lake', '(The lighter is warm through my coat, and the eye finds it — the one small kept fire in all this dark — and rests there. The way old women look at other people’s grandchildren.)'] },
  { say: ['vesper:thinking', '(The eye goes over each of us in turn, unhurried, like a harbormistress reading papers. …Approved. Apparently. Filed under: the river has opinions, and today we had one.)'] },
  { narrate: 'For the length of three boats, the oldest thing in the river looked at them, and they let themselves be looked at. Then — unhurried, immense, deciding — she sank away under the black, back toward her sealed door and everything she was keeping behind it.' },
  { say: ['maren', '(whisper) …Told you. Manners.'] },
  { wait: 1.0 },
  { narrate: 'Then the flume took them.' },
  { shake: 5 },
  { run: () => { Net.send({ type: 'buzz', ms: 400 }); Particles.burst(30, () => ({ kind: 'sparkle', x: 1100 + (Math.random() - 0.5) * 200, y: 350 + (Math.random() - 0.5) * 120, vy: 20, life: 0.6 })); } },
  { say: ['maren:determined', 'BOW LEFT! Left, left— GOOD. First drop in three— two— HANG ON—'] },
  { shake: 6 }, { flash: 0.3 },
  { say: ['system', '(The bottom falls out of the world. The prow lantern draws one gold line down a mile of roaring black.)'] },
  { say: ['maren:happy', 'Second drop’s a dog-leg — fend RIGHT— Da always called it three lengths, it’s TWO now, the wall’s slumped — FEND—'] },
  { shake: 5 },
  { say: ['system', '(A wave the temperature of January comes over the bow. Vesper shields the notebook with her entire body. Priorities.)'] },
  { say: ['lake', '(Light: held. Cat: yowling. Pilot: laughing. Grandmother, the round has gotten strange — and I am sorry to report I’m having the time of my life.)'] },
  { shake: 6 },
  { say: ['maren:happy', 'LAST GATE! It’s open— it was never even shut proper— she OILED it. Ma, you absolute— SHE OILED THE TAIL-GATE—'] },
  { flash: 0.5 },
  { narrate: 'And then: sky. Stars, actual stars, wheeling to a stop overhead. The flume spat them long and flat across the tailwater pool below the last lock, and the roar fell away behind them like a door closing kindly.' },
  { wait: 1.2 },
  { mood: 'resolve' },
  { say: ['system', '(Silence. Steam off the water. Far above, very faint, the lantern-strings of Dellhollow. Mochi emerges from the satchel and begins, immediately and furiously, to wash.)'] },
  { say: ['maren:awed', '…Under four minutes. Da’s best was six.'] },
  { say: ['maren', '(quiet) Beat your time, Da. You’d have hated that. …You’d have loved that.'] },
  { fadeTo: 1 }, { wait: 1.2 },
  { run: () => { F.flumeDone = true; this.playLanding(window.players); } },
]);
```

### BEAT 8 — The landing: the bag, the chart, the boat (`playLanding`)

Chained from Beat 7. Scene: `landing` (dawn). Odessa is at the stair foot — lantern, coiled
rope over one shoulder, and a packed bag. **`odessa:warm` fires exactly once, at the chart
line.** The chapter's required beats: the bag, the chart handoff to Vesper, Maren joins
(toast + banner), the party gains the boat, end card north on the river.

```js
Cutscene.play([
  { run: () => { /* place: boat moored (450, 540); party ashore; odessa at the stair foot (1000, 460), bag at her feet */ } },
  { fadeTo: 0 },
  { cam: { x: 700, y: 480, viewH: 620 } },
  { narrate: 'They warped the boat in to the old stone landing under the cliffs, and bailed, and wrung, and were loudly alive at one another, until the sky went the color of pearl.' },
  { narrate: 'Odessa was on the landing before the sun was. Of course she was. She had her lantern, a rope’s-end coiled over one shoulder — and a bag.' },
  { say: ['maren', '…Ma. That’s my bag.'] },
  { say: ['odessa:grave', 'Packed a week ago. You were going north the moment that eel gave you an excuse — I’ve watched it coming the way I watch weather come. A harbormistress who can’t read her own harbor should hand in the whistle.'] },
  { say: ['maren', 'A WEEK? You packed it a week ago and you still said no! Nine times you said no!'] },
  { say: ['odessa', 'Ten. And I’d say all ten again. The no was what I owed my own heart. The bag is what I owed yours.'] },
  { wait: 1.2 },
  { say: ['odessa', 'The boat’s yours — it was always going to be yours. I only kept the tar on while it waited for you to be ready. Fenders are new-roped. Bread in the bow locker, and salt-fish enough to make you sick of salt-fish, which is a harbor blessing. Take it.'] },
  { toast: { text: '✦ The party gains the boat — tar-dark, clinker-built, river-worthy', color: '#3fa7c9' } },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi walks the gunwale from stem to stern, inspecting. The boat appears to have passed. Nobody points out to Mochi what he was doing in a satchel an hour ago.)'] },
  { wait: 0.8 },
  { say: ['odessa:grave', 'Mapmaker. A word.'] },
  { run: () => { /* aside: odessa + vesper apart, near the stair; cam tightens */ } },
  { cam: { x: 960, y: 440, viewH: 420 } },
  { say: ['system', '(From inside her coat she takes an oilskin tube, worn glossy at the cap from years of handling. She does not hand it over so much as set it in Vesper’s hands and keep her own on it a moment longer.)'] },
  { say: ['odessa', 'His chart. The north river — every reach and shoal of it, tailwater to the grey marshes. He drew it from memory, the night before. It’s wrong.'] },
  { say: ['odessa:warm', 'She’ll want to fix it. Don’t let her do that alone.'] },
  { wait: 1.0 },
  { say: ['vesper', '…I’ve been correcting a wrong map by myself for eleven years, harbormistress. I don’t recommend it to anyone.'] },
  { say: ['vesper:determined', 'She won’t be alone.'] },
  { say: ['odessa:grave', 'Then that’s the whole of my asking.'] },
  { camRelease: true },
  { cam: { x: 650, y: 500, viewH: 560 } },
  { say: ['maren:determined', 'Ma — I’ll send word. Every town with a fish-queue between here and wherever, I’ll send—'] },
  { say: ['odessa', 'You’ll send charts. Word is air. A chart is a daughter’s hand on paper. I’ll have the charts.'] },
  { say: ['system', '(There is an embrace. It is brief, and it is total, and the harbormistress of Dellhollow does not care who is watching — which is how everyone watching knows exactly what it costs.)'] },
  { say: ['maren:happy', '(aboard, scrubbing her face with her sleeve, absolutely not crying) Right! Stations! Flame people amidships. Cat on the— cat wherever the cat decides. I’m not fighting the cat.'] },
  { toast: { text: '✦  Maren joined the party  ✦', color: '#3fa7c9' } },
  { say: ['lake', '(North, then. By water. The lighter warm against my chest, the old road keeping pace somewhere up on the rim. Grandmother — the round’s gotten strange. But I swear it’s still the round.)'] },
  { say: ['vesper:thinking', '(New page. “Party of three, one boat, one cat. One wrong chart to put right — and a hole in my own sheet: filed, patient, waiting for its rise.” …North.)'] },
  { banner: { title: '✦ North on the river ✦', sub: 'the flume behind them, the grey marshes ahead', dur: 6 } },
  { run: () => { F.marenJoined = true; /* maren.follow = 'party' from Ch3 onward; here the boat carries the blocking */ } },
  { narrate: 'The current took the little boat the moment it felt her — north, quick and cold, down the long water her father had drawn wrong, and her mother had let her go and fix.' },
  { narrate: 'On the landing, the harbormistress of Dellhollow stood with her lantern until the boat was a speck, and then stood a while longer. Then she took up her rope and began the long climb home — where a town, a river, and one enormous tenant were waiting, politely, for spring.' },
  { mood: 'silence' },
  { run: () => { F.ended = true; AudioSys.finale(); Net.send({ type: 'end' }); } },
]);
```

End card (`drawEnd` in `main.js` — needs a Chapter Two variant): **'End of Chapter Two —
Dellhollow'** / *'the river is the road'*.

**Interacts (full inventory, for completeness):**

`descent`:
- Empty bracket: 'An iron bracket bolted to the rock, empty, at lamp height. Whoever took the
  lamp unbolted it cleanly and took the bolts too. Thrift, or reverence. On this road,
  possibly both.'
- Chart halt (after `chartDone`): 'The north sheet, corrected in the field: one gorge, one
  river, one town, inked over forty years of confident heath. The annotation reads
  "SURVEYED, this time. —V."'
- Vista parapet: 'The parapet is polished at the top, the way stone gets where four hundred
  years of people have leaned to look at home coming up at them.'

`dellhollow`:
- Rafted queue: 'Boats lashed hull to hull, three and four deep, gangplanked into a floating
  lane. Somebody has strung washing between two masts. Somebody else has planted herbs in a
  bailing bucket. The queue has become a neighborhood.'
- Pumpkin barge: 'Forty tons of pumpkins in elegant rows. The nearest rank has begun, very
  quietly, to slump. Captain Hobb has arranged the worst of them facing away from the quay,
  like a man combing his hair over the thin patch.'
- Eel-stall: 'Smoked eel by the yard. The eel-wife's sign reads "FRESH — ASK HER YOURSELF."
  The quay finds this funnier than visitors do.'
- Notice board: 'RULINGS OF THE HARBOR. One: the river is right. Two: in disputes, see Ruling
  One. Three: no boat works Lock Five while the Tenant is below. — O.'
- Tally beam: 'The old balance beam. Low down, under wax: a fathom of grey chalk tallies, a
  big hand's, ended mid-row one June. Above them, climbing year by year, charcoal: a smaller
  hand's, renewed every morning. Nobody has ever cleaned this beam. Nobody ever will.'
- Waterwheels: 'The bypass races still turn the wheels — the town grinds, saws, and hoists on
  water that never asks the locks' permission. The river is only shut to things that float.'
- Lamp-pole: 'A lamp-pole, a ladder, and a wick-knife on a string. In a flame village this
  corner would be a shrine. Here it is a chore, and the town sleeps just as sound.'
- Dock edge (night, after `dockDone`): 'The bench holds the warmth a while after you stand
  up. That is all it does, and tonight it was enough.'

`lockfive`:
- The pool: 'Still black water. She is watching. She was watching before you looked, and she
  will be watching after you stop — the pale eye neither blinks nor wanders. Being seen is
  the toll here, and it costs more than it should.'
- Sluice grate (after `lockSeen`): 'The sealed gallery, dark weed packed through its bars,
  carried there strand by strand. The next generation of the river, behind a locked door,
  with the oldest thing in the water lying guard. …Move along quietly.'
- Flume mouth: 'A mile of black, dropping like a stair through the inside of a cliff. The
  timber ring is scarred where three centuries of log-drives went through. Boats were never
  the flume's business. There is a first time for everything, ideally with a pilot.'
- Winches (before Beat 6): 'A century of grease gone to amber. The left drum might turn, with
  conviction. The right one has become geology.'
- The boat (hung / after `boatDown`): 'Clinker-built, tar-dark, rope fenders, a lantern hook
  at the prow. The tar is this winter's. Somebody does this boat's rounds, and has for
  eleven years, and has never once said so.'

---

## (d) Objectives, prompts, markers — per beat

| Beat | `objective()` string | Prompts | Markers / gating |
|---|---|---|---|
| 1 | `Down the switchbacks — the road knows the way` → after chart beat: `Down — Dellhollow is not on the map` | `A — look` (bracket, chart halt, parapet) | Vista exit **denied** until `strangerSeen` (the ravine beat triggers on the second terrace, before the exit). South exit always denied. |
| 2 | `Dellhollow — meet the quay (n/2)` (hobb, pell) | `A — talk to Captain Hobb / Watchman Pell`, `A — look` | Deep-stairs exit denied (`odessa` deniedLine). |
| 3 | `The lockhead — ask the harbormistress about passage north` | `A — talk to Odessa` | `storyMarker` over Odessa once `talked` count = 2. Chains into Beat 4. |
| 4 | *(cutscene)* → `Down to Lock Five — the stairs, not the water` | — | `marenDone` opens the deep stairs. `storyMarker` over the stairhead. |
| 5 | `Lock Five — what Maren wants you to see` → after: `Evening — back up to the quay` | `A — look` (pool, grate, flume, winches) | Return upstairs with `planMade` fades to night (`nightFallen`), lantern-strings lit. |
| 5½ | `Night on the quay` → after dock scene: `Meet Maren at the deep stairs — quietly` | `Next ▸` | Dock scene auto-plays after a 2s breath (letter-beat pattern). `storyMarker` over the stairhead after `dockDone`. Descent exit denied at night (`maren` deniedLine). |
| 6 | `The flume — twin winches, together` | `HOLD A` ×2 | `swarm`-style lock: exits disabled during the setpiece (players are staged; the beat auto-plays on entry). |
| 7–8 | *(cutscenes)* → `''` after end | `Next ▸` | — |

---

## (e) Checkpoint plan — scrollable dev checkpoint menu

The engine is building a scrollable checkpoint MENU (no digit-key budget). Chapter Two
registers **five** entries. Follow the Chapter One `applyCheckpoint` pattern: clear
Dialog/Cutscene/Camera/FX, conjure missing keyboard players, base-reset flags, layer the
checkpoint's flags, `Field.enter`, snap cam, toast `⚑ checkpoint — <name>`.

| # | Name | State set |
|---|---|---|
| 1 | `Ch2: the descent` | Fresh flags; both players at the descent top; `playDescent` fires. Mood `forestB`. |
| 2 | `Ch2: Dellhollow — the quay` | `descentIntro, chartDone, strangerSeen`; players at the town's north entry; `playArrival` fires. Day. Mood `festival` (→ dellhollow theme). |
| 3 | `Ch2: Lock Five — the Tenant` | + `arrived`, `talked: {hobb,pell}`, `jamDone, marenDone`; players + Maren at the `lockfive` stair foot; `playLockFive` fires. Mood `silence`. |
| 4 | `Ch2: night — the flume winches` | + `lockSeen, planMade, nightFallen, dockDone`; town state `night` (lantern-strings lit), players + Maren in `lockfive` (state `night`); `playWinches` fires. Mood `silence`. |
| 5 | `Ch2: the landing — Maren joins` | + `boatDown, gateHalf, gatesOpen, flumeDone`; scene `landing`; `playLanding` fires. Mood `resolve`. |

---

## (f) Music & mood plan

Existing moods only as placeholders: `forestA`, `forestB`, `festivalA/B`, `hush`, `resolve`,
`silence` (stings: `hushSting`, `rumble`, `chime`, `pact`, `finale`).

| Where | Mood | Note |
|---|---|---|
| `descent` (Beat 1) | `forestB` | The uneasy wood, continued from the gate. |
| Stranger at the ravine | `silence` → `forestB` | Same shape as every Warden appearance: the quiet IS the sting. One `buzz` on the vanish. |
| Vista reveal | *(hold silence 2 narrates, then…)* | Let the town's noise be the music cue in prose; `festival` enters with the scene change. |
| `dellhollow` day (Beats 2–4) | `festival` (placeholder) | **← the forthcoming 'dellhollow' town theme goes here** — river-town, workaday-warm: festival's heart at a barge-pole tempo, concertina instead of bells. |
| Mother-daughter scene (Beat 4, from "Say why") | `silence` | Music out for the beam; back to town theme on Maren's "She tars the boat." |
| `lockfive` day (Beat 5) | `silence` | The chamber scores itself: drips, chain, the river in the walls. No music until back upstairs. |
| Night quay + dock scene (5½) | `forest` (forestA, placeholder) | **← slot two for the 'dellhollow' theme: a night-quay variant** — same tune, half tempo, music-box register ("the town, asleep, still holding"). |
| Winches (Beat 6) | `silence` + `rumble`/`chime` | Odessa's arrival gets no sting — her footsteps are the sting. |
| Flume run (Beat 7) | `silence` under the glide; nothing but `shake`/`buzz`/sprays under the run | Music re-enters `resolve` on the tailwater stars, exactly as the Lanternstead lantern-lighting does it. |
| Landing (Beat 8) | `resolve` | Warm; `silence` on the final two narrates. |
| End card | `AudioSys.finale()` | Mirrors both existing chapter endings. |

---

## (g) Chapter One light touch — Vesper's search, planted (for the engine agent)

Two lines, one anchor, `public/js/chapter1.js`. Dry-Vesper only; no mysticism, no hole-in-
the-map speech — the plant is that "where are you from" is an open file, nothing more.

**Anchor:** `talkTo`, `poppy` festival branch (the Vesper side), between these two existing
lines:

```js
['poppy:laughing', 'Chart the— HA! Did you hear her? Eat two.'],
// ── insert here ──
['vesper', 'Fine. Question, though — everyone keeps saying “the Kindling Hour” like I was born knowing what it is.'],
```

**Insert (exactly two lines):**

```js
['poppy', 'And where’s home for you, love? Everybody’s road starts somewhere.'],
['vesper', 'Somewhere is under review. I walk routes for a living — ask me again when the survey’s done.'],
```

Why here: Poppy is the village's hospitality-as-law voice — "where's home" is exactly her
question; Vesper deflecting it with a filing joke is exactly the woman who, one chapter
later, tells Lake about the grid on the dock. No other Ch.1 line needs to change.
(Alternative anchor if the Poppy branch is judged too long: `playMeet`, immediately after
`['vesper', 'Vesper. Mapmaker. …']` — same two lines, with Lake in Poppy's role; the Poppy
placement is preferred because the pact scene must stay lean.)

---

## (h) Ch2 → Ch3 bridge & seam notes (for the engine agent — REQUIRED)

Dellhollow ends **north on the river**, in the boat, party of three plus cat. The
Lanternstead chapter (now Chapter Three; script at `docs/chapter3-lanternstead-script.md`)
cold-opens on the grey Order road, on foot. The bridge is a river-landing: the river shoals
and bends away; they put ashore where the old road comes down to the water.

**1. Replace the Lanternstead cold-open's first narrate** (`playRoadOpen`, currently:
*"They walked until the last light of Emberbrook was gone behind them, slept badly under a
bramble, and the first morning of winter came up grey and stayed that way."* — that line now
opens Dellhollow, its rightful position). Proposed replacement:

> `{ narrate: 'Two days the river ran them north, quick and law-abiding — and then it shoaled grey among the marshes and bent away east, from every road at once. They put the boat ashore at an old stone landing where mossed steps climbed to a mossed road, moored her the way Maren’s father would have wanted, and walked.' }`

The second narrate (*"The road was Order stone under three hundred years of moss…"*) stands
unchanged and lands even better off the water.

**2. Mochi's hiss count.** Ch3's Stranger beat says *"Mochi hissed. He has never once
hissed."* Hiss #1 now happens at the Dellhollow ravine. Proposed replacement (keeps the
joke):

> `{ say: ['lake', 'Mochi hissed again. Twice in his life now — both times at that silhouette. Grandmother used to say: when the cat votes, count it twice.'] }`

**3. Maren exists in Chapter Three+.** The Lanternstead implementation has no Maren — she
needs a follower slot (reuse the Tally follower job; she and Tally can share the trailing
position logic with different offsets) and at least token presence in its beats. Minimal
suggested insertions (engine agent's discretion; keep her light — the chapter is Tally's):
supper — `['maren', 'Four places. We’re five and a cat. …I’ll get the wobbly stool, I ALWAYS get the wobbly stool.']`;
wall-map — `['maren:awed', 'Dellhollow. We’re ON somebody’s map. Ma would say that’s no excuse for anything.']`.
Her Stranger-beat and swarm reactions can go through `system` until fuller lines are written.

**4. The boat.** Beached at the Ch3 landing (narrate above). It stays offscreen set-dressing
until story design decides its future (nb: Ch4 is a ferry chapter — the outline owns that
call, not this script).

**5. Renumbering.** The current `chapter2.js` banner (`'— CHAPTER TWO —' / 'The
Lanternstead'`) becomes `'— CHAPTER THREE —'`; `drawEnd` gets 'End of Chapter Three'; this
chapter takes `Chapter2` / checkpoint-menu slots; the light-touch in §(g) applies to
`chapter1.js`. Ch1's ending line 'Come on, partner — first lamp.' needs **no change** — the
first Order road-lamp now pays off two chapters later, and 'as promised' in the Lanternstead
Beat 1 still reads true.

**6. Assets.** `SPEAKERS`/`LOOKS`/`EXPRESSIONS` additions per §(b): `maren` (happy,
determined, awed), `odessa` (grave, warm), minor `hobb`, `pell` (neutral busts). The Tenant
and the boat are art, not speakers.
