# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 37 | 4.44 | 0.66 |
| verts | 116492 | 230504 | 10786 | 4116 |
| tris | 53952 | 122452 | 4996 | 2187 |
| GLB MB | 22.50 | 28.38 | 2.08 | 0.51 |
| embedded texture MB | 17.03 | 17.25 | - | - |
| images | 29 | 31 | - | - |
| materials | 17 | 18 | - | - |
| build s | 2.07 | 5.93 | 0.192 | 0.106 |

Where the build time goes: field 0.11s, zone grid 0.066s, terrain mesh 0.18s, planting 3.45s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.066 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 2.77 |
| NORMAL | 2.77 |
| COLOR_0 | 2.76 |
| TEXCOORD_0 | 1.84 |
| INDICES | 0.96 |
| embedded images | 17.25 |

| zone | coverage |
|---|---|
| meadow | 50.6% |
| forest | 21.0% |
| crag | 20.9% |
| road | 1.7% |
| water | 5.8% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 12.2 kB.
