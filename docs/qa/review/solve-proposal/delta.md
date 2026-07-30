# Exit-seam framing — delta report

Generated `2026-07-30T14:32:40Z` by `docs/qa/review/solve-proposal/derive_delta.mjs`.

Old = the shipped `townmap/dellhollow.cameras.solved.json`. New =
`./dellhollow.cameras.solved.proposed.json`, from
`node tools/cine_solve.mjs --frame-exits --out docs/qa/review/solve-proposal/dellhollow.cameras.solved.proposed.json`.
**Nothing is shipped and nothing is re-baked by this tranche** — the live chain
(`cameras.solved.json` → `cine.json` → the 17 baked backdrops) is untouched.

Self-check: this report's OLD projection agrees with the shipped routes file's own to
**0.001 ndc** (same cameras, same `project()`).

## 1. Per-shot camera delta

| shot | pin | exit seams | dist old→new | Δpos | Δaim | max mark shift | charPx near old→new | taste review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gate` |  | 1 | 29.94 → 30.01 (+0.07) | 0.073 | 0.034 | 2 px | 92 → 92 (+0%) | — |
| `shelf-west` |  | 2 | 21.97 → 22.05 (+0.08) | 0.061 | 0.037 | 2 px | 118 → 117 (-1%) | — |
| `shelf-east` |  | 2 | 15.79 → 15.81 (+0.02) | 0.012 | 0.01 | 1 px | 208 → 207 (-0%) | — |
| `loop-stairs` |  | 3 | 20.26 → 20.26 (+0) | 0.039 | 0.038 | 3 px | 128 → 128 (+0%) | — |
| `quay-west` |  | 4 | 29.31 → 28.53 (-0.78) | 0.955 | 0.447 | 38 px | 93 → 97 (+4%) | — |
| `quay-east` |  | 3 | 18 → 18 (+0) | 0.164 | 0.165 | 6 px | 143 → 144 (+1%) | — |
| `lockhead` |  | 2 | 19.06 → 21.71 (+2.65) | 2.61 | 0.084 | 116 px | 157 → 131 (-17%) | **character -17% smaller near-field** |
| `cottage` |  | 3 | 22.89 → 32.87 (+9.98) | 10.033 | 0.062 | 215 px | 111 → 73 (-34%) | **standoff +10.0u (the shot pulls back); character -34% smaller near-field** |
| `crossing` |  | 2 | 25.07 → 25.1 (+0.03) | 0.018 | 0.011 | 1 px | 91 → 91 (+0%) | — |
| `weave` |  | 3 | 30.42 → 30.57 (+0.15) | 0.2 | 0.191 | 8 px | 88 → 88 (+0%) | — |
| `deep-stairs` |  | 2 | 30.68 → 30.69 (+0.01) | 0.006 | 0.01 | 0 px | 78 → 78 (+0%) | — |
| `boatyard` | **PIN** | 0 | 24.27 → 24.27 (+0) | 0 | 0 | 0 px | 181 → 181 (+0%) | — |
| `waterfront` |  | 4 | 25.05 → 28 (+2.95) | 3.513 | 0.601 | 129 px | 139 → 126 (-9%) | — |
| `fishdock` |  | 3 | 26.53 → 26.33 (-0.2) | 0.254 | 0.117 | 7 px | 104 → 105 (+1%) | — |
| `cottage-steps` |  | 2 | 24.92 → 24.94 (+0.02) | 0.016 | 0.018 | 1 px | 101 → 100 (-1%) | — |
| `lockfive` |  | 4 | 26.73 → 26.97 (+0.24) | 0.113 | 0.147 | 3 px | 125 → 124 (-1%) | **far-field character crosses the rubric's 50 px floor (51 → 49 px)** |
| `north-landing` |  | 1 | 21.84 → 22.78 (+0.94) | 0.472 | 0.525 | 8 px | 162 → 157 (-3%) | — |

16 of 17 shots re-aim; 1 stay put (pinned: `boatyard`). Every shot still frames 100% of its samples (inFrameFrac 1).

Backdrops a later re-bake would visibly have to repaint (a mark moves ≥4 px on the 1344×768 plate): **8** — `quay-west`, `quay-east`, `lockhead`, `cottage`, `weave`, `waterfront`, `fishdock`, `north-landing`. Sub-pixel-to-3 px, cosmetic: `gate`, `shelf-west`, `shelf-east`, `loop-stairs`, `crossing`, `cottage-steps`, `lockfive`.

## 2. The five off-frame exits

| shot | exit | old ndc | old head ndc | new ndc | new head ndc | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `lockhead` | `seam:lockhead__keepers-cottage` | -0.97, -1.06 | -1.02, -0.75 | -0.82, -0.90 | -0.86, -0.63 | FIXED |
| `cottage` | `seam:keepers-cottage__lock-five` | -0.50, -1.36 | -0.51, -1.12 | -0.33, -0.89 | -0.33, -0.72 | FIXED |
| `boatyard` | `seam:winch-foot__slipway` | -0.34, -1.15 | -0.35, -0.76 | -0.34, -1.15 | -0.35, -0.76 | ground-off (unchanged) |
| `waterfront` | `seam:fish-dock__winch-foot` | -0.20, -1.04 | -0.21, -0.72 | -0.15, -0.81 | -0.15, -0.54 | FIXED |
| `waterfront` | `seam:deep-stairs-foot__fish-dock` | -0.43, -1.20 | -0.45, -0.85 | -0.32, -0.92 | -0.33, -0.64 | FIXED |

## 3. Every entry and exit, old vs new

### `gate` — The Valley Gate

pos [26.272,31.8,36.49] → [26.325,31.843,36.516] · aim [15.871,6.057,25.273] → [15.901,6.04,25.273] · fov 35° · margin 0.07 · samples 334 → 336

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:valley-gate__inn` | -0.20, -0.11 | -0.19, -0.11 | +0.000 | 0.804 → 0.806 | 65 → 65 | ok |
| entry | `portal:dellhollow-valley-gate` | 0.10, -0.05 | 0.10, -0.05 | +0.000 | 0.899 → 0.897 | 65 → 65 | ok |
| entry | `spawn:gate` | 0.24, -0.05 | 0.24, -0.05 | +0.000 | 0.763 → 0.762 | 65 → 65 | ok |
| exit | `seam:valley-gate__inn` | -0.32, -0.25 | -0.32, -0.25 | +0.000 | 0.678 → 0.681 | 65 → 65 | ok |
| exit | `portal:valley-gate` | -0.09, -0.05 | -0.08, -0.05 | +0.000 | 0.914 → 0.916 | 65 → 65 | ok |

