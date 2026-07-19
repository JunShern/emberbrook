# Emberbrook 🕯

A couch co-op story RPG for two players. The TV (a MacBook browser, fullscreened)
is the game screen; each phone becomes a controller over your home Wi-Fi.

**Chapter One — Emberwake.** A traveling mapmaker arrives in a village that isn't
on any map, an hour before the night that erases it. Two strangers — the only two
the Hush cannot touch — are thrust together to carry the last warm flame in the
valley. One knows the way; one holds the fire. A cat has opinions.

Played in three acts: **P1 plays Vesper's arrival alone** (a forest road, a
waystone from a dream), then **P2 plays Lake's lamplighting rounds alone**
(beginning in his cottage), then their stories converge at the festival and
it's one shared screen from there.

The world is a set of hand-painted scenes (AI-generated in a fixed anime-film
style, layout-controlled where gameplay demands it) with generated cel-anime
character sprites, per-scene color grading, baked lighting states (festival
night / the grey Hush), and a scene engine with walkable-area polygons,
exits, occluders and a smoothed camera. Dev pages: `proto.html` (scene
prototype), `viewer.html` (sprite-sheet inspector), `busts.html`,
`maps-options.html`, `zoom-options.html`, `jrpg-options.html` (art direction
history). `tools/genart.mjs` generates art via the Gemini API (key in `.env`).

## How to play

1. Install & start (install needed once):

   ```sh
   npm install
   npm start
   ```

2. Connect the MacBook to the TV, open **http://localhost:3000**, fullscreen it
   (`⌃⌘F`), and click once anywhere to enable music (`M` mutes).

3. Each phone (on the **same Wi-Fi**) scans the QR code on screen, then claims a
   keeper: **Vesper** (plays first) or **Lake** (enters in Act II).

4. Left thumb = walk. **A** = talk / act / advance dialogue. Some moments need
   you both to **hold A together**.

### Notes

- Testing without phones: `WASD`+`E` plays Vesper, arrow keys+`Enter` plays Lake
  (unclaimed roles are auto-claimed by the keyboard).
- Dev mode: press `K` to toggle **keyboard override** — the keyboard then also
  drives characters that phones have claimed, so you can test without touching
  your phone. Phone input resumes whenever the keys are idle.
- If a phone locks or drops, reopen the page and tap your keeper again — you
  resume where you were.
- If phones can't connect: System Settings → Network → Firewall → allow `node`.
- Refreshing the TV page restarts the chapter.

See `ROADMAP.md` for the world bible, planned party members, and chapters 2–10.

## Credits

Character sprites, face portraits, and tileset from the CC0
[Ninja Adventure asset pack](https://github.com/sparklinlabs/superpowers-asset-packs)
by [Pixel-boy](https://twitter.com/2pblog1) / Sparklin Labs — thank you! ♥
Everything else (engine, story, music, remaining art) is original.
