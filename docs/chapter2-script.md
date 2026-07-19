# CHAPTER TWO — "The Lanternstead" — complete script

Design + script source for `public/js/chapter2.js`. Written against the Chapter One vocabulary
(`public/js/chapter1.js`) and the story bible (`STORY.md`); §7 register rules are law here:
plain knowledge spoken warmly, tradition stated confidently and never explained, mysteries left
alone. The Warden is never named, never sneered at; moths are vermin as far as anyone on screen
knows; nobody says Ashfield.

Continuity contract with Chapter One's ending: the chapter opens on the same pair, the same
grey road, the same cat — and the **first dead road-lamp is the "first lamp"** Vesper named in
the last line of Chapter One. Honor it in the opening beat.

Chapter flags (suggested):

```js
flags: {
  roadIntro: false, roadLamps: 0, strangerSeen: false,
  arrived: false, wellDone: false, supperDone: false,
  swarmActive: false, swarmDone: false, hooded: false,
  letterRead: false, mapSeen: false, tallyJoined: false,
  ended: false, endT: 0,
}
```

---

## (a) Scene definitions sketch — for the art pipeline

All coordinates on the 1344×768 canvas, same conventions as Chapter One (`lamps` have a head
`{x,y}` and an interact `base [x,y]` roughly 110–150px below; exits are edge zones; the baked
mask governs walkability — the `walk` polygon is fallback only).

### `road` — the grey road north of the gate

Autumn wood gone grey-green: birches and oaks with the color drained to lichen tones, moss
swallowing the old Order stonework. The road is dressed stone under moss — *built*, not worn —
entering bottom-left and winding up to the top-right. Drifting moths cluster in the dark
stretches (engine: `mothAmbience: true`; if cheap to do, scale moth density down near lit
lamps). Light state: flat grey overcast morning.

```js
road: {
  states: { gray: 'assets/scenes/road/main.png' }, state: 'gray',
  viewH: 700, charH: 120, speed: 190, mothAmbience: true,
  tints: { gray: '#96a091' },                    // grey-green, colder than the gate scene
  lamps: [                                       // three dead Order road-lamps, relightable
    { x: 318, y: 400, lit: false, id: 'rlamp1', base: [320, 545] },   // south stretch
    { x: 705, y: 315, lit: false, id: 'rlamp2', base: [707, 455] },   // mid rise
    { x: 1075, y: 240, lit: false, id: 'rlamp3', base: [1077, 372] }, // near the north bend
  ],
  exits: [
    { zone: { x: 40, y: 690, w: 280, h: 78 }, to: null,              // south — back to the gate
      enabled: () => false,
      deniedLine: ['lake', 'Back through the Gate? Not with the spark this side of it. The rounds only go one way now.'] },
    { zone: { x: 1200, y: 60, w: 144, h: 230 }, to: 'lanternstead', spawn: [170, 620, 'right'],
      enabled: () => Chapter2.flags.strangerSeen,
      deniedLine: ['lake', 'That stretch ahead is solid moths. Light the lamps first — nobody walks the dark part of a round.'] },
  ],
}
```

Points of interest (must be in the painting):
- **Road-lamps ×3** at the positions above — Order pattern, same brass door as Emberbrook's
  lamps, taller and plainer; moss to the knee. Rendered lamp-glow handled by engine when lit.
- **Waymarker A** at (480, 615): a carved waystone half-swallowed by bramble — carved pointing
  hand, mile-mark eaten by moss. Interact radius ~70.
- **Waymarker B** at (895, 425): a leaning stone, carved "LANTERNSTEAD —" then weather.
- **The Stranger's mark** at ~(1150, 155): a clear straight sightline up the far road for the
  glimpse cutscene — keep the top-right stretch of road visibly empty and framed (trees pull
  back). The stranger entity stands here, small (h ≈ 120), then vanishes. **No new art
  required** — reuses the Chapter One `stranger` sprite at distance.
- Dark stretches between lamps read *darker* than the rest — the moths pool there.

### `lanternstead` — the waystation courtyard

A round stone tower right-of-center, four stories, crowned by the **great-lantern**: a
glass-and-brass lantern room the size of a small chapel, polished bright, visibly *dead* —
clean cold glass around an unlit wick-carriage. Overgrown courtyard walled in low tumbled
stone; Tally's absurd domestic order stitched through the ruin.

Scene states (art: minimum four variants of the one painting, or dusk/night paintings + lit
overlay for the lantern head):

```js
lanternstead: {
  states: {
    dusk:    'assets/scenes/lanternstead/dusk.png',     // arrival — amber-grey, washing on the line
    night:   'assets/scenes/lanternstead/night.png',    // swarm — near-dark, tower a silhouette
    lantern: 'assets/scenes/lanternstead/lantern.png',  // night + the great-lantern ROARING (warm ring of light over the whole yard)
    morning: 'assets/scenes/lanternstead/morning.png',  // pale blue-gold, frost outside the light-ring only
  }, state: 'dusk',
  viewH: 720, charH: 122, speed: 190, mothAmbience: true,   // ambience off (or near-zero) in 'lantern'/'morning'
  tints: { dusk: '#c9a184', night: '#5d6377', lantern: '#e0b071', morning: '#aebdc9' },
  exits: [
    { zone: { x: 60, y: 700, w: 250, h: 68 }, to: 'road', spawn: [1180, 210, 'left'],
      enabled: () => Chapter2.flags.arrived && !Chapter2.flags.swarmActive,
      deniedLine: ['tally', 'After dark? Flamebearer, rule one! The road will keep till morning — it has kept three hundred years.'] },
    { zone: { x: 830, y: 460, w: 80, h: 90 }, to: 'lanternstead-int', spawn: [672, 660, 'up'] },  // tower door
  ],
}
```