### `shelf-west` — The Shelf — shop street, west

pos [16.001,24.416,25.116] → [15.998,24.475,25.13] · aim [26.821,5.676,21.301] → [26.857,5.667,21.301] · fov 35° · margin 0.1 · samples 420 → 424

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:valley-gate__inn` | 0.37, -0.07 | 0.37, -0.07 | -0.001 | 0.630 → 0.629 | 92 → 92 | ok |
| entry | `seam:weapon-shop__armor-shop` | -0.65, -0.14 | -0.65, -0.14 | -0.001 | 0.348 → 0.351 | 74 → 74 | ok |
| entry | `door:inn` | 0.13, -0.37 | 0.13, -0.37 | +0.000 | 0.634 → 0.634 | 98 → 98 | ok |
| entry | `door:item-shop` | -0.13, -0.35 | -0.13, -0.35 | +0.000 | 0.645 → 0.645 | 97 → 97 | ok |
| entry | `door:weapon-shop` | -0.56, -0.21 | -0.56, -0.21 | +0.000 | 0.435 → 0.438 | 81 → 81 | ok |
| exit | `door:inn` | 0.38, -0.41 | 0.39, -0.41 | +0.000 | 0.588 → 0.588 | 103 → 103 | ok |
| exit | `door:item-shop` | -0.38, -0.37 | -0.38, -0.37 | +0.000 | 0.621 → 0.624 | 98 → 98 | ok |
| exit | `door:weapon-shop` | -0.61, -0.14 | -0.61, -0.14 | +0.000 | 0.389 → 0.391 | 74 → 74 | ok |
| exit | `seam:valley-gate__inn` | 0.56, 0.13 | 0.56, 0.13 | -0.001 | 0.443 → 0.442 | 99 → 99 | ok |
| exit | `seam:weapon-shop__armor-shop` | -0.77, -0.14 | -0.77, -0.14 | +0.000 | 0.232 → 0.235 | 72 → 72 | ok |

### `shelf-east` — The Shelf — shop street, east

pos [56.899,15.816,25.148] → [56.909,15.813,25.153] · aim [44.163,7.857,20.269] → [44.161,7.847,20.269] · fov 35° · margin 0.1 · samples 236 → 240

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:weapon-shop__armor-shop` | 0.06, -0.11 | 0.06, -0.11 | +0.000 | 0.893 → 0.893 | 116 → 116 | ok |
| entry | `seam:armor-shop__shelf-homes` | 0.01, -0.35 | 0.01, -0.35 | -0.001 | 0.650 → 0.649 | 140 → 140 | ok |
| entry | `door:armor-shop` | -0.16, -0.47 | -0.16, -0.47 | +0.000 | 0.534 → 0.534 | 153 → 153 | ok |
| exit | `door:armor-shop` | 0.10, -0.28 | 0.11, -0.28 | +0.000 | 0.715 → 0.715 | 134 → 134 | ok |
| exit | `seam:weapon-shop__armor-shop` | 0.05, -0.01 | 0.05, -0.01 | +0.000 | 0.948 → 0.947 | 104 → 104 | ok |
| exit | `seam:armor-shop__shelf-homes` | -0.21, -0.50 | -0.20, -0.50 | +0.000 | 0.501 → 0.501 | 156 → 156 | ok |

