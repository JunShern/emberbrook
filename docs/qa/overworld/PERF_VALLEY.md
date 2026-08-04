# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 51 | 4.44 | 0.91 |
| verts | 116492 | 757765 | 10786 | 13532 |
| tris | 53952 | 321230 | 4996 | 5736 |
| GLB MB | 22.50 | 50.89 | 2.08 | 0.91 |
| embedded texture MB | 17.03 | 17.23 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 21 | - | - |
| build s | 2.07 | 17.72 | 0.192 | 0.316 |

Where the build time goes: field 0.28s, zone grid 0.084s, terrain mesh 0.22s, planting 4.48s (149 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.084 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 9.09 |
| NORMAL | 9.09 |
| COLOR_0 | 8.96 |
| TEXCOORD_0 | 3.39 |
| INDICES | 3.05 |
| embedded images | 17.23 |

| zone | coverage |
|---|---|
| meadow | 56.8% |
| forest | 13.3% |
| crag | 21.9% |
| road | 1.6% |
| water | 6.3% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 13.7 kB.
