# Placeholder Monster Sprites — Provenance & Licensing

**These are PLACEHOLDER stand-ins, not final art.** They exist only to judge scale, silhouette,
grounding and composition on the JRPG battle screen. Every one of them is expected to be replaced
by bespoke art before release.

**CC0 / public-domain ONLY.** Nothing in this directory may be CC-BY, CC-BY-SA, NC-restricted,
GPL-encumbered, "free for non-commercial", or ripped from a commercial game. Every file below was
sourced from a page whose license field was read directly and is quoted verbatim in this document.
If you add a file here, you must verify the license on the asset page itself — never trust a
filename, a repo name, or a mirror — and record it in the table below.

All six slots are filled. Nothing was skipped, and no non-CC0 substitute was used.

## Summary table

| File | Monster slot | Concept | Native size | Source tile | Pack | Author | License |
|---|---|---|---|---|---|---|---|
| `reed-nibbler.png` | reed-nibbler | small round grazer / blob | 16x16 | `tile_0085` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |
| `brook-sprite.png` | brook-sprite | glowing wisp / floating light spirit | 16x16 | `tile_0090` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |
| `duskpad.png` | duskpad | wolf / hound / wood-dog | 16x16 | `tile_0169` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |
| `bramble-shade.png` | bramble-shade | plant / thicket creature | 16x16 | `tile_0008` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |
| `scree-shell.png` | scree-shell | armored shell / turtle | 16x16 | `tile_0150` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |
| `weir-eel.png` | weir-eel | serpent / eel | 16x16 | `tile_0041` | Tiny Creatures 1.0 | Clint Bellanger | CC0 1.0 Universal |

## Common source

All six files come from a single pack, so the set is stylistically consistent.

- **Pack name:** Tiny Creatures (version 1.0)
- **Author / attribution:** Clint Bellanger (clintbellanger.net)
- **Source page URL:** https://opengameart.org/content/tiny-creatures
- **Direct download URL:** https://opengameart.org/sites/default/files/tiny-creatures.zip
- **Downloaded:** 2026-07-30
- **Archive checked:** `tiny-creatures.zip`, 180,479 bytes, valid Zip archive
- **Sprite source inside archive:** `tiny-creatures/Tilemap/tilemap_packed.png` (160x288 RGBA)

### Exact license text seen

The OpenGameArt asset page lists the license field as:

> **CC0** (CC0 1.0 Universal)

The bundled `tiny-creatures/License.txt` inside the downloaded archive states verbatim:

```
	Tiny Creatures (1.0)

	Created by Clint Bellanger (clintbellanger.net)
	Creation date: 03-18-2024

			------------------------------

	License: (Creative Commons Zero, CC0)
	http://creativecommons.org/publicdomain/zero/1.0/

	This content is free to use in personal, educational and commercial projects.
	Support my work by crediting Clint Bellanger (this is not mandatory)

			------------------------------

 	This set is an expansion of Kenney's Tiny Dungeon and Tiny Town:
	https://kenney.nl/assets/tiny-dungeon
	https://kenney.nl/assets/tiny-town
	The included sample Tiled map and example images contain works by Kenney from these sets.

	Made with Kenney's permission
```

Attribution is **not** required under CC0, but crediting **Clint Bellanger** is appreciated by the
author and costs us nothing. The pack is an expansion of Kenney's Tiny Dungeon / Tiny Town (both
themselves CC0), made with Kenney's permission, so the upstream chain is CC0 end to end.

## Processing applied (all files)

The pack ships per-tile PNGs under `Tiles/`, but **those are palette-mode with an opaque black
background** (verified: alpha extrema `(255, 255)`, corner pixel `(0,0,0,255)`). They are unusable
over a pre-rendered battle background.

Instead, each sprite was cropped out of `Tilemap/tilemap_packed.png`, which carries a true alpha
channel with fully-clear `(0,0,0,0)` background pixels. (The alternate `Tilemap/tilemap.png` also
has alpha but stores its transparent pixels as `(118,59,54,0)`, i.e. tinted-but-clear, which can
bleed a maroon fringe under filtering — so the packed sheet was preferred.)

- Sheet geometry: 16x16 tiles, **0px** spacing, 10 columns x 18 rows.
- Index mapping: the `Tiles/tile_NNNN.png` numbering is **1-based**, so
  `sheet_index = NNNN - 1`, then `col = sheet_index % 10`, `row = sheet_index / 10`.
  This off-by-one was verified by pixel-comparing crops against the shipped `Tiles/` files.