### `loop-stairs` — The Loop Stairs

pos [50.107,28.769,23.187] → [50.069,28.762,23.189] · aim [54.84,9.784,17.945] → [54.804,9.772,17.945] · fov 35° · margin 0.11 · samples 346 → 352

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:armor-shop__shelf-homes` | 0.48, 0.16 | 0.47, 0.16 | -0.001 | 0.523 → 0.526 | 105 → 105 | ok |
| entry | `seam:shelf-homes__quay-deck` | 0.24, -0.00 | 0.24, -0.00 | +0.000 | 0.756 → 0.759 | 101 → 101 | ok |
| entry | `seam:shelf-homes__market-stalls` | 0.10, 0.07 | 0.10, 0.07 | +0.000 | 0.899 → 0.902 | 100 → 100 | ok |
| exit | `seam:armor-shop__shelf-homes` | 0.68, 0.17 | 0.68, 0.17 | +0.000 | 0.316 → 0.319 | 105 → 105 | ok |
| exit | `seam:shelf-homes__quay-deck` | 0.05, -0.42 | 0.04, -0.42 | +0.000 | 0.581 → 0.581 | 99 → 99 | ok |
| exit | `seam:shelf-homes__market-stalls` | -0.10, -0.07 | -0.10, -0.07 | +0.000 | 0.900 → 0.896 | 97 → 97 | ok |

### `quay-west` — The Harbour Deck

pos [37.258,40.64,24.819] → [37.915,39.994,24.568] · aim [45.359,14.142,15.278] → [45.803,14.193,15.278] · fov 35° · margin 0.06 · samples 110 → 118

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:shelf-homes__quay-deck` | -0.40, 0.08 | -0.39, 0.07 | -0.001 | 0.600 → 0.614 | 61 → 63 | ok |
| entry | `seam:quay-deck__market-stalls` | -0.46, -0.03 | -0.45, -0.03 | -0.003 | 0.537 → 0.550 | 64 → 66 | ok |
| entry | `seam:quay-deck__pilot-cluster` | -0.69, -0.10 | -0.69, -0.10 | -0.005 | 0.306 → 0.313 | 68 → 70 | ok |
| entry | `seam:deep-stairs-head__deep-stairs-foot` | 0.56, -0.42 | 0.61, -0.44 | -0.019 | 0.441 → 0.387 | 86 → 89 | ok |
| entry | `door:cookhouse` | 0.16, -0.05 | 0.19, -0.05 | -0.004 | 0.840 → 0.810 | 66 → 67 | ok |
| exit | `door:cookhouse` | 0.33, -0.07 | 0.36, -0.07 | -0.004 | 0.671 → 0.635 | 66 → 68 | ok |
| exit | `seam:shelf-homes__quay-deck` | -0.37, 0.18 | -0.35, 0.18 | +0.002 | 0.632 → 0.646 | 58 → 59 | ok |
| exit | `seam:quay-deck__market-stalls` | -0.55, 0.00 | -0.54, -0.00 | -0.003 | 0.448 → 0.458 | 62 → 64 | ok |
| exit | `seam:quay-deck__pilot-cluster` | -0.83, -0.20 | -0.82, -0.20 | -0.009 | 0.173 → 0.176 | 68 → 70 | ok |
| exit | `seam:deep-stairs-head__deep-stairs-foot` | 0.40, -0.63 | 0.45, -0.65 | -0.026 | 0.375 → 0.349 | 85 → 88 | ok |

