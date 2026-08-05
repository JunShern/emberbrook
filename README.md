# Emberbrook 🕯

A story JRPG prototype in the FFIX pre-rendered-background style: real-time
characters walking through fixed, pre-rendered 3D scenes with exact-pixel depth
occlusion, turn-based battles, and a chapter story that fires as you walk it.
Single-player for the prototype (couch co-op is a later upgrade — user ruling
2026-08-02; the 2D phone-controller prototype was retired 2026-08-05 and lives
in git history).

**Chapter One — Emberwake.** A traveling mapmaker arrives in a village that isn't
on any map, an hour before the night that erases it. Two strangers — the only two
the Hush cannot touch — are thrust together to carry the last warm flame in the
valley. One knows the way; one holds the fire. A cat has opinions.

**Chapter Two — Dellhollow.** The river is the road: a canal town of locks and
scaffold tiers, a log-jam, and a lockkeeper's daughter who joins the party.

## How to play

```sh
npm install
npm start
```

Open **http://localhost:3000** — the chapter-select hub. **PLAY** starts or
continues the game (`/play.html` is the engine page). `WASD`/arrows to move,
`E` to talk or act, `Esc` for the menu, `H` for the developer scene menu.

A built static version deploys to GitHub Pages — see `docs/DEPLOY.md`.
Live demo: https://junshern.github.io/emberbrook/

## Where truth lives

- `CLAUDE.md` — the context index: every system's authoritative doc, one line each.
- `STORY.md` — the story bible. `docs/VOICES.md` — dialogue voice law.
- `public/townmap/` — the landmarks-first town layouts and the map viewer.
- `docs/plans/` — the design canon (seam law, town legibility, combat, look pillars).

## Credits

Character/scene art and music are original (generated: art via the Gemini API,
music via Lyria). Animation donors: [Quaternius](https://quaternius.com/)
Universal Animation Library (CC0) and [KayKit](https://kaylousberg.com/) (CC0).
The retired 2D prototype used sprites/tiles from the CC0
[Ninja Adventure asset pack](https://github.com/sparklinlabs/superpowers-asset-packs)
by [Pixel-boy](https://twitter.com/2pblog1) / Sparklin Labs — thank you! ♥