Points of interest (must be in the painting, approximate positions):
- **Tower** base spanning ~(830–1110, 250–560); **tower door** (heavy Order door, twin-lamp
  carving) at (870, 505). **Great-lantern** head centered ~(965, 95) — the money object of the
  chapter; in `lantern` state it throws a warm ring over the entire courtyard.
- **Winch** at (1045, 545): a brass windlass set into the tower base — chain runs up the tower
  wall to the lantern head (raises the wick-carriage into the flame-gate). Co-op station 1.
- **Wick-gate** at (880, 470), left of the door: a brass door the size of a hatch, the same
  pattern as a street-lamp's little door scaled up. Co-op station 2.
- **Well** at (430, 505): stone well with a two-handled crank windlass. Co-op (small).
- **Washing line** strung (250, 300)→(520, 275): three patched shirts and one enormous nightcap.
- **Order prayer flags** strung from tower to a post, (760, 190)→(1100, 250): small faded
  block-printed flags, each with a lamp sigil.
- **Vegetable rows** patch (150–430, 585–700): ruler-straight rows, little stick labels.
- **Crow perch** at (585, 350): a tall post with a brass ring and rail — the post-crow station.
  Crows on it in every state; "Twenty-Two" lands here in Beat 5.

### `lanternstead-int` — the round room

One round room filling the tower's ground floor: curved shelves of rite-books, a cold hearth
laid but only cook-fire small, one bed with hospital corners and one hammock, a big table, and
the Order's wall-map of the dead circuit. Warm browns and brass; candle-lit at evening, pale
window-light at morning.

```js
'lanternstead-int': {
  states: { evening: 'assets/scenes/lanternstead-int/evening.png',
            morning: 'assets/scenes/lanternstead-int/morning.png' }, state: 'evening',
  viewH: 725, charH: 205, speed: 280,
  tints: { evening: '#e8b184', morning: '#c9c2ae' },
  exits: [{ zone: { x: 610, y: 690, w: 130, h: 78 }, to: 'lanternstead', spawn: [870, 585, 'down'] }],
}
```

Points of interest:
- **Rite-books** — curved shelving along the back wall, ~(140–620, 210–330); interact at
  (380, 330). Thirty-nine hand-copied volumes, worn round with rereading.
- **Cold hearth** at (250, 430) (interact (250, 480)): laid, swept, ready; the fire in it small
  and careful — a cook's fire, not a keeper's. Above the mantel: an **empty polished bracket**
  exactly the size of a lamplighter's lighter.
- **Wall-map** at (1060, 300) (interact (1060, 420)): a big framed chart of the circuit — a ring
  of valleys around the deep wood, one road joining them, each valley with a lamp sigil; tiny
  meticulous tally-marks inked under every station name. Beat 6 centerpiece.
- **Bed** at (185, 615): made with hospital corners — the walkers' bed, kept ready 300 years.
  **Hammock** at (1150, 545), strung by the window: Tally's.
- **Table** at (672, 555): supper staging; candles; Vesper's chart-work spreads here.

---

## (b) NPC roster — for the character pipeline

### TALLY — new, full design (`tools/characters/tally.json` material)

**desc:** A round, warm-faced friar in his late thirties, endlessly cheerful: the last keeper
of the Order's waystation. Soft build, apple cheeks, round brass-rimmed spectacles that catch
the light, curly mid-brown hair thinning honestly on top (no shaved tonsure — nature is
handling it), a few days' soft stubble. He wears a patched ash-grey wool habit to the shin,
sleeves rolled to the elbow for chores, with an **ember-orange stole/sash** block-printed with
a row of small lamp sigils, a rope belt hung with a polishing cloth, a tiny brass hand-bell,
and a slim strapped book of rites, fingerless wool gloves, and sturdy mud-proofed boots.
Everything mended with liturgical neatness; nothing new. He should read as a man keeping
civilization alive by hand, and delighted about it.

**sheetHint:** same face, round brass spectacles, curly brown hair thin on top, ash-grey
patched habit with sleeves rolled, ember-orange lamp-sigil stole, rope belt with cloth +
hand-bell + strapped book, fingerless gloves, sturdy boots.

**expressions** (for the art agent — exactly these three):
- `happy` — the default beam: eyes nearly shut behind the spectacles, cheeks lifted, a smile
  that has clearly been practiced on crows and vegetables for want of people.
- `awed` — spectacles slightly slipped, eyes wide and wet, lips parted; the face of a man
  seeing the thing he has only ever read about. (Beat 4 lives on this one. It should be able
  to carry laughing-and-crying at once.)
- `earnest` — leaning in, brows up, hands implied mid-gesture: doctrine matters, please
  understand, this is important and also wonderful.

**Speaker entry** (`assets.js`): `tally: { name: 'Friar Tally', color: '#d97b3f' }` —
ember-orange, warm against Lake's brass and Vesper's teal.
**LOOKS row** (pixel sprite): `tally: { hair: '#7a5c3d', outfit: '#8a8494', shade: '#6b6577',
accent: '#d97b3f', skin: '#f0c49e', hairstyle: 'short', robe: true }` — round silhouette if the
sprite baker supports a wide variant.

### TWENTY-TWO — the grey post-crow (entity, not a speaker)

A big ash-grey crow — storm-grey feathers going pale at the collar, a scarred beak, one brass
message-ring on the left leg with a tiny tube. Expression: permanently unimpressed. She is the
Order's message line, still flying a dead route because Tally feeds it. Small sprite (h ≈ 34)
plus, ideally, a landing pose for the perch. Lines about her go through `system`.