### `quay-east` — The Market

pos [48.852,27.52,20.92] → [48.877,27.358,20.92] · aim [57.924,13.003,15.357] → [57.948,12.84,15.357] · fov 35° · margin 0.1 · samples 26 → 32

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:quay-deck__market-stalls` | -0.04, -0.21 | -0.05, -0.22 | -0.010 | 0.786 → 0.776 | 112 → 113 | ok |
| entry | `seam:market-stalls__lockhead` | -0.16, -0.17 | -0.16, -0.18 | -0.009 | 0.829 → 0.820 | 108 → 109 | ok |
| entry | `seam:shelf-homes__market-stalls` | 0.11, 0.21 | 0.11, 0.20 | -0.006 | 0.793 → 0.799 | 102 → 103 | ok |
| exit | `seam:quay-deck__market-stalls` | 0.13, -0.32 | 0.12, -0.33 | -0.012 | 0.683 → 0.671 | 121 → 122 | ok |
| exit | `seam:market-stalls__lockhead` | -0.34, -0.14 | -0.34, -0.14 | -0.008 | 0.664 → 0.656 | 105 → 105 | ok |
| exit | `seam:shelf-homes__market-stalls` | 0.32, 0.41 | 0.32, 0.40 | -0.005 | 0.594 → 0.599 | 105 → 106 | ok |

### `lockhead` — The Lockhead

pos [82.818,29.997,23.015] → [84.015,32.052,24.091] · aim [73.591,15.23,15.262] → [73.507,15.236,15.262] · fov 35° · margin 0.1 · samples 44 → 48

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:market-stalls__lockhead` | 0.56, 0.17 | 0.50, 0.15 | -0.018 | 0.442 → 0.500 | 83 → 75 | ok |
| entry | `seam:lockhead__keepers-cottage` | -0.72, -0.68 | -0.62, -0.58 | +0.096 | 0.284 → 0.382 | 136 → 116 | ok |
| exit | `seam:market-stalls__lockhead` | 0.63, 0.23 | 0.57, 0.21 | -0.022 | 0.369 → 0.430 | 78 → 71 | ok |
| exit | `seam:lockhead__keepers-cottage` | -0.97, -1.06 | -0.82, -0.90 | +0.165 | -0.064 → 0.101 | 148 → 125 | **FIXED** |

### `cottage` — Keepers' Spur

