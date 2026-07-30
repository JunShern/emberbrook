# The Valley region against the F2 prototype tile

The region is **280 x 200u = 56.0 k square units**, the F2 tile was 120 x 90u = 10.8 k — **5.2x the area**.  Absolute numbers are what the runtime pays; the per-1000-square-unit column is the only fair comparison of the two builds.

| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |
|---|---|---|---|---|
| draw calls | 48 | 37 | 4.44 | 0.66 |
| verts | 116492 | 234304 | 10786 | 4184 |
| tris | 53952 | 118926 | 4996 | 2124 |
| GLB MB | 22.50 | 28.29 | 2.08 | 0.51 |
| embedded texture MB | 17.03 | 17.03 | - | - |
| images | 29 | 29 | - | - |
| materials | 17 | 18 | - | - |
| build s | 2.07 | 6.12 | 0.192 | 0.109 |

Where the build time goes: field 0.11s, zone grid 0.074s, terrain mesh 0.20s, planting 3.50s (143 trees).  The zone grid — the whole encounter geography of a 280 x 200u region, 224 x 160 cells — costs **0.074 s**.

Geometry byte budget inside the GLB:

| attribute | MB |
|---|---|
| POSITION | 2.81 |
| NORMAL | 2.81 |
| COLOR_0 | 2.80 |
| TEXCOORD_0 | 1.84 |
| INDICES | 0.95 |
| embedded images | 17.03 |

| zone | coverage |
|---|---|
| meadow | 54.9% |
| forest | 14.7% |
| crag | 21.7% |
| road | 2.1% |
| water | 6.6% |

Zone grid: 224 x 160 cells of 1.25u (35840 total), run-length encoded to 12.8 kB.