### Returning, no new art
- **stranger** — Chapter One sprite, used once at distance (h ≈ 120). Hooded, pale-blue lantern.
  He has no dialogue. He does not get dialogue.
- **mochi** — as is. He gets his first hiss (text-rendered; optionally a flat-ears frame if the
  sprite sheet ever grows one — not required).
- **vesper, lake** — as is. **rowan** appears only as his letter — render letter lines with
  speaker `rowan` and the existing `hollow` expression bust (see Beat 5 note).

---

## (c) Beat-by-beat script

Speaker keys: `vesper / lake / tally / mochi / rowan` (letter only) / `stranger` (never
speaks) / `system`. Expression tags used: all existing Ch.1 tags, plus `tally:happy`,
`tally:awed`, `tally:earnest`.

### BEAT 1 — Cold open: the grey road (`playRoadOpen`)

Trigger: chapter start, both players present, `!roadIntro`. Spawns: vesper (150, 640, 'right'),
lake (235, 665, 'right'), mochi ahead of them at (300, 620).

```js
Cutscene.play([
  { mood: 'forestB' },                                     // the deep wood, uneasy
  { banner: { title: '— CHAPTER TWO —', sub: 'The Lanternstead', dur: 5 } },
  { cam: { x: 340, y: 560, viewH: 520 } },
  { wait: 1.2 },
  { narrate: 'They walked until the last light of Emberbrook was gone behind them, slept badly under a bramble, and the first morning of winter came up grey and stayed that way.' },
  { narrate: 'The road was Order stone under three hundred years of moss — built by people who measured in lamps, for a walk that stopped.' },
  { run: () => { /* mochi trots to (300, 620), tail up */ } },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi walks exactly down the middle of the road, tail up — the only one of the three who has decided this is a procession.)'] },
  { move: { ent: vesper, x: 290, y: 600, speed: 120 } },
  { face: { ent: vesper, dir: 'right' } },
  { say: ['vesper', 'There. Dead lamp, ten o’clock, brass door and all. First lamp, partner — as promised.'] },
  { say: ['lake', 'It’s ours. I mean — it’s the same pattern as ours. Same door, same wick. This whole road belonged to the Order.'] },
  { say: ['vesper', 'Three of them between here and the rise, and the moths sit thickest exactly where the lamps aren’t. So we do this your way. Lamp to lamp.'] },
  { say: ['lake', '(A road of my own lamps. Grandmother walked me the village round a thousand times and never once said the round kept going.)'] },
  { say: ['vesper:thinking', '(New page. “The North Road. Surface: Order stone. Weather: grey, permanent. Company: one lamplighter, one cat, every moth in the world.”)'] },
  { camRelease: true },
  { run: () => { F.roadIntro = true; } },
]);
```

**Lamp mechanic, reused** — Lake lights the three road-lamps with the Chapter One `lightLamp`
flow (`AudioSys.lampOn`, sparkle burst, buzz). His lamp-thoughts now carry road-lore
(tradition register — stated plainly, never explained):

```js
if (F.roadLamps === 1) Dialog.start([
  { who: 'lake', text: '(One. The door swings like it was oiled last week. Order brass doesn’t rust — grandmother said they built for a longer war than weather.)' },
]);
// then, first time only, the observed mechanic — small follow-on dialog:
//   vesper: 'The moths just… made room. Noted: they don’t cross the lamplight.'
//   lake:   'A lit lamp is a shut door. Grandmother’s phrase. I never asked who it was shut against.'

if (F.roadLamps === 2) Dialog.start([
  { who: 'lake', text: '(Two. A mile-lamp. The walkers measured the road in light — one lamp, one hour, one prayer. I only know the saying: count lamps, not miles. Miles don’t care about you.)' },
]);

if (F.roadLamps === 3) Dialog.start([
  { who: 'lake', text: '(Three. Lit, the road looks kept. Somebody should tell the moths this street’s taken. …I suppose I just did.)' },
]);
```

**Interacts (road):**
- Waymarker A — by role:
  `vesper`: 'A waymarker, swallowed to the shoulders. The carved hand points north; the
  mile-count is moss. Vesper records it as “one, presumed.”'
  `lake`: 'The stone hand points up the road. Someone cut a small sun above it — or a lamp. On
  this road, likely a lamp.'
- Waymarker B — both: 'This one leans like it stopped believing in the road. The carving reads
  “LANTERNSTEAD —” and then three centuries of weather.'
- Dark stretch (optional ambient interact between lamps 2 and 3): 'The moths here drift
  without hurry and without direction — the way lost things drift, waiting to be found.'
  (Direct reprise of the Chapter One ending line; free resonance.)

### BEAT 2 — The Stranger glimpse (`playStranger`)

Trigger: `roadLamps >= 3 && !strangerSeen`, any player past x > 950 on `road`. Canon beat
(STORY §5): full pale-blue lantern, a bow to the *lighter*, gone between blinks, Mochi's first
hiss. Register: wary bafflement; no identity, no motive, no speculation beyond what's seen.