pos [92.476,40.663,18.572] → [94.44,50.059,21.491] · aim [87.926,19.255,11.88] → [87.905,19.313,11.88] · fov 35° · margin 0.11 · samples 208 → 214

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:lockhead__keepers-cottage` | 0.14, 0.12 | 0.10, 0.09 | -0.032 | 0.855 → 0.898 | 83 → 59 | ok |
| entry | `seam:keepers-cottage__lock-five` | -0.38, -0.81 | -0.26, -0.54 | +0.272 | 0.186 → 0.458 | 103 → 69 | ok |
| entry | `seam:weave-huts__keepers-cottage` | 0.22, -0.76 | 0.15, -0.52 | +0.245 | 0.236 → 0.481 | 97 → 66 | ok |
| entry | `door:keepers-cottage` | -0.10, -0.74 | -0.07, -0.50 | +0.243 | 0.256 → 0.499 | 99 → 67 | ok |
| exit | `door:keepers-cottage` | -0.35, -0.76 | -0.24, -0.51 | +0.250 | 0.243 → 0.493 | 101 → 68 | ok |
| exit | `seam:lockhead__keepers-cottage` | 0.28, 0.26 | 0.20, 0.19 | -0.071 | 0.722 → 0.802 | 81 → 58 | ok |
| exit | `seam:keepers-cottage__lock-five` | -0.50, -1.36 | -0.33, -0.89 | +0.475 | -0.365 → 0.110 | 110 → 72 | **FIXED** |
| exit | `seam:weave-huts__keepers-cottage` | 0.40, -0.76 | 0.27, -0.52 | +0.243 | 0.236 → 0.479 | 95 → 65 | ok |

### `crossing` — The Crossing

pos [77.008,47.378,13.5] → [76.998,47.393,13.504] · aim [79.588,22.823,9.147] → [79.581,22.815,9.147] · fov 35° · margin 0.13 · samples 34 → 38

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:weave-huts__keepers-cottage` | 0.15, -0.20 | 0.15, -0.20 | +0.000 | 0.801 → 0.801 | 82 → 82 | ok |
| entry | `seam:weave-huts__keepers-cottage` | -0.14, -0.24 | -0.14, -0.24 | +0.000 | 0.762 → 0.762 | 81 → 81 | ok |
| exit | `seam:weave-huts__keepers-cottage` | 0.32, -0.18 | 0.32, -0.18 | +0.000 | 0.682 → 0.683 | 83 → 83 | ok |
| exit | `seam:weave-huts__keepers-cottage` | -0.30, -0.22 | -0.30, -0.22 | +0.000 | 0.702 → 0.702 | 80 → 80 | ok |

### `weave` — The Weave

pos [46.935,45.347,23.195] → [47.061,45.492,23.249] · aim [60.178,20.439,11.798] → [60.367,20.468,11.798] · fov 35° · margin 0.1 · samples 296 → 302

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:quay-deck__pilot-cluster` | 0.07, -0.08 | 0.09, -0.08 | -0.002 | 0.921 → 0.915 | 67 → 67 | ok |
| entry | `seam:weave-huts__moorage` | -0.70, -0.26 | -0.68, -0.27 | -0.002 | 0.304 → 0.316 | 61 → 60 | ok |
| entry | `seam:weave-huts__keepers-cottage` | -0.65, -0.21 | -0.64, -0.21 | -0.001 | 0.348 → 0.359 | 59 → 59 | ok |
| exit | `seam:quay-deck__pilot-cluster` | 0.14, 0.19 | 0.15, 0.19 | -0.002 | 0.812 → 0.814 | 66 → 66 | ok |
| exit | `seam:weave-huts__moorage` | -0.79, -0.37 | -0.78, -0.37 | -0.001 | 0.207 → 0.219 | 59 → 59 | ok |
| exit | `seam:weave-huts__keepers-cottage` | -0.71, -0.16 | -0.70, -0.16 | -0.001 | 0.294 → 0.304 | 56 → 56 | ok |

### `deep-stairs` — The Deep Stairs

pos [28.94,50.648,12.844] → [28.943,50.653,12.845] · aim [38.328,21.755,8.574] → [38.335,21.748,8.574] · fov 35° · margin 0.13 · samples 394 → 398

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:deep-stairs-head__deep-stairs-foot` | -0.07, 0.25 | -0.07, 0.25 | +0.000 | 0.752 → 0.752 | 62 → 62 | ok |
| entry | `seam:deep-stairs-head__deep-stairs-foot` | 0.08, -0.18 | 0.08, -0.18 | +0.000 | 0.818 → 0.818 | 69 → 69 | ok |
| exit | `seam:deep-stairs-head__deep-stairs-foot` | 0.05, 0.40 | 0.05, 0.40 | +0.000 | 0.604 → 0.604 | 62 → 62 | ok |
| exit | `seam:deep-stairs-head__deep-stairs-foot` | -0.11, -0.47 | -0.11, -0.47 | +0.000 | 0.528 → 0.528 | 69 → 69 | ok |

