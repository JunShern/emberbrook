# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 37 | 4.44 | 0.66 |
| verts | 116492 | 252439 | 10786 | 4508 |
| tris | 53952 | 151508 | 4996 | 2706 |
| GLB MB | 22.50 | 29.07 | 2.08 | 0.52 |
| embedded texture MB | 17.03 | 17.03 | - | - |
| images | 29 | 29 | - | - |
| materials | 17 | 18 | - | - |
| build s | 2.07 | 6.10 | 0.192 | 0.109 |

Where the build time goes: field 0.12s, zone grid 0.079s, terrain mesh 0.19s, planting 3.34s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.079 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 3.03 |
| NORMAL | 3.03 |
| COLOR_0 | 3.02 |
| TEXCOORD_0 | 1.78 |
| INDICES | 1.13 |
| embedded images | 17.03 |

| zone | coverage |
|---|---|
| meadow | 55.9% |
| forest | 14.8% |
| crag | 20.6% |
| road | 2.2% |
| water | 6.6% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.0 kB.