```js
Cutscene.play([
  { mood: 'silence' },
  { run: () => { const s = this.npcs.stranger; s.hidden = false; s.scene = 'road'; s.x = 1150; s.y = 155; s.dir = 'down'; } },
  { cam: { x: 1040, y: 280, viewH: 560 } },
  { wait: 1.2 },
  { narrate: 'Far up the road, where their lamplight ran out, stood a light that was not theirs. A lantern, carried. Full to the glass. And pale, pale blue.' },
  { say: ['vesper', 'Lake.'] },
  { say: ['lake', 'I see him.'] },
  { say: ['mochi', 'Hhhhhhhh.'] },
  { say: ['system', '(A sound is coming out of Mochi that neither of them has ever heard a cat make. Low. Level. Aimed.)'] },
  { say: ['vesper:worried', '(Hooded. Tall. Not moving like a man who has been walking — moving like a man who has never been doing anything else.)'] },
  { say: ['lake', 'Sir! The road’s dark past the bend — you’re welcome to walk in our light—'] },
  { wait: 1.0 },
  { narrate: 'The stranger did not come closer. He looked at them — or at something they carried — for a long moment. And then he bowed: deep, and slow, and courteous, the way you bow to an altar. Not to them. To the small brass flame in Lake’s hand.' },
  { wait: 0.8 },
  { flash: 0.5 },
  { run: () => { this.npcs.stranger.hidden = true; Net.send({ type: 'buzz', ms: 120 }); } },
  { narrate: 'Between one blink and the next, the road was empty.' },
  { wait: 0.8 },
  { say: ['vesper', '…Gone. Gone HOW? That’s a quarter mile of open road and nothing to be behind.'] },
  { say: ['lake:worried', 'He bowed. To the lighter — I know where he was looking.'] },
  { say: ['vesper', 'People don’t bow to lighters.'] },
  { say: ['lake', 'Lamplighters do. On the high days. Grandmother bowed exactly that deep and exactly that slow, and I never saw another soul do it in my life.'] },
  { say: ['vesper:thinking', '(Entry: one walker, unmapped. Lantern: full, blue, wrong. Manner: courteous. Departure: unexplained. Filed under things I refuse to call impossible twice in one week.)'] },
  { say: ['lake', 'Mochi hissed. He has never once hissed. Grandmother used to say: when the cat votes, count it twice.'] },
  { say: ['vesper', 'And how does the cat vote?'] },
  { say: ['lake', 'Against.'] },
  { mood: 'forestB' },
  { camRelease: true },
  { run: () => { F.strangerSeen = true; } },   // north exit opens
]);
```

### BEAT 3 — Dusk at the Lanternstead: meet Tally (`playArrival`, `playWell`, supper)

Trigger: first entry to `lanternstead` (state `dusk`). Tally starts hidden behind the tower.
Mood: `resolve` as stand-in (see §f — a cozy waystation variant is genuinely warranted).

```js
Cutscene.play([
  { mood: 'resolve' },
  { cam: { x: 620, y: 380, viewH: 620 } },
  { narrate: 'They smelled the Lanternstead before they saw it: woodsmoke, turned earth, and — impossibly, out here at the end of the world — laundry.' },
  { wait: 0.8 },
  { say: ['vesper', 'A tower. A well. A vegetable patch in ruler-straight rows. And… shirts.'] },
  { say: ['lake', 'Somebody LIVES here.'] },
  { say: ['tally', '…aaaand the ninth observance, the polishing of the glass, la-la-la, that the light find no dust upon arrival—'] },   // offstage, sung
  { run: () => { const t = this.npcs.tally; t.hidden = false; t.x = 1060; t.y = 470; /* rounds the tower with a basket */ } },
  { move: { ent: tally, x: 860, y: 520, speed: 120 } },
  { run: () => { /* Tally sees them. Basket stays, barely. */ } },
  { wait: 0.8 },
  { say: ['tally:earnest', 'Oh! Oh. Wait. Wait wait wait — I know this one.'] },
  { say: ['tally', '“WHO WALKS the dead road?” — no, sorry, it’s “who KEEPS the dead road,” and then YOU say—'] },
  { say: ['vesper', '…We walk it?'] },
  { say: ['tally', 'You’re not supposed to ANSWER! Nobody has EVER answered!'] },
  { move: { ent: tally, x: lake.x + 60, y: lake.y, speed: 150 } },
  { say: ['tally:awed', '…Flamebearer. Flamebearer, is that flame ALIVE?'] },
  { say: ['lake', 'It’s— yes? It’s my lighter. It’s warm, if you want to—'] },
  { say: ['tally:awed', 'Don’t— don’t let me touch it. There’s a correct distance. I know the correct distance. I have never once needed the correct distance.'] },
  { wait: 1.0 },
  { say: ['tally:earnest', 'Three hundred years this station has kept the Rite of the Open Door. Firewood dry. Beds aired. Great-lantern polished — I do the glass on Sundays.'] },
  { say: ['tally', 'You’re real. The office is real. I have the whole liturgy and nobody ever came.'] },
  { wait: 1.2 },
  { say: ['vesper:worried', '…How long have you been out here alone?'] },
  { say: ['tally:happy', 'Alone? Madam, I have nineteen crows, a well with opinions, and the entire Order of Lamplighters, bound in thirty-nine volumes.'] },
  { say: ['tally:earnest', 'And now — a Flamebearer and a Waykeeper. A walking two, at my door, at dusk, in the correct season. The road was never meant to be walked alone, you know. It says so on the door.'] },
  { say: ['vesper', 'Vesper. Mapmaker — not, that I’m aware, a Waykeeper.'] },
  { say: ['tally:earnest', 'You walked here off the map, madam, in front of a Flamebearer. I won’t argue doctrine with the doctrine standing in my yard.'] },
  { say: ['lake', 'Lake. Lamplighter. Emberbrook.'] },
  { say: ['tally:happy', 'Emberbrook! The Third Daughter! Founded from a carried ember, one wick, one walking— sorry. I will be doing this all evening. Tally. Friar Tally, if titles survive being the last one.'] },
  { say: ['tally', 'You’ll want supper. The rite is clear: the walkers eat first.'] },
  { say: ['vesper', 'Why does everyone on this road make feeding me a LAW?'] },
  { say: ['tally:happy', 'Because the Order wrote good laws, madam.'] },
  { camRelease: true },
  { run: () => { F.arrived = true; Objective.set('Help Tally draw water — the well takes two'); } },
]);
```

