# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 41 | 4.44 | 0.73 |
| verts | 116492 | 325768 | 10786 | 5817 |
| tris | 53952 | 167859 | 4996 | 2997 |
| GLB MB | 22.50 | 33.03 | 2.08 | 0.59 |
| embedded texture MB | 17.03 | 17.42 | - | - |
| images | 29 | 34 | - | - |
| materials | 17 | 19 | - | - |
| build s | 2.07 | 8.09 | 0.192 | 0.144 |

Where the build time goes: field 0.24s, zone grid 0.078s, terrain mesh 0.17s, planting 3.39s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.078 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 3.91 |
| NORMAL | 3.91 |
| COLOR_0 | 3.90 |
| TEXCOORD_0 | 2.60 |
| INDICES | 1.23 |
| embedded images | 17.42 |

| zone | coverage |
|---|---|
| meadow | 50.0% |
| forest | 21.7% |
| crag | 20.9% |
| road | 1.7% |
| water | 5.8% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 12.4 kB.