### `boatyard` — The Boatyard · **PINNED**

pos [37.6,25.4,8.5] → [37.6,25.4,8.5] · aim [14.4,30.4,3.4] → [14.4,30.4,3.4] · fov 35° · margin 0.1 · samples 112 → 112

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:winch-foot__slipway` | -0.27, -0.87 | -0.27, -0.87 | +0.000 | 0.129 → 0.129 | 140 → 140 | ok |
| exit | `seam:winch-foot__slipway` | -0.34, -1.15 | -0.34, -1.15 | +0.000 | -0.152 → -0.152 | 164 → 164 | **ground-off (unchanged)** |

### `waterfront` — The Waterfront — winch foot

pos [57.41,33.429,10.08] → [60.644,34.455,10.992] · aim [35.019,25.28,2.338] → [35.616,25.346,2.338] · fov 35° · margin 0.08 · samples 58 → 66

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:fish-dock__winch-foot` | -0.14, -0.76 | -0.10, -0.60 | +0.160 | 0.237 → 0.397 | 123 → 102 | ok |
| entry | `seam:deep-stairs-head__deep-stairs-foot` | -0.10, -0.07 | -0.07, -0.04 | +0.030 | 0.903 → 0.925 | 90 → 78 | ok |
| entry | `seam:deep-stairs-foot__fish-dock` | -0.32, -0.92 | -0.24, -0.72 | +0.201 | 0.080 → 0.281 | 134 → 109 | ok |
| entry | `seam:winch-foot__slipway` | 0.10, 0.09 | 0.10, 0.09 | +0.008 | 0.896 → 0.899 | 65 → 59 | ok |
| exit | `seam:fish-dock__winch-foot` | -0.20, -1.04 | -0.15, -0.81 | +0.232 | -0.042 → 0.190 | 141 → 114 | **FIXED** |
| exit | `seam:deep-stairs-head__deep-stairs-foot` | -0.28, 0.10 | -0.23, 0.11 | +0.008 | 0.724 → 0.774 | 99 → 85 | ok |
| exit | `seam:deep-stairs-foot__fish-dock` | -0.43, -1.20 | -0.32, -0.92 | +0.282 | -0.202 → 0.080 | 154 → 122 | **FIXED** |
| exit | `seam:winch-foot__slipway` | 0.18, 0.16 | 0.17, 0.16 | +0.001 | 0.820 → 0.831 | 62 → 56 | ok |

### `fishdock` — The Fish Dock

