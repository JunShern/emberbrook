# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 46 | 4.44 | 0.82 |
| verts | 116492 | 297680 | 10786 | 5316 |
| tris | 53952 | 150528 | 4996 | 2688 |
| GLB MB | 22.50 | 31.69 | 2.08 | 0.57 |
| embedded texture MB | 17.03 | 17.42 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 19 | - | - |
| build s | 2.07 | 9.34 | 0.192 | 0.167 |

Where the build time goes: field 0.37s, zone grid 0.093s, terrain mesh 0.21s, planting 3.89s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.093 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 3.57 |
| NORMAL | 3.57 |
| COLOR_0 | 3.57 |
| TEXCOORD_0 | 2.37 |
| INDICES | 1.14 |
| embedded images | 17.42 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
