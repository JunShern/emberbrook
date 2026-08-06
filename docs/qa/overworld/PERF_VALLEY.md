# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 58 | 4.44 | 1.04 |
| verts | 116492 | 911089 | 10786 | 16269 |
| tris | 53952 | 387249 | 4996 | 6915 |
| GLB MB | 22.50 | 58.01 | 2.08 | 1.04 |
| embedded texture MB | 17.03 | 17.39 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 21 | - | - |
| build s | 2.07 | 26.11 | 0.192 | 0.466 |

Where the build time goes: field 0.32s, zone grid 0.087s, terrain mesh 0.24s, planting 5.38s (149 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.087 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 10.93 |
| NORMAL | 10.93 |
| COLOR_0 | 10.70 |
| TEXCOORD_0 | 4.35 |
| INDICES | 3.63 |
| embedded images | 17.39 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
