# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 36 | 4.44 | 0.64 |
| verts | 116492 | 433986 | 10786 | 7750 |
| tris | 53952 | 188774 | 4996 | 3371 |
| GLB MB | 22.50 | 37.87 | 2.08 | 0.68 |
| embedded texture MB | 17.03 | 17.03 | - | - |
| images | 29 | 29 | - | - |
| materials | 17 | 17 | - | - |
| build s | 2.07 | 33.62 | 0.192 | 0.600 |

Where the build time goes: field 0.14s, zone grid 0.083s, terrain mesh 0.20s, planting 28.77s (369 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.083 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 5.21 |
| NORMAL | 5.21 |
| COLOR_0 | 5.18 |
| TEXCOORD_0 | 3.46 |
| INDICES | 1.73 |
| embedded images | 17.03 |

| zone | coverage |
|---|---|
| meadow | 61.0% |
| forest | 14.1% |
| crag | 15.9% |
| road | 1.9% |
| water | 7.1% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 11.1 kB.
