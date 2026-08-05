# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 55 | 4.44 | 0.98 |
| verts | 116492 | 880075 | 10786 | 15716 |
| tris | 53952 | 373667 | 4996 | 6673 |
| GLB MB | 22.50 | 56.70 | 2.08 | 1.01 |
| embedded texture MB | 17.03 | 17.39 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 21 | - | - |
| build s | 2.07 | 19.15 | 0.192 | 0.342 |

Where the build time goes: field 0.23s, zone grid 0.068s, terrain mesh 0.19s, planting 3.85s (149 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.068 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 10.56 |
| NORMAL | 10.56 |
| COLOR_0 | 10.33 |
| TEXCOORD_0 | 4.24 |
| INDICES | 3.55 |
| embedded images | 17.39 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
