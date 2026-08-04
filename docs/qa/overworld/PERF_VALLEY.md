# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 51 | 4.44 | 0.91 |
| verts | 116492 | 648256 | 10786 | 11576 |
| tris | 53952 | 268426 | 4996 | 4793 |
| GLB MB | 22.50 | 45.79 | 2.08 | 0.82 |
| embedded texture MB | 17.03 | 17.42 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 21 | - | - |
| build s | 2.07 | 12.29 | 0.192 | 0.219 |

Where the build time goes: field 0.23s, zone grid 0.074s, terrain mesh 0.17s, planting 3.45s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.074 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 7.78 |
| NORMAL | 7.78 |
| COLOR_0 | 7.70 |
| TEXCOORD_0 | 2.55 |
| INDICES | 2.49 |
| embedded images | 17.42 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
