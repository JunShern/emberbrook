# CHAPTER TWO — "Dellhollow" — EXPANSION ADDENDUM (director-approved)

Screenplay addendum to `docs/chapter2-dellhollow-script.md`, written against the **shipped**
implementation (`public/js/chapter2.js`) — every splice point below cites the real function,
flag, and line as it exists in that file. The base screenplay and
`docs/chapter2-scene-deltas.md` remain in force; where the base doc and the shipped code
disagree, the shipped code is authoritative and is what this addendum splices into.

Three additions: **`vista`** (a cutscene-only valley-from-above backdrop, `landing`-class),
**`stairs`** (a new walkable street-level scene the party now enters town through), and
**`cottage`** (Maren and Odessa's house, interior) with **the supper beat** between the
shipped Lock Five beat and the nightfall/dock flow.

**Register law, restated and binding:** the lore budget is one deep system (the flame), and
Dellhollow spends none of it. Everything in this addendum is human themes — bread, laundry,
stairs, a locked drawer, a coat on a peg, a mother who serves instead of speaking. No
Heartlight, no Hush-anatomy, no ceremony around any lamp. Vesper's fog gets **one** internal
line at the supper table and not a syllable more (pre-Ch5 rule). Nobody says "afraid."
Dellhollow stays moth-free.

**Painting-drift contract:** all coordinates below are sketch values on the 1344×768 canvas,
Chapter One conventions. Painted reality overrode the base sketch once
(`docs/chapter2-scene-deltas.md`) and will again — a `chapter2-expansion-scene-deltas.md`
will carry the final values. POIs below are specced with generous interact radii and no
pixel-critical staging; the two coordinates that must NOT drift are called out inline (the
proven `dellhollow` west-entry spawn, and the reuse of the shipped west exit zone).

New chapter flags (added to `Chapter2.flags` and mirrored in `resetFlags()`):

```js
supperCalled: false, supperDone: false,          // the cottage flow
sorrelTalk: 0, creelTalk: 0, nibTalk: 0,         // stair-street flavor voices
// transient (not flags): this._supT — dwell timer for the supper trigger
```

`nightFallen` keeps its shipped meaning but moves its *setter*: it is now latched at the end
of `playSupper2` (the shipped `playNightfall` is absorbed — see §c and §g). No shipped flag
is renamed; every downstream check (`playDockNight`, `playWinches`, exits, `talkTo` night
branches) works unchanged.

Mechanics budget: **no new systems.** The vista is `Field.enter` + cam steps + `fadeTo`
(the `playLanding` scene-switch pattern, lines 1017–1028 of chapter2.js). The stairs are an
ordinary walkable scene with lantern-string lamps (no `id`, engine glow). The cottage is a
Ch1-`interior`-class scene. The supper is pure dialogue vocabulary.

---

## (a) Scene definitions sketch — for the art pipeline

### `vista` — the valley from above (cutscene-only backdrop)

The whole gorge in one breath, from high on the western rim at the forest's edge — the shot
that teaches the player the map before the map is ever argued about. Pearl-grey first-winter
morning light. **This is a painting the camera reads left to right, south to north**; compose
it as geography first and picturesque second — every element below is load-bearing for
Vesper's read-aloud and must be findable at a glance.

```js
vista: {
  // cutscene-only, landing-class but stricter: no mask, no exits, NO walkability —
  // players are never present in it (they stay in 'descent'; only the camera travels)
  states: { morning: 'assets/scenes/vista/main.png' }, state: 'morning',
  viewH: 700, charH: 120, speed: 190,
  tints: { morning: '#adb3a6' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],
  blocked: [], exits: [],
}
```

No `maskSrc`. Do **not** add `vista` to the bake list in `public/js/bake-core.js` (line 23).
The engine agent must verify `Field.register`/`Field.enter` tolerate a scene with no mask
(nothing ever queries walkability here — followers don't update during cutscenes, chapter2.js
line 271); if the loader insists, ship a trivial all-white mask and note it in the deltas doc.

Required contents (approximate positions — the pan path is specced to survive drift):
- **The river entering**, upper-left: silver water coming in high from the south at
  (120, 260), wide and calm — the upper pool with the **rafted queue** as a speck-cluster of
  hulls at (300, 330); one barge in the cluster reads faintly orange (Hobb's pumpkins,
  strictly an easter egg at this distance).
- **The five great locks**, all five visible for the first and only time in the chapter: a
  stair of dark timber treads stepping the silver down the gorge — Lock One (330, 300),
  Two (470, 350), Three (610, 405), Four (740, 460), Five swallowed under the town's shoulder
  at (860, 515), its chamber roofed in shadow (the player who has finished the chapter will
  know why; the painting doesn't say).
- **Dellhollow strung down both cliff walls**: near (south-west) wall houses stacked
  (380–900, 380–630), far wall (380–900, 170–360); the **stair-street** legible on the near
  wall as a pale zigzag seam through the stacked roofs, (700, 380) down to (820, 560) —
  this is the `stairs` scene seen from a mile out, and it should read as the same landmark.
- **THE COLOR RULE (director note, binding):** the gorge is grey-and-green — stone, moss,
  winter water — and **the town is a ribbon of color down both walls**. Dellhollow paints
  everything in leftover hull paint, so the stacked houses read at a mile as flecks of
  boat-red, gate-green, teal, ochre and whitewash against the grey cliff; bright laundry and
  a thread of old regatta bunting are just resolvable along the stair-street seam; the
  **moored boats of the rafted queue are colorful hulls**, not grey specks (Hobb's faint
  pumpkin-orange sits among genuinely painted boats). The contrast is the composition's
  thesis: a grey world, and the one loud, proud, lived-in thing in it. Color follows
  working-river-town logic (hulls, doors, shutters, washing, bunting) — never abstract
  decoration.
- **Woodsmoke**: standing columns off the roofs at (450, 300), (620, 260), (780, 330),
  leaning all one way (the gorge has one wind and everyone lives in it).
- **Lantern-strings as faint bead-lines**: strung straight across the air between the walls
  at (510, 340), (650, 380), (790, 420) — unlit points of glass catching the morning, with
  two or three **rope bridges** beneath them as single hairline catenaries.
- **The flume, a hairline**: a scratch of shadow running diagonally inside the right-hand
  cliff face from (880, 430) down to (1030, 570) — barely there; Vesper points at it once.
- **The tailwater and the river north**: the pool steaming faintly at (1060, 585), the
  landing an unremarkable grey nub beside it, and the river running off the right edge
  (1150–1344, 480–620) into layered haze. North is an exit, visibly.
- **Foreground anchor**: the rim itself across the bottom-left corner (0–260, 660–768) —
  wind-bent grass, one moth (the last one; the gorge below stays moth-free), the road
  starting down out of frame. Roots the POV so the pan reads as *standing somewhere*.
- Gulls, small, over the locks. No figure anywhere on the far rim — the Stranger has not
  happened yet and this painting must not accidentally stage him.

**Pan path** (the whole beat is three cam rests; the engine's cam tween carries the travel):

| Order | Camera rect (`cam`) | What it frames |
|---|---|---|
| start | `{ x: 300, y: 330, viewH: 520 }` | river in, upper pool, queue, Locks 1–2 |
| mid | `{ x: 672, y: 400, viewH: 520 }` | the town, both walls, strings and bridges |
| end | `{ x: 1080, y: 500, viewH: 560 }` | flume hairline, tailwater, the north haze |

Total beat length ~35–45s with dialogue; the two tweens should each take ~4s of that (slow —
this is a reading, not a whip).

### `stairs` — street-level Dellhollow (new walkable scene)

The missing shot: the town *around* you. A stair-street cut down the near cliff between
stacked houses — the pale zigzag seam from the vista painting, now at boot height. Doors open
onto other doors' roofs; laundry lines and two rope bridges cross overhead; a bread-window,
a public cistern, barrels going up a house wall on a hoist, kids, gulls. Bustling, lived-in,
**vertical**: the composition should make the player feel the town is above them and below
them at once. Day state warm in the cold-gorge palette; night state = tint + lantern-strings
lit (engine glow), same painting.

**THE COLOR RULE (director note, binding — this scene is its showcase):** Dellhollow is a
LIVELY, COLORFUL town, and the stair-street is where the player stands inside that fact.
The town paints everything in **bold boat-paint colors** — a lock-town uses hull paint on
its houses because hull paint is what it has, buys, and trusts. Required contents:
- **Painted shutters and doors** in hull colors — boat-red, gate-green, teal, ochre, a
  proud wrong purple — chipped and repainted in layers (paint history, not fresh trim);
  no two neighboring doors the same color.
- **Bright laundry** strung between the houses: every size, every color boat-paint comes
  in, snapping in the gorge wind — the town's ordinary flags.
- **Awnings** over the bread-window and the lower-landing doorway vendors: striped, patched,
  sun-faded on the up-gorge side.
- **Flower boxes** on sills and stair-rails — winter-hardy herbs and one or two stubborn
  late blooms in old bailing buckets and cut-down barrels (rhymes with the rafted queue's
  herbs-in-a-bailing-bucket interact).
- **Hanging market goods**: strings of peppers and gourds, racks of dried fish, coils of
  new rope, on hooks under the awnings and out of the drip-line.
- **Kids' chalk** on the stone: hop-grids, tally games, a gull with a rude expression
  (the same artist as the hoist wall), on the landings and the lower steps.
- **Bunting left up from some past regatta**, faded but never taken down, sagging between
  the upper houses — nobody remembers whose job it is and nobody wants it gone.
All of it grounded in working-river-town logic: the palette is the town's personality —
proud, busy, loud — never decoration for its own sake. The stone, the timber and the gorge
stay grey-green; the color is what the people nailed, painted, hung and grew onto it.
Night state: the color drops back under the tint and the lantern-strings carry the warmth.

Route change (the heart of this addendum's plumbing): the party now enters town
**descent → stairs (top) → stairs (bottom) → dellhollow (west quay entry)**. The shipped
descent↔dellhollow link via the west rope bridge is replaced; the painted rope bridge in the
`dellhollow` backdrop stays as non-exit dressing (new interact, §c inventory).

```js
stairs: {
  states: { day: 'assets/scenes/stairs/main.png',
            night: 'assets/scenes/stairs/main.png' }, state: 'day',
  maskSrc: 'assets/scenes/stairs/mask.png',
  viewH: 720, charH: 118, speed: 190,
  tints: { day: '#c9a988', night: '#66708c' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
  blocked: [],
  lamps: [   // lantern-strings crossing the stair — ordinary, no id, lit at night
    { x: 430, y: 200, lit: false }, { x: 700, y: 240, lit: false },
    { x: 540, y: 380, lit: false }, { x: 830, y: 300, lit: false },
    { x: 700, y: 540, lit: false }, { x: 480, y: 600, lit: false },
  ],
  exits: [
    // top — back up the switchbacks (inherits the shipped night denial + Maren's line,
    // which MOVES here from the shipped dellhollow west exit, chapter2.js lines 70–72)
    { zone: { x: 560, y: 0, w: 240, h: 70 }, to: 'descent', spawn: [640, 640, 'up'],
      enabled: () => !Chapter2.flags.nightFallen,
      deniedLine: ['maren', 'Up the switchbacks at THIS hour? Nothing up there but weather. Everything worth anything is down.'] },
    // bottom — the quay gate. Spawn (210, 110) is the PROVEN shipped west-entry spawn
    // (chapter2.js line 49, delta-doc verified walkable) — do not drift this value.
    { zone: { x: 540, y: 700, w: 260, h: 68 }, to: 'dellhollow', spawn: [210, 110, 'down'] },
    // the keepers' cottage door — mid-scene door exit (Ch1 lane→interior precedent)
    { zone: { x: 845, y: 330, w: 70, h: 60 }, to: 'cottage', spawn: [300, 560, 'right'],
      enabled: () => Chapter2.flags.supperCalled && !Chapter2.flags.supperDone,
      deniedLine: ['vesper', 'A door with lock-gates carved over it. Keepers live here. We haven’t been asked.'] },
  ],
}
```

After `supperDone`, the door's `deniedLine` should swap to the softer close (engine agent:
a ternary in the deniedLine, or a second denied variant — either is fine):
`['system', '(Pulled to. The lamp inside is banked low. Let the house keep its keeper tonight.)']`

Points of interest (must be in the painting):
- **Stair path**: top landing under an arch at (672, 110); flights zigzag — down-left to a
  landing at (420, 300), down-right to a landing at (760, 470), down to the quay gate at
  (672, 690). Landings are the scene's social floors; the mask should give each one room.
- **The keepers' cottage door** at (880, 350), off the middle landing, interact (870, 405),
  radius ~75: a low door under a **lintel carved in miniature — two lock-gates, shut,
  holding back a carved curl of water**. The plainest door on a street of painted ones, and
  the only one with a job description over it. Height-tallies are just visible on the inner
  frame when the door stands open (the full prop is inside — §a `cottage`). This is the same
  landmark the vista painting shows as the seam's midpoint; keep the silhouettes consistent.
- **Sorrel's bread-window** at (350, 340): a hinged shutter counter in a house wall, warm
  light, loaf-iron. (NPC station — see §b; no separate interact, Sorrel is the interact.)
- **Public cistern** at (500, 470), interact (520, 505), radius ~70: stone basin fed off a
  bypass race, tin cup on a chain worn bright.
- **Laundry lines** overhead, (300–1000, 150–260), "look up" interact from the upper landing
  at (620, 320), radius ~70.
- **Gull rail** at (900, 520), interact (880, 560), radius ~65: gulls in seniority order.
- **Barrel-hoist** at (1010, 360), interact (990, 420), radius ~70: freight going up the
  outside of a house; chalked load-tallies and a rude gull drawing on the wall.
- **Kids** painted mid-flight on the lower stairs (they also exist as Nib, §b); doorway
  vendors as painted dressing on the lower landing (one interactive voice is enough).
- Night state: strings lit, windows warm, the bread-window shuttered dark.

### `cottage` — Maren and Odessa's house (new interior)

One room and a curtained sleeping nook, in the Ch1 `interior` style/palette family
(chapter1.js lines 56–64: `viewH: 725, charH: 215`, warm tint) — but a river-keeper's house,
not a lamplighter's: the warmth here is work-warmth. Timber walls, a hearth with a stew-hook,
one good table, the river audible under the floorboards. Everything oiled, nothing for show.

**Warmth/color spec (director note):** the cottage carries the town's color rule indoors, at
house volume. The same hull paint shows up in small, used ways: **bowls and a jug glazed in
boat-colors** on the dresser (mismatched — bought one at a time, years apart); a **rag rug of
bright rope-ends** by the hearth (a splicer's off-cuts — Creel's trade reaching indoors); the
**bread-tin painted gate-green**; the window-frame teal outside, bare timber inside; a string
of dried peppers by the hearth doing double duty as pantry and decoration. Against this, the
storytelling props stay deliberately unpainted — the doorframe tallies, the oilskin coat, the
dresser drawer, the new stool are **bare, oiled wood**: the color in this house is for living
things and daily things, and the kept things keep their own finish. (Exterior contrast holds:
on a street of painted doors, the keepers' door is the plainest — inside is where its warmth
lives.)

```js
cottage: {
  states: { dusk: 'assets/scenes/cottage/main.png',
            night: 'assets/scenes/cottage/main.png' }, state: 'dusk',
  maskSrc: 'assets/scenes/cottage/mask.png',
  viewH: 725, charH: 205, speed: 280,
  tints: { dusk: '#e8b489', night: '#8d8298' },
  walk: [[0, 0], [1344, 0], [1344, 768], [0, 768]],   // fallback; mask governs
  blocked: [],
  exits: [{ zone: { x: 180, y: 560, w: 110, h: 160 }, to: 'stairs', spawn: [880, 430, 'down'] }],
}
```

Required storytelling props (each painted + interactable; texts in §c inventory):
- **The height-tally doorframe** — the door at (250, 470); interact (270, 560), radius ~75.
  Small dated marks climbing the inner frame: MAREN and a height, MAREN and a height, rising
  like water — **stopping a hand below the lintel, years ago.** Nothing above the last mark.
  Spec note (never stated in dialogue): she stopped being measured and started measuring —
  her records moved to her forearm and the beam. The doorframe is the third ledger in this
  family, and the only one that stopped.
- **The father's oilskin coat** on the peg nearest the door at (340, 350); interact
  (340, 445), radius ~70. Square on its shoulders, oiled recent — kept-ready the way the
  boat is tarred. One empty peg below it (Lake will use it in the beat; paint the empty peg).
- **The locked chart drawer** — a small drawer in the dresser under the window, right wall,
  drawer face at (1050, 430); interact (1035, 520), radius ~75. Every latch in the house is
  worn bright with use; this one keyhole is worn bright with something else. **Glimpsed,
  never opened.** Beat 8 pays it off (§c, the one-line `playLanding` insert). Do not paint a
  key anywhere in the scene.
- **Eel-spears and winch-parts** racked on the back wall at (900, 300); interact (900, 400),
  radius ~75: spears wicked and elderly beside pinions, a gear-puller, chain-links — the
  tool-wall of a house where the river is the family trade.
- **The table and the three seats**, center at (740, 520): **two chairs, arm-ends worn to
  shine by four generations of forearms — and a third seat: a stool, the newest wood in the
  room by eighty years, standing where a chair would.** Interact (740, 590), radius ~80.
  Spec note (never stated in dialogue): the third chair was the father's, and it is gone —
  where, the house doesn't say — and the stool was made about eleven years ago so that the
  table could seat three without pretending nothing was missing. Paint the stool's wood
  visibly younger; that is the entire storytelling budget for it. (It also quietly seeds
  Maren's Ch3 line "I ALWAYS get the wobbly stool" — at home, the stool is hers.)
- **Hearth** at (520, 380) with the stew-pot on its hook; interact (540, 460), radius ~75 —
  this interact is also the supper trigger (§c).
- Window over the dresser showing the gorge going dark; night state = same painting, tint.

---

## (b) Additions to the roster — for the character pipeline

Three stair-street flavor NPCs. All **sprite-first, nameplate-only** — reuse-tinted existing
villager sheets in the Hobb/Pell pattern (chapter2.js lines 118–121), speaker entries with
name + color, **no bust art** (engine agent: verify `Dialog` renders cleanly for a speaker
with no bust — Hobb and Pell shipped with neutral busts, these three ship with none).
Human register only; none of them gates anything; the objective still counts Hobb + Pell.

### SORREL — the bread-window (nameplate-only)
Forearms, flour, a permanently raised voice for a permanently vertical street; sells through
a hinged shutter and has opinions about everyone's cat. Plant-name in the Poppy tradition.
**Speaker entry**: `sorrel: { name: 'Sorrel', color: '#c98a5a' }`.
**Sprite**: reuse the `poppy` sheet, tint `#d9b08a`, h ≈ 120, stationed at the bread-window
(360, 355).

### OLD CREEL — the rope-splicer (nameplate-only)
Ancient, content, mid-splice on the same step he has occupied since before opinions. Keeper
of the town's other infrastructure: everything that hangs.
**Speaker entry**: `creel: { name: 'Old Creel', color: '#8a8a72' }`.
**Sprite**: reuse a villager sheet (engine agent's pick; not `finn` — Hobb's tint already
owns it on this quay), tint `#b0a98f`, h ≈ 112, seated pose acceptable if the sheet has one;
stationed (820, 435).

### NIB — the gull kid (nameplate-only)
Eight-ish, loud, employed (self-appointed) as the stair-street's gull officer. The town's
future, currently feeding it to seagulls.
**Speaker entry**: `nib: { name: 'Nib', color: '#d9a94a' }`.
**Sprite**: smallest villager sheet available at h ≈ 84, tint `#e0c07a`, stationed (560, 565),
gulls painted around.

All three are **hidden at night** (the supper's exit run hides them; `resetFlags()` and the
checkpoint night block restore/hide accordingly). No expressions, no arcs, no lore.

No other new characters. Odessa's `warm` expression budget is **unchanged: once, Beat 8** —
the supper beat below is written entirely on `odessa:grave` and stage business, on purpose;
guard this in review.

---

## (c) Beat-by-beat script — the three additions

Speaker keys as shipped, plus minor `sorrel / creel / nib`.

### BEAT 1v — the valley from above (`playValley`) — spliced inside `playDescent`

**Function name ruling:** the shipped parapet beat already owns `playVista`
(chapter2.js line 589), so the new high shot is **`playValley`**, and the new *scene* key is
`vista` (free — no shipped scene uses it). Do not rename the shipped function.

**Splice point (exact):** inside `playDescent` (chapter2.js lines 501–522), immediately after
`{ say: ['vesper', 'Well. That’s the other thing.'] }` (line 518) and **before**
`{ camRelease: true }` (line 519). The vista *is* the other thing — Lake asks "Down where?
All I can see is gorge," Vesper answers "Well. That's the other thing," and the cut lands as
the answer. This is the very start of Beat 1, well before the chart halt trigger
(`playChart` gates on the slab zone, update() lines 228–230), satisfying the approved order.

The whole insert is steps within the running `playDescent` cutscene (no new trigger, no new
flag — the beat cannot be missed or double-fired because `descentIntro` already latches it):

```js
  // …after ['vesper', 'Well. That’s the other thing.']:
  { fadeTo: 1 },
  { wait: 0.8 },
  { run: () => { Field.enter('vista'); Field.cam.x = 300; Field.cam.y = 330; } },
  { cam: { x: 300, y: 330, viewH: 520 } },
  { fadeTo: 0 },
  { wait: 1.2 },
  { narrate: 'They stepped out of the trees onto the rim of the world, and the other thing was this:' },
  { narrate: 'A gorge you could lose a cathedral district in — and it was FULL. The river came in high and silver from the south, stepped down five great timber stairs, and a town went with it: houses stacked down both cliffs and painted every colour a boat can be, one ribbon of loud, lived-in colour down all that grey stone, woodsmoke leaning all one way, strings of unlit lanterns crossing the air like beads on a wire.' },
  { mood: 'dellhollow' },                        // the town theme, early and far away (§f)
  { cam: { x: 672, y: 400, viewH: 520 } },
  { say: ['vesper', 'Not on the sheet. A whole town, Lake. Not on the sheet.'] },
  { say: ['vesper', 'Read it off the water — rivers abbreviate, they don’t lie. In high on the south. Five locks — that’s a STAIR, for boats. Town on both walls, where the work is. And out the far end, low and easy — north, into the haze. That hairline in the right-hand cliff will be a spillway. The rest is people.'] },
  { say: ['lake', 'The little lights, strung straight across the air. Bridges?'] },
  { say: ['vesper', 'Lantern-strings, on rope bridges. A town that ties its own two halves together every morning, and lights the knot at night. …I like them already.'] },
  { cam: { x: 1080, y: 500, viewH: 560 } },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi regards the whole descending wonder of it with the enthusiasm of a cat regarding a very large wet staircase. There had better be fish.)'] },
  { narrate: 'Smoke went up. Gulls came down. And out past the last lock the river went on north without waiting for anyone, the way rivers do.' },
  { fadeTo: 1 },
  { wait: 0.8 },
  { run: () => { Field.enter('descent'); const v = window.players.find(p => p && p.role === 'vesper'); if (v) { Field.cam.x = v.x; Field.cam.y = v.y; } } },
  { fadeTo: 0 },
  { mood: 'forestB' },                           // back on the grey road
  // …then the shipped { camRelease: true } and mochi-follow restore proceed as-is
```

(6 spoken lines + 3 narrates + 1 system — inside the 3–6 dialogue budget; Vesper reads the
geography, Lake asks the first-timer's question, Mochi is indifferent.)

**Consequences downstream (required line surgery, part of this beat's seam):**

1. `playVista` (the shipped parapet beat, lines 589–601) is now the *second* look — its job
   shifts from discovery to proximity and NOISE (which its best lines already are). Three
   edits, exact:
   - Keep narrate 1 (`'The last switchback turned them…like a lit window.'`) unchanged.
   - **Replace** narrate 2 (`'A town. Stacked down both cliffs…selling something.'`) with:
     `'Closer now, the town stopped being geography and started being NOISE. Hammers. Gulls. Somebody laughing. Somebody selling something. And under everything, patient as a held breath, the river working.'`
   - **Delete** `{ say: ['vesper', 'Not on the sheet. A whole town, Lake. Not on the sheet.'] }`
     (line 595 — the line moved up to `playValley`, where the discovery now lives).
   - Keep `'Listen to it.'`, `'…I’d forgotten what a Tuesday sounds like.'`, and Lake's
     internal line unchanged.
2. `playChart` needs **no** edits: seeing the valley first makes "my best chart of this whole
   country says: heath" land harder, and Vesper's halt lines are forensics ("who inked the
   guess"), not discovery. Verified against lines 535–541: nothing contradicts a prior look.

### BEAT 2 (relocated) — arrival on the stair-street (`playArrival`, retargeted to `stairs`)

**Trigger change (exact):** update() lines 241–244 — the gate
`players.some(p => p && p.scene === 'dellhollow')` becomes
`players.some(p => p && p.scene === 'stairs')`. Everything else (both players, `!F.arrived`,
`F.strangerSeen`, `!busy`) unchanged; `F.arrived` is still latched at cutscene start (line
606) so all downstream gating — `spawnFor`, the Beat 3 quay-count, the `objective()` ladder —
works untouched. There is no separate dellhollow-entry beat; Vesper's closing line aims the
players down the stairs, and the objective string carries them to the quay.

The relocated beat, expanded to breathe (shipped lines kept verbatim where they survive the
move; edits marked):

```js
Cutscene.play([
  { mood: 'dellhollow' },
  { cam: { x: 672, y: 300, viewH: 620 } },
  { narrate: 'Dellhollow, of the five locks. It smelled of tar, bread, wet rope and roasting chestnuts, and it sounded like everything Emberbrook had stopped being.' },        // verbatim
  { narrate: 'The road became a street and the street became a stair, and the town happened to them from every side at once: houses standing on each other’s shoulders, every door and shutter painted in somebody’s leftover hull-colours, washing overhead like signal-flags, bunting from some long-finished regatta that nobody had ever taken down — the whole loud, painted, vertical parish descending, arguing, to the water.' },     // NEW
  { narrate: 'Nobody stared at them. A woman in a bread-window quoted them a price on principle. Two children ran down between the party without apology or slowing, taking the stairs three at a time. It was wonderful.' },   // EDITED (eel-wife → bread-window; the eel-wife keeps her quay)
  { say: ['vesper:happy', 'A stair with SHOPS on it. A bread-window. A public cistern with a polished cup. Lake — people. Uninterrupted people, doing ordinary things, at VOLUME, on top of each other, on a cliff.'] },        // EDITED (market-row list → stair-street list; cadence kept)
  { say: ['lake', '(No pedestal. No keeping-flame. I’ve read every doorway on the way down — just oil lamps on strings, lit by whoever’s nearest, meaning nothing.)'] },          // EDITED ('walked the whole quay with my eyes twice' → the stair)
  { say: ['lake', '(And it holds. It’s loud, and it’s kind, and it holds together with no flame at all. …Grandmother, what else didn’t you tell me? Or didn’t know?)'] },        // verbatim
  { say: ['system', '(A rope bridge creaks overhead: a woman crosses it with a basket of eels on her hip, treating the air between the cliffs as a footpath — because here, it is one.)'] },   // NEW
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi has caught wind of the eel-stall. It is somewhere below. Everything worth anything, the cat has concluded, is down — and the party’s marching order has quietly changed.)'] },   // EDITED; quietly rhymes with Maren’s denied-exit line
  { say: ['vesper', 'Quay first. Towns are like rivers — you read them from the people at the edges. Then whoever’s in charge.'] },   // verbatim — and now it literally points down the stairs
  { camRelease: true },
]);
```

(11 lines/narrates — the shipped 9, rehoused and given room.)

**Stair-street voices** — `talkTo` branches, day only (all three hidden at night):

SORREL (first talk — `sorrelTalk++`):
```
sorrel  'Mind the drip-line, loves — wash overhead, bread underhand. Half-loaf’s a penny,
         whole loaf’s a penny and a look at your cat.'
mochi   'Mrrp.'
sorrel  'Paid in full. Here’s the heel for him, and don’t tell the gulls. Nineteen days of
         stuck boats is nineteen days of boat-folk buying bread — worst thing ever to happen
         to this town, and my ovens haven’t cooled since. Don’t tell the harbormistress
         which way I’m praying.'
```
SORREL (repeat): `'Half-loaf’s still a penny. The cat’s credit is good.'`

OLD CREEL (first talk — `creelTalk++`):
```
creel   'Four hundred years of stairs, stranger. The town’s knees give out before the timber
         does. I’ve spliced rope on this step since I was the boy with the gulls — and
         there’s always a boy with the gulls.'
creel   'The bridges? Sound as sermons. I splice what they hang from. Rope tells you before
         it goes — so do stairs, so do most things, if you’re the sort that listens.'
```
OLD CREEL (repeat): `'Mind your feet going down. Coming up, mind everything else.'`

NIB (first talk — `nibTalk++`):
```
nib     'That one’s Bailiff, that one’s Soup, and the big one’s called the Harbormistress —
         don’t TELL the harbormistress.'
lake    'Your secret’s kept.'
nib     'She knows anyway. She knows everything. Are you the flame people? You’re littler
         than the quay said.'
```
NIB (repeat): `'Soup! SOUP! …He knows his name. He just doesn’t respect it.'`

**Stair-street interacts** (`nearestThing` → `interact`, new kinds):
- `cistern`: 'The public cistern, fed off a bypass race somewhere above. A tin cup on a chain, worn bright. Four centuries of the same thirst, and the same answer.'
- `laundry`: 'Laundry strung wall to wall, three stories up — shirts of every size, in every colour boat-paint comes in, snapping in the gorge wind. The town flies its ordinary flags, daily, and nobody salutes.'
- `gullrail`: 'Gulls hold the stair-rail in strict order of seniority, everyone sliding down one place whenever a bigger gull lands at the top. The town underneath runs on roughly the same system, at roughly the same volume.'
- `hoist`: 'A barrel-hoist rigged from a top-floor beam: freight goes up the outside of the house, because the inside is stairs, and the stairs are already full of everyone. Chalked on the wall: load-tallies, initials, and a rude but accurate drawing of a gull.'
- `cottagedoor` (before `supperCalled`): 'A low door under a lintel carved in miniature: two lock-gates, shut fast, holding back a carved curl of water. On a street of painted doors it is the plainest one — and the only one with a job description over it.'
- `cottagedoor` (after `supperDone`): 'Pulled to. The lamp inside is banked low. Let the house keep its keeper tonight.'

And one in **`dellhollow`** — the retired exit:
- `ropebridge`, bridgehead interact at (70, 150) by the shipped west zone: 'The west rope bridge, slack-roped and patient, running out over the ravine toward the old rim. It goes to the switchback road eventually, for those with the knees and the nerve. The stair-street has handrails, and better gossip.'

### BEAT 5¼ — supper at the keepers' cottage (`playSupperCall` → `playSupper2`)

Slots between the shipped Lock Five beat and the nightfall/dock flow. The shipped
`playNightfall` (chapter2.js lines 794–813) is **absorbed**: its trigger becomes the
supper-call, and its body (night states, lamps, desat, hides, glue narrate) moves into
`playSupper2`'s exit. `nightFallen` is now latched at the supper's end, which means the
shipped `playDockNight` trigger (lines 260–264) and everything after it run **unchanged**.

**`playSupperCall`** — dusk glue, ~30s. **Trigger (exact):** replaces the `playNightfall`
gate at update() lines 256–258 — `both && F.planMade && !F.supperCalled && !busy &&
players.some(p => p && p.scene === 'dellhollow')`. Latch `F.supperCalled` at start.

```js
Cutscene.play([
  { run: () => { /* Maren up from the stairhead to meet them */ const m = this.npcs.maren;
      m.hidden = false; m.scene = 'dellhollow'; m.x = 1150; m.y = 600; m.dir = 'left'; } },
  { cam: { x: 900, y: 540, viewH: 520 } },
  { move: { ent: maren, x: 760, y: 560, speed: 170 } },
  { narrate: 'They came up out of the lock-dark into the last of the light: dusk sliding down both cliffs, and the first lantern going up the stair-street like the first bead on a wire.' },
  { say: ['maren:happy', 'There you are. Right — orders, and not mine, so don’t argue with ME: Ma says the flame people eat at ours tonight.'] },
  { say: ['vesper', 'She says, or she asks?'] },
  { say: ['maren', 'She SAYS. Asking is for the guild. It’s the low door on the stair-street — the one with the gates carved over. I’ll go ahead; somebody has to warn the stew.'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['maren:happy', 'Yes, the cat’s invited. The cat was invited FIRST, if you want the order of it.'] },
  { run: () => {                                  // the house fills: Odessa home cooking, Maren ahead
      const { maren, odessa } = this.npcs;
      odessa.scene = 'cottage'; odessa.x = 560; odessa.y = 420; odessa.dir = 'right';
      maren.scene = 'cottage'; maren.x = 820; maren.y = 540; maren.dir = 'left';
    } },
  { camRelease: true },
]);
```

(5 spoken lines + 1 narrate.) Story marker moves to the cottage door (§d). Odessa leaves the
quay for the evening — her `talkTo` is unreachable in town, and in the cottage pre-supper she
gets one holding line: `['odessa:grave', 'Sit or stir, guest. Standing in the middle of a kitchen is for weathervanes.']`
Maren pre-supper in the cottage: `['maren:happy', 'Door’s open. Lintel’s low — for tall people and opinions.']`

**Free-roam breath (deliberate):** the supper does not fire on entry. Both players in
`cottage` accrue `this._supT` (only while `!busy`, dock-scene pattern); at **8s** the beat
auto-plays — or immediately if either player interacts with the **hearth** (`kind: 'hearthpot'`).
The breath exists so the props (§a) can be found while the house is still awake; after supper
the cottage is closed for the chapter, so this window is the only one.

**`playSupper2`** — the supper, ~35 steps. Latch `F.supperDone` at start. Tone contract:
the Tally supper's warmth (chapter3.js `playSupper`, line 610) with inverted dynamics —
Tally hosts by talking; **Odessa hosts by serving.** Maren talks too much. The friction and
the love arrive in the same gestures. Vesper gets exactly one internal line. Lake is good at
hearths, and it shows instead of telling.

```js
Cutscene.play([
  { fadeTo: 1 },
  { wait: 0.8 },
  { run: () => {                                  // everyone to the table
      // vesper → chair (700, 505, 'right'); lake → chair (790, 505, 'left');
      // maren → THE STOOL (745, 470, 'down'); odessa at the pot (560, 420, 'right');
      // mochi → the doorstep (300, 600, 'up'); Field.enter('cottage'); cam to table
    } },
  { cam: { x: 740, y: 480, viewH: 580 } },
  { mood: 'dellhollowNight' },                    // the town theme at house scale (§f)
  { fadeTo: 0 },
  { wait: 0.6 },
  { narrate: 'The keepers’ cottage held its heat the way the gorge held the town: close, and hard-won. Eel stew on the hook, bread in the window-iron, and the river talking quietly under the floorboards, off shift but never off duty.' },
  { say: ['odessa:grave', 'Wash. Basin’s by the door. The cat eats on the step, and knows it.'] },
  { say: ['mochi', 'Mrrp.'] },
  { say: ['system', '(Mochi eats on the step. On the WARM half of the step. The negotiation takes four seconds, and Odessa loses exactly half of it, and does not appear to mind the arithmetic.)'] },
  { say: ['system', '(She serves the way she runs the locks: in order, without hurry, every bowl filled before her own is even down. She has not sat yet. It is not clear the chair expects her to.)'] },
  { say: ['maren:happy', 'So — this is the house. Four generations. That beam’s off a barge that sank in the ’02 flood, Da reclaimed it — well, GRAND-da — and that’s the good table. We’re eating at the good table. Ma got out the good table.'] },
  { say: ['odessa:grave', 'The table we eat at.'] },
  { say: ['maren', 'The good one.'] },
  { cam: { x: 420, y: 480, viewH: 460 } },
  { say: ['system', '(By the door, climbing the frame: small dated marks. MAREN, and a height. MAREN, and a height. They rise like water coming up a lock wall — and stop, a hand below the lintel, years ago.)'] },
  { say: ['lake', 'The doorframe. Emberbrook does the same — Grandmother kept mine on the pantry door.'] },
  { say: ['maren', 'Ma stopped measuring me at fourteen.'] },
  { say: ['odessa:grave', 'You stopped standing still.'] },
  { mood: 'silence' },                            // music out for the middle of the table
  { wait: 0.8 },
  { say: ['maren', 'You never asked me to.'] },
  { say: ['system', '(Odessa says nothing. Odessa puts a second helping into Maren’s bowl before Maren has noticed the first is gone. That, apparently, is the sentence.)'] },
  { cam: { x: 740, y: 480, viewH: 580 } },
  { say: ['vesper', 'Harbormistress — your house has one lock in it. Forgive me; I survey rooms, it’s a disease. Every latch here is worn bright with use. One keyhole is worn bright with something else.'] },
  { say: ['odessa:grave', 'And it will stay one.'] },
  { say: ['maren', 'It’s the—'] },
  { say: ['odessa', 'Maren.'] },
  { say: ['maren', '…It’s nothing. Dresser drawer. Sticks.'] },
  { say: ['system', '(It is a small drawer, in the dresser, under the window. The wood around the keyhole is clean. The keyhole does not stick. Nobody at this table believes the drawer is nothing, including, just possibly, the drawer.)'] },
  { say: ['vesper:thinking', '(A mother, a daughter, one table, and one locked thing in the middle of it, politely orbited. So this is what other people’s kitchens are for. …Filed. And for once, the file can stay shut.)'] },
  { wait: 0.8 },
  { mood: 'dellhollowNight' },                    // music back with the kitchen rhythm
  { say: ['system', '(Lake, without asking, has found the cloth, the kettle-hook, and the rhythm of somebody else’s kitchen. He and Odessa work around each other like two halves of one watch.)'] },
  { say: ['odessa:grave', 'You’ve kept house.'] },
  { say: ['lake', 'Kept a lamp. It’s the same wrist.'] },
  { say: ['odessa', 'Mm.'] },
  { say: ['system', '(From the harbormistress, that is a commendation with a seal on it.)'] },
  { say: ['system', '(Going to hang the cloth, Lake finds one peg by the door already taken: a man’s oilskin, oiled this winter, hung square. He hangs the cloth on the peg below it, and asks nothing — and Odessa watches him not ask, and fills his bowl again.)'] },
  { say: ['maren:happy', 'Anyway — tomorrow we thought we’d see the town. More of the town. There’s… plenty of town.'] },
  { say: ['lake', '(She is the worst liar on this river. Her mother is letting her be.)'] },
  { say: ['odessa:grave', 'Mind the tide, then. Seeing your town.'] },
  { wait: 1.0 },
  { narrate: 'The stew went, and the bread went after it, and the lamp burned down the way house-lamps do — unwatched, and trusted.' },
  { say: ['odessa:grave', 'Night’s down. Take the stair slow, strangers. Mind the—'] },
  { say: ['maren', 'Forty-first step.'] },
  { mood: 'silence' },
  { wait: 1.2 },
  { say: ['maren', '(quiet) …You know the step joke.'] },
  { say: ['odessa:grave', 'I taught him the step joke.'] },
  { fadeTo: 1 },
  { wait: 1.2 },
  { run: () => {                                  // NIGHTFALL — the absorbed playNightfall body
      Field.setSceneState('dellhollow', 'night');
      Field.setSceneState('stairs', 'night');
      Field.setSceneState('lockfive', 'night');
      FX.desatTarget = 0.35;
      Field.scenes.dellhollow.lamps.forEach(l => { l.lit = true; });
      Field.scenes.stairs.lamps.forEach(l => { l.lit = true; });
      const N = this.npcs;
      N.maren.hidden = true;                      // gone ahead — to rig chains
      N.hobb.hidden = true;                       // the town turns in; Pell keeps the night
      N.sorrel.hidden = true; N.creel.hidden = true; N.nib.hidden = true;
      // odessa stays in the cottage (scene 'cottage'; door now closed to re-entry)
      // players out onto the stairs by the door: vesper (830, 420, 'down'), lake (895, 435, 'down')
      // mochi.follow = 'party' restored; Field.enter('stairs'); cam to players
      this.flags.nightFallen = true;              // ← the shipped flag, latched HERE now
    } },
  { mood: 'dellhollowNight' },
  { fadeTo: 0 },
  { narrate: 'They stepped out into a night already down, the lantern-strings burning above the stair-street like beads of held breath. Maren had gone past them somewhere between the bread and the door, two steps at a time, already rigging chains in her head.' },
]);
```

(~24 spoken lines + 4 narrates + 8 system = the 25–35 budget with the system lines carrying
the served-not-said register.) The forty-first step is the deep-stairs joke from
`playLockFive` line 740 — the ending reveals it was the father's joke first, which is the
beat's whole thesis said in one exchange, and then the door closes on it.

**Cottage interacts** (pre-supper window; `nearestThing`/`interact` new kinds):
- `tallies`: 'Small dated marks climb the doorframe: MAREN, and a height; MAREN, and a height — rising like a spring flood, then stopping a hand below the lintel, years ago. Above the last mark, nothing. Her records moved to her arm, and to the beam, and nobody in this house has ever said so out loud.'
- `coatpeg`: 'A man’s oilskin coat on the peg nearest the door, square on its shoulders, oiled this winter the way the boat is tarred. Eleven years of weather have come and gone outside. The coat is ready anyway.'
- `drawer`: 'A small drawer in the dresser, under the window. Every latch in this house is worn bright with use. This one keyhole is worn bright with something else. Locked — not stuck. Locked.'
- `toolwall`: 'Eel-spears, wicked and elderly, racked beside winch-pinions, a gear-puller, and a coil of chain-links: the wall of a house where the river is the family trade. Everything is oiled. Nothing is for show.'
- `tableseats`: 'Two chairs, arm-ends worn to shine by four generations of forearms — and a third seat: a stool, the newest wood in the room by eighty years, standing exactly where a chair would. Nobody says why. The table has learned not to ask.'
- `hearthpot` (also the supper trigger): 'The stew-pot on its hook, and a fire kept the way locks are kept: banked exact, nothing wasted, nothing out.'

**The Beat 8 payoff (required, one line):** in `playLanding` (chapter2.js lines 1010–1073),
immediately after the oilskin-tube system line
(`'(From inside her coat she takes an oilskin tube, worn glossy at the cap…)'`, line 1050)
and before Odessa's `'His chart…'` (line 1051), insert:

```js
{ say: ['vesper:thinking', '(The drawer. The one bright keyhole in a worn house. She went home in the dark, then, before the portage stair — and stood in front of eleven years, and turned the key.)'] },
```

Nothing else in Beat 8 changes; the glimpsed-never-opened drawer resolves in the player's
head, which is where it lived all along.

---

## (d) Objectives, prompts, markers — deltas only

| Where | `objective()` change |
|---|---|
| Beat 1 (with `playValley`) | No change — the vista is inside the intro cutscene; the shipped ladder (lines 314–318) stands. |
| Beat 2 on `stairs` | No string change — `'Down — Dellhollow is not on the map'` carries them into the stairs; once `arrived`, the shipped `'Dellhollow — meet the quay (n/2)'` now also *directs* (the quay is down the stairs). |
| After `planMade`, before `supperCalled` | `'Evening — back up to the quay'` (shipped line 325's slot, unchanged text). |
| `supperCalled && !nightFallen` | **NEW:** `'Supper at the keepers’ cottage — the low door on the stair-street'`. Code shape: the shipped `if (!F.nightFallen) return 'Evening — back up to the quay';` becomes `if (!F.nightFallen) return F.supperCalled ? 'Supper at the keepers’ cottage — the low door on the stair-street' : 'Evening — back up to the quay';` |
| After supper | Shipped strings unchanged (`'Night on the quay'`, `'Meet Maren at the deep stairs — quietly'`). |

Prompts: no new verbs — `'A — talk to <name>'` for Sorrel/Creel/Nib (via `SPEAKERS`),
`'A — look'` for all new interacts including the hearth (which fires the supper).

`storyMarker()` (chapter2.js lines 333–345) — currently early-returns unless
`Field.currentKey === 'dellhollow'`; restructure to per-scene:
- `dellhollow`: shipped markers unchanged; **add** — when `supperCalled && !supperDone`, mark
  the west stairs gate at `{ x: 30, y: 125 }` (the retargeted exit, guiding them up).
- `stairs` (new): when `supperCalled && !supperDone`, mark the cottage door `{ x: 880, y: 300 }`.
- `lockfive`, `cottage`: none.

---

## (e) Checkpoint plan — extend Chapter Two to SIX entries

The supper earns a checkpoint: it is the chapter's second quiet center, it sits behind two
cutscenes and a scene change (expensive to reach for iteration), and the mother-daughter
table is precisely the content that will be revised most. Ruling: **yes — six.**

Revised `CHECKPOINT_NAMES` (chapter2.js line 1076) and `applyCheckpoint` states:

| # | Name | State set |
|---|---|---|
| 1 | `Ch2: the descent` | Unchanged from shipped n=1. (`playValley` now plays inside the intro.) |
| 2 | `Ch2: Dellhollow — the stair-street` | Shipped n=2 flags (`descentIntro, chartDone, strangerSeen`, `_vistaSeen`); **placement moves** to the stairs top: players (672, 120)/(714, 138) 'down', mochi (650, 160); `playArrival` fires on `stairs`. Mood `dellhollow`. |
| 3 | `Ch2: Lock Five — the Tenant` | Unchanged from shipped n=3 (the shipped `n >= 3` flag block stands as-is). |
| 4 | **NEW** `Ch2: supper at the keepers’ cottage` | + `lockSeen, planMade, supperCalled`; Odessa in `cottage` at the pot (560, 420), Maren in `cottage` (820, 540); players in `cottage` (620, 590)/(700, 600); scene states still day/dusk; `playSupper2` fires via the 8s dwell (props explorable first — that is the point of this checkpoint). Mood `dellhollowNight`. |
| 5 | `Ch2: night — the flume winches` | Shipped n=4, plus: `supperCalled, supperDone` set; night block now also sets `Field.setSceneState('stairs','night')` + stairs lamps lit + `sorrel/creel/nib` hidden; Odessa's hide is per shipped (she re-enters in `playWinches`). |
| 6 | `Ch2: the landing — Maren joins` | Shipped n=5, renumbered; adds the same supper flags to its base. |

`main.js` needs **no code change** for the menu — `showCheckpointMenu`'s `add(Chapter2, 'Ch2')`
(line 302) iterates `CHECKPOINT_NAMES`. Behavior note for the team: the digit shortcuts
(main.js lines 412–416, "first nine entries of the C menu") shift by one for everything after
Ch2 entry 3; the scrollable menu is the source of truth.

---

## (f) Music & mood plan — deltas only

No new engine arrangements. The `dellhollow` / `dellhollowNight` pair
(engine.js `DELLHOLLOW_SECTIONS`, line 183) does all the new work — deliberately: the
addendum's thesis is that the cottage is the town at house scale, and the score should agree.

| Where | Mood | Note |
|---|---|---|
| `playValley` cut | *(hold `forestB` through the fade)* → `silence` implicit in the fade gap | Two narrates land on quiet. |
| `playValley` pan, from Vesper's first line | `dellhollow` | **Ruling: the town theme enters early, here** — far away and under narration, the town scoring itself before the player ever stands in it. Makes `playArrival`'s `{ mood: 'dellhollow' }` a *return*, not a debut. |
| `playValley` exit | `forestB` | Back on the grey road; the theme is now a promise. |
| `stairs` day | `dellhollow` | `moodFor('stairs')` → `F.nightFallen ? 'dellhollowNight' : 'dellhollow'`. |
| `stairs` night | `dellhollowNight` | Same painting, same tune, half tempo. |
| `cottage` (free-roam + supper) | `dellhollowNight` | **Ruling: NOT `resolve`.** `resolve` is the Tally-supper and Beat 8 color; spending it here would flatten both. The music-box night-variant *is* "the town, asleep, still holding" — one house of it, awake. |
| Supper, "You stopped standing still" → the drawer | `silence` | One dropout only, back in on the kitchen-rhythm system line. |
| Supper ending, the step joke | `silence` | The door closes on quiet; `dellhollowNight` returns with the night street. |
| `vista` in `moodFor` | `null` | Cutscene-only; `playValley` owns its own moods (landing pattern, chapter2.js line 205). |

Stings: none added. Odessa gets no sting at supper for the same reason she gets none at the
winches (base §f): her footsteps — here, her ladle — are the sting.

---

## (g) Seam list — every touchpoint, by real name (for the engine agent)

**`public/js/chapter2.js`** (all line numbers = shipped file as of this addendum):

1. `flags` (19–26) + `resetFlags()` (133–166): add `supperCalled, supperDone, sorrelTalk,
   creelTalk, nibTalk`; clear `this._supT`; reset `Field.setSceneState('stairs','day')`,
   `('cottage','dusk')`; stairs lamps unlit; new NPC homes (Sorrel (360,355), Creel (820,435),
   Nib (560,565), all `scene:'stairs'`, unhidden).
2. `buildScenes()` (36–104): add `vista`, `stairs`, `cottage` per §a. Edit
   `S.descent.exits[1]` (49): `to: 'stairs', spawn: [672, 120, 'down']` (enable/denied
   unchanged). Edit `S.dellhollow.exits[0]` (70–72): zone `{x:0,y:90,w:60,h:70}` **kept**,
   `to: 'stairs', spawn: [672, 640, 'up']`, `enabled: () => true` — the night denial and
   Maren's deniedLine **move** to the stairs top exit (§a).
3. `build()` (106–130): three `N()` calls for sorrel/creel/nib (reuse-tinted sheets, §b).
4. `spawnFor()` (184–192): unchanged; *recommended* — if `supperCalled && !supperDone`,
   spawn rejoiners at the cottage door on `stairs` (870, 430) so the both-in-cottage trigger
   can't strand a late join on the quay.
5. `moodFor()` (195–207): add `case 'stairs'` and `case 'cottage'` per §f; `vista` falls to
   the `default: null`.
6. `update()` (210–274): retarget the `playArrival` gate (241–244) `'dellhollow'`→`'stairs'`;
   replace the `playNightfall` gate (255–258) with the `playSupperCall` gate (§c); add the
   `playSupper2` dwell trigger (`both && F.supperCalled && !F.supperDone && !busy && both
   players' scene === 'cottage'`, `this._supT > 8`); `playDockNight` gate (259–264) and
   `playWinches` gate (265–268) untouched.
7. `objective()` (311–329): one branch change per §d.
8. `storyMarker()` (331–345): per-scene restructure per §d.
9. `nearestThing()` (348–391): add `if (p.scene === 'stairs')` block (cistern, laundry,
   gullrail, hoist, cottagedoor; NPCs come free via the npcs loop) and
   `if (p.scene === 'cottage')` block (tallies, coatpeg, drawer, toolwall, tableseats,
   hearthpot); add `ropebridge` to the `dellhollow` block.
10. `interact()` (406–435): texts per §c inventories, incl. the two `cottagedoor` variants
    and the `hearthpot`-fires-`playSupper2` hook.
11. `talkTo()` (438–496): branches for `sorrel/creel/nib` (§c); Maren + Odessa pre-supper
    cottage lines (§c); shipped night branches for Hobb/Pell untouched.
12. `playDescent()` (501–522): the `playValley` insert after line 518 (§c, exact).
13. `playVista()` (589–601): one narrate replaced, one Vesper line deleted (§c, exact).
14. `playArrival()` (604–620): relocated + expanded per §c (three line edits marked).
15. `playNightfall()` (794–813): **removed**; body absorbed into `playSupper2`'s exit run;
    replaced by `playSupperCall` (§c).
16. **New**: `playValley`, `playSupperCall`, `playSupper2`.
17. `playLanding()` (1010–1073): single-line insert after line 1050 (§c, the drawer payoff).
18. `CHECKPOINT_NAMES` (1076) + `applyCheckpoint()` (1078–1165): six entries per §e; the
    `n >= 4` night block gains stairs night-state + lamps + flavor-NPC hides + supper flags;
    n=2 placement moves to the stairs top; landing becomes n=6.

**`public/js/main.js`**: no code changes. Behavior notes only — checkpoint menu self-adapts
(302); digit shortcuts shift (412–416); `END_CARDS` (728) / `drawEnd` (741) untouched.

**`public/js/bake-core.js`** (line 23): add `'stairs', 'cottage'` to the bake list.
**Do not add `'vista'`** (no mask by design; see §a for the loader-tolerance check).

**`public/js/assets.js`**: `SPEAKERS` += `sorrel`, `creel`, `nib` (§b). No `LOOKS`/bust
rows — verify `Dialog` handles bust-less speakers before shipping the first stairs talk.

**`public/js/engine.js`**: no changes.

**Art pipeline**: `assets/scenes/vista/main.png` (no mask); `assets/scenes/stairs/main.png`
+ `mask.png`; `assets/scenes/cottage/main.png` + `mask.png`. All POI coordinates in this doc
are pre-drift sketch values — publish `docs/chapter2-expansion-scene-deltas.md` when the
paintings land, and BFS-verify stairs (both exits + door + 5 interact mouths) and cottage
(door + 6 interact mouths) per the established pipeline.

**Untouched, verified against the shipped file:** `playChart`, `playRavine`, `playJam`,
`playMarenWet`, `playLockFive`, `playDockNight`, `playWinches`, `playFlumeRun`; the flags
`descentIntro, chartDone, strangerSeen, arrived, talked, jamDone, marenDone, lockSeen,
planMade, dockDone, boatDown, gateHalf, gatesOpen, flumeDone, marenJoined, ended`; the
Ch2→Ch3 handoff (`startChapter3` on `endT`, main.js 521/571); base doc §(g)/§(h) seams.
