# Emberbrook — Roadmap & World Bible

## The world

The **Vale of Brindlemere**: scattered villages, each kept warm by a **Heartlight** —
a flame-crystal that holds the village's collective memory. "A village is a story it
tells itself by firelight." All Heartlights were kindled long ago from **the Kindling**,
a shrine deep in the Whisperwood, by the **Order of Lamplighters** — now dwindled to
one hereditary lighter per town. Their creed: *light does not die; it is only ever carried.*

**The Hush**: grey moths that eat memory-light. When a Heartlight is harvested, everything
it held drains skyward. People keep skills and words; they lose names, faces, bonds.
Written things fade slower — ink is a countdown, not a cure.

**The Lanternless** (antagonist arc): a figure in grey with an *empty* lamp that is
somehow full — a fallen Lamplighter who takes light instead of giving it. He bows,
politely, like a debt collector. Why he harvests, and for whom, is the spine of the
ten-chapter mystery. He recognized Lake's lighter.

**The mystery of the pair**: Vesper has drawn the Kindling in her dreams 41 times —
it has been *calling* her. Lake's Everlit Lighter is a splinter of the first flame.
Neither knows why they alone kept their memories. (Planned answer threads through
chapters 4–9; the flame chooses carriers in pairs — every Lamplighter had a Cartographer,
a fact the Order erased about itself.)

## The party (recruits by chapter)

| Member | Joins | Role | Hook |
|---|---|---|---|
| **Vesper** | Ch1 | mapmaker (P1) | dreams roads; is building a "ledger of everyone" as backup memory |
| **Lake** | Ch1 | lamplighter (P2) | last warm flame; knows every name in Emberbrook |
| **Mochi** | Ch1 | cat, scout | immune to the Hush; hates the Lanternless on sight |
| **Bramble** | Ch2 | shrine-keeper golem | moss-covered guardian of the Kindling road, rusty, 300 years of small talk saved up |
| **Wick** | Ch4 | ex-apprentice of the Lanternless | knows the enemy's routes; morally grey; keeps trying to pay for things with stolen memories |
| **Pip** | Ch6 | stowaway | follows the party out; his mother still doesn't remember him — he wants to earn a memory worth giving back |

## Chapter arc (sketch)

1. **Emberwake** ✅ — the Hush takes Emberbrook; the pact; through the Old Gate.
2. **The Whisperwood** — forest travel, first co-op puzzles (light/shadow), meet Bramble; discover another village already blank *and empty*.
3. **The Kindling** — the shrine is cold; the first flame was *taken*, not lost. First "boss": a moth-swarm shepherd.
4. **The Tollroad** — meet Wick; learn the Lanternless collects for something called **the Archive**.
5. **Brindlemere Fair** — a big town still lit; heist/social chapter; Vesper's dream-charts start drawing *forward* in time.
6. **The Long Dark** — Pip stows away; a chapter about what the party would each trade away.
7. **The Archive** — a library of stolen villages, each shelf a bottled town.
8. **The Order's Secret** — why Lamplighters come in pairs; Lake's grandmother's last entry.
9. **The Unlit Road** — carrying Emberbrook's flame home while hunted.
10. **Emberwake II** — the festival again, one year on; what gets remembered, what gets forgiven.

## Systems roadmap (build as needed, not all at once)

- **Save/checkpoints**: serialize chapter flags + positions to localStorage on the display; "continue" on boot. (Next up — chapters get long.)
- **Inventory**: `player.items` exists conceptually (Dream Charts, Last Spark). Add a phone-side satchel screen (controller shows your items; TV stays clean).
- **Equipment**: slot-based (charm / tool / coat), stat mods, found not bought in early chapters.
- **Combat** (Ch3+): real-time Zelda-ish. Phones get A (interact/attack) + B (dodge/lantern-flash). Enemies = moth constructs; "damage" is light vs. dark — party wields light, never kills villagers-turned. Companions fight as AI.
- **Co-op verbs to grow**: twin sigils → carry-together objects, lantern relay (pass the flame), one-holds-the-light-while-one-works, dream-map navigation (Vesper's player sees routes Lake's can't).
- **Engine**: chapter files are self-contained (`chapter1.js`); a chapter registry + shared save loader is the next refactor when chapter2 starts.

## Architecture

```
server.js            dumb WebSocket relay + static + QR (never holds game state)
public/index.html    TV screen (the game runs here)
public/controller.html  phone controller (role select, stick + A, prompts, haptics)
public/js/
  assets.js    palette, pixel-sprite compiler, portraits, character looks
  engine.js    screen, camera, FX (letterbox/flash/desat/fade), particles, audio moods, net
  world.js     tiles + autotiling, props, houses, lighting, character rendering
  story.js     dialogue w/ portraits, cutscene runner, banners, objectives, toasts
  chapter1.js  ALL Chapter One content: map, cast, dialogue, cutscenes, phases
  main.js      boot, roles/join, keyboard fallback, game loop, render pipeline
```
