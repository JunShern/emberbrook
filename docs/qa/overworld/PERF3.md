# Overworld round 3 — style F2 against round-2 F (one 120 x 90u tile)

| style | draws | verts | tris | GLB MB | tex MB | imgs | mats | nrm | rough | MASK | build s/tile | per-tile bake work |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F  | 30 | 33151 | 24052 | 14.33 | 12.71 | 21 | 14 | 12 | 12 | 0 | 0.8 | no bake — tiled PBR slots |
| F2 | 48 | 116492 | 53952 | 22.50 | 17.03 | 29 | 17 | 13 | 11 | 1 | 2.1 | no bake — tiled PBR + procedural veg maps (one-off) |

F2 costs 2.1 s/tile against F's 0.8, and **0.01 s of that is the zone grid** — the encounter geography is essentially free. The rest is the zone-aware tessellation and 4x the vegetation.

The tri count roughly doubles: the crag cells fan into 4 triangles each (+23% of quads) and the trees are real constructions rather than round 1's three primitives. The GLB grows mostly in TEXTURE — the procedural canopy, bark and leaf-mass maps — and those are one-off shared assets, so a second tile adds geometry only.

| zone | coverage |
|---|---|
| meadow | 47.5% |
| forest | 16.7% |
| crag | 23.9% |
| road | 6.8% |
| water | 5.1% |

Zone grid: 96 x 72 cells of 1.25u (6912 total), run-length encoded to 5.3 kB.