pos [43.659,50.761,9.252] → [43.652,50.513,9.199] · aim [54.893,27.727,2.385] → [54.8,27.656,2.385] · fov 35° · margin 0.08 · samples 56 → 62

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:tenant-shack__fish-dock` | -0.54, 0.03 | -0.55, 0.03 | -0.001 | 0.460 → 0.449 | 66 → 66 | ok |
| entry | `seam:fish-dock__winch-foot` | 0.43, -0.28 | 0.43, -0.28 | -0.004 | 0.568 → 0.573 | 87 → 88 | ok |
| entry | `seam:deep-stairs-foot__fish-dock` | 0.34, -0.20 | 0.33, -0.20 | -0.003 | 0.663 → 0.669 | 81 → 82 | ok |
| exit | `seam:tenant-shack__fish-dock` | -0.61, 0.09 | -0.62, 0.09 | +0.000 | 0.394 → 0.384 | 63 → 63 | ok |
| exit | `seam:fish-dock__winch-foot` | 0.61, -0.32 | 0.61, -0.33 | -0.004 | 0.390 → 0.393 | 89 → 90 | ok |
| exit | `seam:deep-stairs-foot__fish-dock` | 0.49, -0.23 | 0.49, -0.23 | -0.003 | 0.510 → 0.514 | 83 → 84 | ok |

### `cottage-steps` — The Keepers' Steps

pos [77.175,44.343,10.809] → [77.179,44.358,10.814] · aim [92.122,25.211,5.204] → [92.14,25.208,5.204] · fov 35° · margin 0.12 · samples 244 → 248

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:keepers-cottage__lock-five` | -0.04, -0.27 | -0.04, -0.27 | +0.000 | 0.735 → 0.735 | 83 → 83 | ok |
| entry | `seam:keepers-cottage__lock-five` | -0.09, 0.03 | -0.09, 0.03 | +0.000 | 0.909 → 0.910 | 78 → 78 | ok |
| exit | `seam:keepers-cottage__lock-five` | -0.07, 0.06 | -0.07, 0.06 | -0.001 | 0.925 → 0.926 | 77 → 77 | ok |
| exit | `seam:keepers-cottage__lock-five` | -0.03, -0.28 | -0.03, -0.28 | -0.001 | 0.719 → 0.718 | 83 → 83 | ok |

### `lockfive` — Lock Five

pos [51.16,35.567,10.382] → [51.089,35.64,10.431] · aim [75.728,26.625,4.824] → [75.875,26.619,4.824] · fov 35° · margin 0.08 · samples 300 → 308

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:weave-huts__moorage` | 0.06, -0.17 | 0.06, -0.17 | -0.003 | 0.835 → 0.832 | 84 → 84 | ok |
| entry | `seam:tenant-shack__fish-dock` | 0.21, -0.58 | 0.22, -0.58 | -0.002 | 0.423 → 0.421 | 94 → 94 | ok |
| entry | `seam:keepers-cottage__lock-five` | -0.20, -0.02 | -0.20, -0.02 | -0.003 | 0.803 → 0.805 | 51 → 51 | ok |
| entry | `seam:lock-five__north-landing` | -0.26, -0.20 | -0.26, -0.20 | -0.002 | 0.740 → 0.743 | 53 → 53 | ok |
| exit | `seam:weave-huts__moorage` | 0.11, 0.17 | 0.11, 0.16 | -0.004 | 0.834 → 0.838 | 79 → 79 | ok |
| exit | `seam:tenant-shack__fish-dock` | 0.24, -0.75 | 0.24, -0.75 | -0.001 | 0.252 → 0.251 | 104 → 103 | ok |
| exit | `seam:keepers-cottage__lock-five` | -0.21, 0.11 | -0.21, 0.11 | -0.003 | 0.792 → 0.794 | 49 → 49 | ok |
| exit | `seam:lock-five__north-landing` | -0.28, -0.17 | -0.27, -0.17 | -0.002 | 0.725 → 0.727 | 50 → 50 | ok |

### `north-landing` — North Landing

pos [120.599,30.301,6.011] → [120.982,30.456,6.24] · aim [99.616,27.352,0.728] → [99.092,27.38,0.728] · fov 35° · margin 0.11 · samples 32 → 34

| role | mark | old ndc | new ndc | Δndc y | old edge margin → new | charPx | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry | `seam:lock-five__north-landing` | 0.08, 0.05 | 0.08, 0.04 | -0.015 | 0.916 → 0.924 | 72 → 71 | ok |
| exit | `seam:lock-five__north-landing` | 0.10, 0.12 | 0.09, 0.10 | -0.014 | 0.884 → 0.898 | 68 → 67 | ok |

## 4. Advisory — the worst camera-vs-floor ownership mismatches

These are metres where the floor belongs to one shot and another shot's camera is live
(routes.json `mismatch`, ranked). Exit framing does not fix ownership; the question is
whether the LIVE camera can at least see the ground the player is walking on there.

Each span is sampled at 5 points along the map edge that generated it.

| edge | t | metres | camera up | floor owned by | span in frame under live cam (old → new) | min edge margin | min charPx | improved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `weave-huts__keepers-cottage` | 0.591..1 | 8.8 | `cottage` | `crossing` | 100% → 100% | 0.238 → 0.485 | 96 → 65 | yes |
| `deep-stairs-head__deep-stairs-foot` | 0.637..1 | 8.8 | `waterfront` | `deep-stairs` | 100% → 100% | 0.358 → 0.488 | 91 → 79 | yes |
| `quay-deck__pilot-cluster` | 0..0.483 | 6.6 | `quay-west` | `weave` | 100% → 100% | 0.173 → 0.176 | 65 → 66 | no |
| `keepers-cottage__lock-five` | 0.5..1 | 5.8 | `lockfive` | `cottage-steps` | 100% → 100% | 0.753 → 0.756 | 49 → 49 | no |
| `shelf-homes__market-stalls` | 0.5..1 | 5.5 | `quay-east` | `loop-stairs` | 100% → 100% | 0.603 → 0.608 | 102 → 102 | no |
| `shelf-homes__quay-deck` | 0.5..1 | 4.3 | `quay-west` | `loop-stairs` | 100% → 100% | 0.568 → 0.582 | 58 → 59 | no |
| `valley-gate__inn` | 0..0.428 | 4.2 | `gate` | `shelf-west` | 100% → 100% | 0.678 → 0.681 | 65 → 65 | no |
| `weave-huts__keepers-cottage` | 0..0.188 | 4.0 | `weave` | `crossing` | 100% → 100% | 0.293 → 0.304 | 56 → 56 | no |

8 of these 8 spans were ALREADY fully in frame under the live camera before the change: the ownership mismatch is a *timing* defect (the cut lands late), not a visibility one, so exit framing is not the lever for it — it only makes the late metres sit further inside the frame while they are walked. The lever is ownership/`cutOffset`, which is the coordinator's call and a separate tranche.

## 5. Totals

* exits with their ground off-frame — **before 5**, **after 1**
* fixed: `lockhead/seam:lockhead__keepers-cottage`, `cottage/seam:keepers-cottage__lock-five`, `waterfront/seam:fish-dock__winch-foot`, `waterfront/seam:deep-stairs-foot__fish-dock`
* still off-frame: `boatyard/seam:winch-foot__slipway` — every one of them on a PINNED shot, i.e. left off-frame BY RULING, not by the solver
* regressed: none
* flagged for taste review: `lockhead`, `cottage`, `lockfive`

## 6. Reproduce, and what the coordinator still has to move

```sh
node tools/cine_solve.mjs --check                 # the SHIPPED solve is unchanged
node tools/cine_solve.mjs --frame-exits \
     --out docs/qa/review/solve-proposal/dellhollow.cameras.solved.proposed.json
