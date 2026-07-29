# Overworld round 2 — perf per style (one 120 x 90u tile)

| style | draws | verts | tris | GLB MB | tex MB | imgs | mats | nrm | rough | emis | MASK | UV1 | build s/tile | per-tile bake work |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E | 18 | 31801 | 24496 | 1.75 | 0.47 | 1 | 5 | 0 | 0 | 2 | 0 | 0 | 18.5 | 2 Cycles bakes (albedo + dusk lighting) per tile |
| F | 30 | 33151 | 24052 | 14.33 | 12.71 | 21 | 14 | 12 | 12 | 0 | 0 | 0 | 0.8 | no bake — tiled PBR slots, per-material only |
| G | 18 | 21889 | 20656 | 2.46 | 1.51 | 2 | 6 | 2 | 0 | 0 | 0 | 1 | 4.2 | 2 Cycles bakes (albedo + AO) per tile |
| H | 20 | 33653 | 27174 | 2.71 | 1.30 | 3 | 7 | 0 | 0 | 0 | 2 | 0 | 2.9 | 1 Cycles bake (albedo) per tile + one-off card atlases |

`build s/tile` is wall-clock inside overworld2_build.py on an M1 Max (Cycles baking on Metal).  It is the number that decides whether a style can cover a world: E and G pay it AGAIN for every new tile, F and H essentially do not.

Texture MB is what is embedded in the GLB.  F's is the shared PolyHaven set at 1k (diffuse+normal+roughness x 4 terrain classes x 5 prop classes); E/G/H's is dominated by their single baked 2048 terrain map.
