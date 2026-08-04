# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 51 | 4.44 | 0.91 |
| verts | 116492 | 667687 | 10786 | 11923 |
| tris | 53952 | 277816 | 4996 | 4961 |
| GLB MB | 22.50 | 46.62 | 2.08 | 0.83 |
| embedded texture MB | 17.03 | 17.42 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 21 | - | - |
| build s | 2.07 | 14.86 | 0.192 | 0.265 |

Where the build time goes: field 0.28s, zone grid 0.075s, terrain mesh 0.21s, planting 3.56s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.075 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 8.01 |
| NORMAL | 8.01 |
| COLOR_0 | 7.88 |
| TEXCOORD_0 | 2.67 |
| INDICES | 2.55 |
| embedded images | 17.42 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