**Small co-op moment — the well** (`playWell`): triggered by either player interacting with the
well while `arrived && !wellDone`. Tally trots over.

```js
Cutscene.play([
  { say: ['tally:earnest', 'Supper wants water, and the well was cut by the Order — which is to say, the crank takes two. Everything here takes two. It was that kind of Order.'] },
  { run: () => { /* stage players at the two crank handles, (395, 520) and (465, 520) */ } },
  { bothHold: { prompt: 'HOLD  A — haul the bucket, together', dur: 1.6 } },
  { run: () => { AudioSys.chime(); Net.send({ type: 'buzz', ms: 120 }); } },
  { say: ['system', '(The bucket arrives. It contains water, and one entirely unhurried frog.)'] },
  { say: ['vesper', 'Your well has a frog.'] },
  { say: ['tally:happy', 'That’s Brother Frog. He predates me. Back he goes.'] },
  { say: ['mochi', 'Mrrp.'] },
  { run: () => { F.wellDone = true; Objective.set('Supper at the Lanternstead — go inside'); } },
]);
```

**Supper transition:** entering `lanternstead-int` with `wellDone` plays a short fade-narrate
and sets `supperDone` (see Beat 4 trigger). Villager-style `talkTo` branches for Tally during
the evening (courtyard or interior, repeatable, in this order then looping the last):

1. ```
   tally:happy   'Ask me anything! I know everything and have seen none of it. I am the world’s
                  leading authority on things I have never watched happen.'
   lake          'The great-lantern, then. What was it for?'
   tally:earnest 'The waystations ring the deep wood — one great-lantern each. Lit, they warded
                  the road for the walkers, and each answered the next: light in sight of light,
                  all the way around the circuit. The rite calls it the necklace.'
   tally:happy   'I also call it the necklace. It’s a good rite.'
   vesper        'And it’s been dark since—'
   tally         'Since a hundred and nine years before my order bought its last new kettle. We
                  were never a hasty organization.'
   ```
2. ```
   tally:earnest 'Friars keep; lighters walk. I’m the fourteenth keeper of this station — and
                  the first to keep it alone.'
   tally         'My teacher taught me the rounds the way his teacher taught him: for the day
                  the walking twos came back. He died believing they would.'
   tally:happy   'I feed his crows. And look — he was right.'
   ```
3. (repeat) `tally:happy 'Eat! Doctrine can wait an hour. Doctrine has waited three hundred years — it’s very good at it.'`

**Mochi flavor (talkTo, at the station):**
`system`: '(Mochi has inspected the entire station and is now sitting on the rite-books. Tally
appears to regard this as a liturgically significant endorsement.)'

### BEAT 4 — Night: the first moth swarm, the great-lantern (`playSwarm`)

Trigger: `supperDone` — plays automatically after the supper fade (players placed in the
courtyard, scene state `night`). Set `swarmActive` for the duration (locks the south exit).

```js
Cutscene.play([
  { narrate: 'Supper was turnips, doctrine, and the best bread either of them had eaten since Emberbrook. Night came down on the Lanternstead like a lid.' },
  { run: () => { F.swarmActive = true; Field.setSceneState('lanternstead', 'night'); } },
  { mood: 'silence' },
  { wait: 1.5 },
  { say: ['system', '(Mochi’s ears go flat. He is facing the courtyard wall. He is very, very still.)'] },
  { say: ['mochi', 'Hhhhhhhh.'] },
  { say: ['tally:earnest', 'The cat. The books draw PICTURES of a cat doing that— oh. Oh no. The books SAY this. “In the dark season the strays seek the walking flame”— outside. Everyone outside, NOW.'] },
  { cam: { x: 672, y: 420, viewH: 640 } },
  { run: () => { /* moth storm: heavy particle spawn from the walls, spiraling toward Lake */
      Particles.burst(60, () => ({ kind: 'moth', /* converge on lake.x, lake.y */ }));
      AudioSys.hushSting(); Net.send({ type: 'buzz', ms: 400 }); } },
  { shake: 4 },
  { say: ['vesper', 'Define “seek the walking flame,” Tally — QUICKLY.'] },
  { say: ['tally:earnest', 'Moths eat light, madam, and out here your partner is carrying the only lit thing in the world! It’s rule ONE — no bare flame outdoors after dark on the dead road — it’s the FIRST rule and I have never once needed to say it out loud!'] },
  { say: ['lake:worried', 'They’re coming through my coat— I can’t put it out, it doesn’t GO out—'] },
  { say: ['tally:earnest', 'Don’t put it out — OUTSHINE it! The great-lantern! A lit lamp is a shut door; a GREAT lamp is a shut GATE! Wick and winch — it takes two, it always takes two!'] },
  { say: ['tally', 'Waykeeper — the winch! Nine turns, then HOLD! Flamebearer — the wick-gate! Brass door, same as your lamps, only rather — rather LARGE—'] },
  { run: () => { /* stage: vesper → winch (1045, 545); lake → wick-gate (880, 470); tally between, directing */ } },
  { say: ['lake', '(Mean it. A lamp for the whole road — for every walker who never came, and the one keeper who stayed. …That one’s easy to mean.)'] },
  { bothHold: { prompt: 'HOLD  A — wick and winch, together', dur: 2.6 } },
  { flash: 0.9 }, { shake: 5 },
  { run: () => { Field.setSceneState('lanternstead', 'lantern');
      AudioSys.rumble(); AudioSys.chime(); Net.send({ type: 'buzz', ms: 500 });
      Particles.burst(30, () => ({ kind: 'sparkle', /* from the lantern head, (965, 95) */ })); } },
  { narrate: 'The great-lantern of the Lanternstead took the flame like a held breath let go — three hundred years of polish and readiness, and then LIGHT: a roar of it, out across the grey road in every direction at once.' },
  { run: () => { /* swarm turns: moths wheel once around the tower, then scatter outward and thin */ } },
  { narrate: 'The swarm broke against it like water on a stone. The moths rose, wheeled once around the tower — and scattered back into the dark, thin and aimless again.' },
  { wait: 1.2 },
  { mood: 'resolve' },
  { cam: { x: 900, y: 300, viewH: 560 } },
  { say: ['tally:awed', '…Ha. Hahaha. It’s— I did the glass on Sundays. Every Sunday. And the books never once say that it’s YELLOW—'] },
  { say: ['system', '(Tally is laughing. Tally is also crying. He does not appear to have noticed either.)'] },
  { say: ['lake:tender', 'You lit it too, Tally. Whoever keeps the wick dry is lighting the lamp — grandmother’s rule. You’ve been lighting this one your whole life. It just caught tonight.'] },
  { say: ['tally:awed', '…I’m going to write that in the margin of Volume One.'] },
  { wait: 0.8 },
  { say: ['tally:earnest', 'Now. Rule one, said properly this time: no bare flame outdoors after dark. The stores keep a walking-hood — brass cowl, Order pattern. The flame breathes; the light stays home.'] },
  { toast: { text: '✦ The walking-hood — the lighter travels shielded at night', color: '#e0a94e' } },
  { say: ['vesper:thinking', '(Entry: lamps ward moths. Great lamps ward roads. And after dark my partner is the most interesting thing in the world to every hungry thing on it. Underlined twice.)'] },
  { fadeTo: 1 }, { wait: 1.0 },
  { run: () => { F.swarmDone = true; F.hooded = true; F.swarmActive = false; } },
]);
```