node docs/qa/review/solve-proposal/derive_delta.mjs
```

The solver change itself is unconditional and general: `solveCamera` now fits each shot
around its owned region + its ARRIVALS + **the centre of every seam band it is an exit
of** (both directions of every seam), so no future town can ship a shot whose own exit
is off-frame. Two flags govern it and both belong in `townmap/<town>.cameras.json`:

| flag | where | meaning |
| --- | --- | --- |
| `"pin": true` | a camera record | this frame is a human ruling: reproduce its authored `pos`/`aim` exactly and exclude it from the exit constraint. Requires `pos`+`aim`. |
| `defaults.frameExits: false` | the cameras file | the whole town opts OUT — a migration flag for a town whose backdrops are already baked. |

Because this tranche may not edit `cameras.json`, both currently live in the sidecar
`public/townmap/dellhollow.cameras.pins.json`, which the solver merges onto the camera
records. **The coordinator should move them into `cameras.json`** (`"pin": true` on the
boatyard camera; `"frameExits": false` in `defaults`, deleted when the re-bake lands) and
delete the sidecar — the solver only ever reads `cam.pin` / `C.D.frameExits`, so nothing
else changes. Turning exit framing on for Dellhollow means re-solving the shipped
`cameras.solved.json`, re-running `tools/scenegraph_derive.mjs`, and re-baking the
8 plates listed in §1 — deliberately NOT done here.
