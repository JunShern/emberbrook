# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 37 | 4.44 | 0.66 |
| verts | 116492 | 233341 | 10786 | 4167 |
| tris | 53952 | 123624 | 4996 | 2208 |
| GLB MB | 22.50 | 28.52 | 2.08 | 0.51 |
| embedded texture MB | 17.03 | 17.25 | - | - |
| images | 29 | 31 | - | - |
| materials | 17 | 18 | - | - |
| build s | 2.07 | 6.21 | 0.192 | 0.111 |

Where the build time goes: field 0.10s, zone grid 0.069s, terrain mesh 0.17s, planting 3.70s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.069 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 2.80 |
| NORMAL | 2.80 |
| COLOR_0 | 2.79 |
| TEXCOORD_0 | 1.86 |
| INDICES | 0.98 |
| embedded images | 17.25 |

| zone | coverage |
|---|---|
| meadow | 51.3% |
| forest | 21.2% |
| crag | 20.1% |
| road | 1.7% |
| water | 5.8% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 12.2 kB.