**Interacts, post-lantern (courtyard, `lantern`/`morning` states):**
- Great-lantern (lit): 'The great-lantern, burning. The courtyard has a heartbeat now. The
  moths keep to the far dark, like a tide around a rock.'
- (Before, `dusk`/`night`): 'The great-lantern crowns the tower: glass the size of a room,
  brass polished bright — around a wick that has never in living memory been lit. It is the
  cleanest dead thing on the whole road.'

### BEAT 5 — Morning: the grey post-crow, Rowan's letter (`playLetter`)

Trigger: morning fade-in after Beat 4 (scene state `morning`, players near the crow perch —
or auto-play after a short free-roam breath). Mood: `hush` for the reading.

Implementation note: render the letter with speaker `rowan` and the **`hollow`** expression
bust — Vesper's voice reading, Rowan's emptied face on the box. The quotation marks in the
text carry the framing.

```js
Cutscene.play([
  { narrate: 'Morning came up almost blue. Inside the great-lantern’s ring the frost had kept off the vegetable rows — and the crows were shouting about a visitor.' },
  { run: () => { /* Twenty-Two lands on the perch (585, 350); brass tube on her leg */ } },
  { cam: { x: 585, y: 430, viewH: 500 } },
  { say: ['tally:happy', 'Twenty-Two! MANNERS!'] },
  { say: ['vesper', 'You number your crows?'] },
  { say: ['tally', 'They’re post-crows, madam — the Order’s message line. The route runs to every Heartlight; the birds still fly it, because I still feed it. The letters stopped long before me.'] },
  { say: ['tally:earnest', 'She’s carrying. She’s— that is the first letter on this route since my teacher died.'] },
  { wait: 0.8 },
  { say: ['lake', 'Somebody at our end remembered what the old perch by the gate was for.'] },
  { say: ['vesper', 'Rowan.'] },
  { mood: 'hush' },
  { run: () => { /* vesper takes the tube; unrolls */ } },
  { say: ['vesper', 'It’s his hand. Steady as ever. “To the mapmaker and the lamplighter, gone north.”'] },
  { cam: { x: 620, y: 480, viewH: 420 } },
  { say: ['rowan:hollow', '“Day two. The village is fed. The mill turns. The weather has been fair for the season.”'] },
  { say: ['rowan:hollow', '“Notices: the baker bakes daily; output normal. The child Pip continues his instruction of the woman Mara; progress is recorded. The fisherman reports that the pond has fish in it. This is all of the news.”'] },
  { say: ['rowan:hollow', '“The ledger is kept. I find I have nothing further to put in this letter, though I sat an hour with it. Provisions follow with the bird. — R. Elder.”'] },
  { wait: 1.6 },
  { say: ['vesper', '…It’s all true. Every line of it is true, and correct, and in order.'] },
  { say: ['lake', 'That’s what’s wrong with it.'] },
  { say: ['vesper:sad', '(Rowan makes jokes. Rowan makes jokes the way the mill turns. There is not one joke in this letter.)'] },
  { say: ['lake:worried', 'He wrote “the woman Mara.” He named her to the flame himself, the day she was born — he used to tell that story every Emberwake. Now she’s “the woman Mara.”'] },
  { wait: 1.2 },
  { say: ['vesper:determined', 'New page. “Day two: the village is fed, and fading. The facts are keeping. The people aren’t.” …We walk faster.'] },
  { say: ['lake', 'She used to say a street goes cold slower than it warms. It’s the only mercy we’ve got. Let’s spend it walking.'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi leans, very briefly, against Lake’s boot. Then pretends he didn’t.)'] },
  { camRelease: true },
  { run: () => { F.letterRead = true; Objective.set('The round room — ask Tally about the road ahead'); } },
]);
```

