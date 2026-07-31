# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 45 | 4.44 | 0.80 |
| verts | 116492 | 331774 | 10786 | 5925 |
| tris | 53952 | 167093 | 4996 | 2984 |
| GLB MB | 22.50 | 33.30 | 2.08 | 0.59 |
| embedded texture MB | 17.03 | 17.42 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 19 | - | - |
| build s | 2.07 | 10.46 | 0.192 | 0.187 |

Where the build time goes: field 0.28s, zone grid 0.092s, terrain mesh 0.24s, planting 4.13s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.092 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 3.98 |
| NORMAL | 3.98 |
| COLOR_0 | 3.97 |
| TEXCOORD_0 | 2.65 |
| INDICES | 1.24 |
| embedded images | 17.42 |

| zone | coverage |
|---|---|
| meadow | 53.8% |
| forest | 14.0% |
| crag | 24.2% |
| road | 1.7% |
| water | 6.4% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.0 kB.
