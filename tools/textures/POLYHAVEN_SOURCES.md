# Fetched texture sources

Everything in `tools/textures/` and `tools/textures/overworld/` that is a
photograph rather than a generated map comes from **Poly Haven**
(<https://polyhaven.com>), fetched headlessly through their public API
(`https://api.polyhaven.com/files/<slug>`) — no key, no browser.  Poly Haven
assets are **CC0**.

Naming convention in `tools/textures/overworld/` is `<slug>_{diff,nor_gl,rough}_1k.jpg`,
which is what `overworld3_build.layer_paths()` and the material recipes expect.
1k is deliberate: the terrain tiles these at ~6u per repeat, so 1k is already
finer than the camera can resolve, and every image is embedded in `scene.glb`.

## Fetched by the foliage & rock quality pass (2026-07-30)

| slug | used for | why this one |
|---|---|---|
| `dark_rock_02` | the crag / gorge-wall rock material | Poly Haven tags it *stratified, striated, fissured, craggy* — it is the only rock face in their library whose photo already contains BEDDING, which is the thing the Dellhollow gorge walls needed and the fine-jitter crag treatment could not supply |
| `cliff_side` | warm crag variant (canyon rim, outcrops) | *canyon, sediment, eroded, orange* — matches the region's existing warm rock palette so it can sit beside `rock_face_03` without a hue jump |

Both are 1k jpg (`Diffuse` / `nor_gl` / `Rough`), ~0.4-1.0 MB each.

## Fetched earlier (rounds 1-3, same source)

`leafy_grass`, `withered_grass`, `sparse_grass`, `stony_dirt_path`,
`forest_ground_04`, `aerial_grass_rock`, `aerial_rocks_02`, `dry_riverbed_rock`,
`mossy_rock`, `snow_02`, `rock_face_03`, and the interior/town sets
(`clay_plaster`, `red_slate_roof_tiles_01`, `weathered_planks`,
`dark_wooden_planks`, plank/stone/fabric variants) — see `_manifest*.json`.

## Generated, NOT fetched

These are numpy-drawn and belong to this repo:

| file | generator |
|---|---|
| `overworld/leafclump_atlas.png` + `leafclump_nor.jpg` | `tools/foliage_atlas.py` — the leaf-cluster card atlas |
| `overworld/leafmass_tile.jpg` + `leafmass_tile_nor.jpg` | `tools/foliage_atlas.py` — the tileable core leaf mass |
| `overworld/veg3_*`, `veg_leaf_atlas.png`, `veg_tuft_atlas.png` | `tools/overworld3_lib.py` / `overworld2_lib.py` (rounds 2-3) |
| `canopy_painted_{albedo,normal}.png` | the third canopy iteration (superseded) |