### BEAT 6 — The wall-map, Tally joins, end card (`playWallMap`)

Trigger: interacting with the wall-map (or talking to Tally) in `lanternstead-int` with
`letterRead`. Tally stands at the map, (990, 460).

```js
Cutscene.play([
  { cam: { x: 1000, y: 380, viewH: 480 } },
  { say: ['tally:earnest', 'Before you walk, you should see what road you’re on.'] },
  { say: ['tally', 'The circuit. One road, thirteen stations, ringing the deep wood — a Heartlight in every valley, and every one of them a daughter of the mother-fire at the middle. Emberbrook, here. The Lanternstead — you are here. First station north.'] },
  { say: ['tally:earnest', 'And ahead — Harrowdel. Three days up the circuit. A LIVING valley, Flamebearer: their lamps still answer. The last on this road that do.'] },
  { say: ['vesper', 'And the little marks? Under every name?'] },
  { say: ['tally', 'Sunrises the station has been kept. My teacher started the count; I kept the count. It’s also where I got my name — the crows had names, and I had marks, so.'] },
  { say: ['tally:earnest', 'It is a great many marks, madam. But the count held. That’s the whole of the friar’s rite: hold the count until the walkers come.'] },
  { say: ['tally:happy', 'You came.'] },
  { wait: 1.0 },
  { say: ['lake:worried', 'The walker we saw on the road. Pale lantern, full. If he’s out here—'] },
  { say: ['tally:earnest', 'One road is all there is, Flamebearer. Whatever he keeps, he keeps it somewhere ahead of you.'] },
  { say: ['system', '(Mochi is sitting in the doorway, facing north.)'] },
  { wait: 1.0 },
  { say: ['tally:earnest', 'Which brings me to a request I have practiced, so let me get it out. The station kept the road FOR the walkers. The walkers are back. Therefore the keeping goes WITH you — that’s doctrine. I checked. I checked twice.'] },
  { say: ['vesper', 'Tally. Are you asking to come with us?'] },
  { say: ['tally', 'Desperately, madam.'] },
  { say: ['lake:happy', 'The road was meant to be walked by two. …Nobody ever said ONLY two.'] },
  { say: ['tally:happy', 'I’ll fetch the kettle. Not the good kettle. The WALKING kettle. We have DOCTRINE about kettles—'] },
  { toast: { text: '✦  Friar Tally joined the party  ✦', color: '#d97b3f' } },
  { say: ['vesper:thinking', '(For the record: party of three, one cat, one crow flying the route behind us. The chart is getting crowded. I find I don’t mind.)'] },
  { say: ['tally', 'Twenty-Two flies the circuit — she’ll find us wherever the road puts us. The rest stay and keep the necklace. Somebody must.'] },
  { banner: { title: '✦ The road to Harrowdel ✦', sub: 'three days north — the last living valley on the circuit', dur: 6 } },
  { run: () => { F.tallyJoined = true; /* tally.follow = 'party' — reuse the Mochi follower logic with a larger rest offset */ } },
  { fadeTo: 1 }, { wait: 0.8 },
  { run: () => { /* exterior shot: courtyard, morning, lantern burning; party at the south exit */ } },
  { fadeTo: 0 },
  { cam: { x: 965, y: 220, viewH: 640 } },
  { narrate: 'They left the Lanternstead burning behind them — the first light of the necklace, lit again; a shut gate at their backs and three days of grey road ahead.' },
  { narrate: 'And behind them the great-lantern held its one note of yellow against the winter, saying to anyone on the road what the Order had always meant it to say: keep walking. You are expected.' },
  { mood: 'silence' },
  { run: () => { F.ended = true; AudioSys.finale(); Net.send({ type: 'end' }); } },
]);
```

End card (drawEnd lives in `main.js` — needs a Chapter Two variant): 'End of Chapter Two —
The Lanternstead' / 'the necklace has its first light'.

**Interacts (interior), for completeness:**
- Rite-books: 'Thirty-nine volumes, hand-copied, shelved in liturgical order and re-shelved,
  by the wear on them, several thousand times. Volume One falls open to the creed: “Light does
  not die—”. The rest of the page is worn away by a thumb.'
- Cold hearth: 'The hearth is laid, swept, ready — the fire in it small and careful, a cook's
  fire. Above the mantel hangs an empty bracket, polished, exactly the size of a lamplighter's
  lighter. Waiting.'
- Bed & hammock: 'One bed, made with hospital corners — the walkers' bed, kept ready three
  hundred years. One hammock, strung by the window: Tally's. The arithmetic of a man who never
  stopped expecting company.'
- Wall-map (before Beat 6): 'The Order's wall-map of the circuit: a ring of valleys around the
  deep wood, one road joining them, a lamp sigil at every name — and under every name, years
  of tiny meticulous tally-marks. You don't yet know what they count.'
- Well (after Beat 3): 'The well. Somewhere down there, Brother Frog continues his ministry.'
- Washing line: 'Three shirts patched with liturgical neatness, and one enormous nightcap. The
  washing line of a man keeping civilization alive by hand.'
- Prayer flags: 'Small faded flags, each block-printed with a lamp. Order prayer flags — the
  wind says the rite for you when you are too busy walking. These have been praying nonstop
  for three hundred years.'
- Vegetable rows: 'Cabbages in rows straight enough to survey by. A stick label reads
  “TURNIPS (unconvinced)”.'