- Crop box: `(col*16, row*16, col*16+16, row*16+16)`.
- Output: saved as 8-bit RGBA PNG via Python Pillow 11.1.0. **No scaling, no upscaling, no
  recolouring, no filtering** — pixels are bit-identical to the source sheet.
- The full 16x16 tile canvas was kept (rather than tight-cropping to the alpha bbox) so that all
  six sprites share one common canvas and consistent relative scale/grounding.

The dark `(63,38,49)` border around each creature is the pack's intentional thick outline style,
not a background — it is fully opaque and should be kept.

## Per-file detail

### `reed-nibbler.png`
- Slot: **reed-nibbler** — small round grazer / blob / critter
- Depicts: a round-topped orange slime / ooze blob
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0085` (sheet index 84, col 4, row 8) from `Tilemap/tilemap_packed.png`
  at box `(64, 128, 80, 144)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(2,2,14,15)`.

### `brook-sprite.png`
- Slot: **brook-sprite** — glowy wisp / will-o-wisp / floating light spirit
- Depicts: a bright blue glowing orb with a white-hot core
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0090` (sheet index 89, col 9, row 8) from `Tilemap/tilemap_packed.png`
  at box `(144, 128, 160, 144)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(2,2,15,15)`.

### `duskpad.png`
- Slot: **duskpad** — wolf / hound / wood-dog
- Depicts: a four-legged brown hound/dog standing in profile
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0169` (sheet index 168, col 8, row 16) from `Tilemap/tilemap_packed.png`
  at box `(128, 256, 144, 272)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(1,2,16,16)`.
- Note: the pack also contains bipedal werewolf sprites (`tile_0094`, `tile_0095`); the quadruped
  hound was chosen deliberately because its silhouette reads better as a beast enemy.

### `bramble-shade.png`
- Slot: **bramble-shade** — plant / thicket / vine / treant creature
- Depicts: a leafy green vine-tangle creature with glowing eyes on a woody stump base
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0008` (sheet index 7, col 7, row 0) from `Tilemap/tilemap_packed.png`
  at box `(112, 0, 128, 16)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(0,0,16,16)`
  (fills the full tile).
- Alternative in the same pack if a plainer treant is wanted: `tile_0114` (canopy-on-trunk tree).

### `scree-shell.png`
- Slot: **scree-shell** — armored shell / turtle / rock golem
- Depicts: a green shelled turtle in side view, shell dominant
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0150` (sheet index 149, col 9, row 14) from `Tilemap/tilemap_packed.png`
  at box `(144, 224, 160, 240)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(0,3,16,14)`
  — this is the shortest sprite of the set, occupying only 11 of 16 rows.
- Alternative in the same pack if a rock golem is preferred: `tile_0048` (stone elemental).

### `weir-eel.png`
- Slot: **weir-eel** — serpent / eel / snake / worm
- Depicts: a coiled green serpent with a raised head
- Source page: https://opengameart.org/content/tiny-creatures
- Direct download: https://opengameart.org/sites/default/files/tiny-creatures.zip
- Pack: Tiny Creatures 1.0 — Author: Clint Bellanger
- License: `CC0` (CC0 1.0 Universal)
- Downloaded: 2026-07-30
- Processing: cropped `tile_0041` (sheet index 40, col 0, row 4) from `Tilemap/tilemap_packed.png`
  at box `(0, 64, 16, 80)`. Saved as RGBA PNG at native 16x16, unscaled. Alpha bbox `(0,1,16,16)`.

## Rendering notes for the battle screen

- Every file is **16x16 native**. Ship them at native resolution and scale up in CSS with
  `image-rendering: pixelated` — do not resample or pre-upscale on disk.
- To read at roughly 100-260px tall, scale by about **8x to 16x** (e.g. `width: 192px; height: 192px`
  is a clean 12x and keeps pixels square).
- **Use integer scale factors only.** Non-integer scaling on 16px art produces uneven pixel widths
  that look broken even with `pixelated`.
- All six share the same 16x16 canvas, so a single uniform scale factor gives correct relative
  sizing between monsters out of the box. `scree-shell` will sit slightly shorter and `bramble-shade`
  slightly taller, which is intended.
- Sprites face **right** where not symmetrical (per the pack's own `Tilesheet.txt`); horizontally
  flip if enemies should face left toward the party.