---

## (d) Objectives, prompts, markers — per beat

| Beat | `objective()` string | Prompts | Markers / gating |
|---|---|---|---|
| 1 | `The grey road — light the road-lamps (0/3)` (count up; append hint `· two past the rise` style like Ch.1) | `A — light the lamp`, `A — look` (waymarkers) | North exit **denied** until `strangerSeen`; south exit always denied. Moth density marks the dark stretches. |
| 2 | after glimpse: `Make the Lanternstead by dusk — north, lamp to lamp` | — (cutscene) | North exit opens on `strangerSeen`. |
| 3 | `The Lanternstead — someone is singing` → after meet: `Help Tally draw water — the well takes two` → `Supper at the Lanternstead — go inside` | `A — talk to Friar Tally`, `A — the well`, `HOLD A` (well) | Tower door usable from arrival; south exit denied after dark (`tally` deniedLine). |
| 4 | `Moths! — the great-lantern: wick and winch, together` | `HOLD A` (both stations) | `swarmActive` locks all exits for the setpiece. |
| 5 | `Morning — see what the crow brought` | `Next ▸` | Auto-plays or triggers at the perch. |
| 6 | `The round room — ask Tally about the road ahead` → `''` after end | `A — the wall-map`, `A — talk to Friar Tally` | Map interact upgrades to the Beat 6 cutscene once `letterRead`. |

### BEAT 3½ — supper transition (glue, not a beat)

Entering `lanternstead-int` with `wellDone && !supperDone`:
`{ fadeTo: 1 } → set supperDone → return to courtyard/night → playSwarm`. Keep it one narrate
long (the "turnips, doctrine, and the best bread" line already opens Beat 4).

---

## (e) Checkpoint plan — Digit8 / Digit9 / Digit0

`main.js` currently routes `Digit[1-7]` → `Chapter1.applyCheckpoint`. Suggest extending to
`Digit[89]|Digit0` → `Chapter2.applyCheckpoint(1|2|3)` (do not touch Chapter One's mapping).

| Key | Name | State set |
|---|---|---|
| `Digit8` | `Ch2: the grey road` | `roadIntro: true`, lamps unlit, both players at road start, Mochi following party, mood `forestB`. |
| `Digit9` | `Ch2: the Lanternstead at night (swarm ready)` | `roadLamps: 3`, `strangerSeen`, `arrived`, `wellDone`, `supperDone: false` → set `supperDone: true` and place both players in the night courtyard so `playSwarm` fires immediately. Tally at (900, 500). Mood `silence`. |
| `Digit0` | `Ch2: morning (the letter & the wall-map)` | All of the above + `swarmDone`, `hooded`; scene `lanternstead` state `morning`, lantern lit; `playLetter` fires (or is one interact away at the perch). Mood `resolve`. |

Follow the Chapter One `applyCheckpoint` pattern exactly: clear Dialog/Cutscene/Camera/FX,
conjure missing keyboard players, base-reset all flags, then layer the checkpoint's flags,
`Field.enter`, snap cam, toast `⚑ checkpoint — <name>`.

---

## (f) Music & mood notes

Existing moods only: `forestA`, `forestB`, `festivalA/B`, `hush`, `resolve`, `silence` (plus
stings: `hushSting`, `rumble`, `chime`, `pact`, `finale`).

| Where | Mood | Note |
|---|---|---|
| `road` (whole beat 1) | `forestB` | "old roots" — the uneasy forest candidate; right for grey wood. Do **not** use the `forest` alias (it resolves to `forestA`, Vesper's wonder-forest). |
| Stranger glimpse | `silence` → back to `forestB` | Same shape as the Hush: the quiet IS the sting. One `buzz` on the vanish, no music hit. |
| Lanternstead dusk + evening (beats 3–3½) | `resolve` (stand-in) | See below — the one genuinely warranted new mood. |
| Swarm onset | `silence` + `hushSting` | Then nothing under the moth storm — wind and wings. |
| Great-lantern roars | `resolve` (after `rumble` + `chime`) | The lantern lighting is the loudest moment of the chapter; let the music re-enter *after* the narrate, on Tally's laugh. |
| Morning + letter (beat 5) | `hush` | The Hush's own music under Rowan's letter is the point: home sounds like this now. Return to `resolve` after "We walk faster." |
| Wall-map + joining (beat 6) | `resolve` | |
| Departure narrates + end card | `silence` → `AudioSys.finale()` | Mirrors the Chapter One ending exactly. |

**New mood, genuinely warranted (suggest, do not implement): `waystation`** — a cozy-hearth
variant for beats 3/5/6 at the Lanternstead: `festivalA`'s warmth at roughly half tempo, music
box + soft low drone, one voice, long rests — "festival for a congregation of one." Currently
`resolve` (the pact/quest mood) is doing triple duty; a waystation mood would keep `resolve`
special. If cut, `resolve` works everywhere it's penciled in above.

---

## Implementation checklist (for the chapter2.js agent — not this document's job to do)

- `assets.js`: add `tally` to `SPEAKERS` (`Friar Tally`, `#d97b3f`), `LOOKS`, and
  `EXPRESSIONS` (`['happy','awed','earnest']`). Crow is an entity, not a speaker.
- `main.js`: Digit8/9/0 checkpoint routing; Chapter Two end-card text in `drawEnd`.
- Tally as follower: reuse Mochi's follow logic with a larger offset and `h: 118`.
- Art pipeline consumes §a (scenes ×3, states as listed) and §b (Tally busts + 3 expressions,
  sprite; crow sprite). Gallery-publish candidates per MEMORY.md.
