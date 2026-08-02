# nav-eval predictions — Emberbrook's first dressed plates (2026-08-01, plate-bake lane)

**Registered BEFORE the judge ran.** The handover requires it and the reason is not
ceremony: nav-eval's output is a number between 0 and 1 that a reader can rationalise in
either direction after the fact. A prediction written first turns the run into a test of
a belief instead of a source of one. Git's timestamp on this file is the proof of order.

Predictions are made from the SHIPPED plates (I have looked at woodroad, square and their
luminance histograms) and from nothing else — no route data, no walk network, no map.

| shot | predicted escape rate | confidence | the reasoning being tested |
|---|---|---|---|
| `woodroad` | **0.0 – 0.25** | high | The frame is functionally black: median L=6.7, max L=52.3, 99.7% of pixels under L=25, and NO light source anywhere in it. A context-free viewer has almost no path affordance to read. The dirt road is faintly traceable from the clearing toward upper-right and the waystone is clipped at the top edge — if anything scores, it will be that road. |
| `square` | **0.45 – 0.70** | medium | Genuinely lit — the Heartlight, the lamp ring, benches and stalls give real structure, and max L=254.9 means there ARE highlights to navigate by. But 75.4% of the frame is still under L=25 and the camera is high and near-aerial, which flattens the read of which gaps are exits. |
| `gatefield` | **0.0 – 0.25** | high | Not yet baked when this was written. Predicted low on the grade doc's own numbers: gatefield measured 0.18–0.25x of golden hour, the darkest shot in the table, and it is canon that "nobody's warmth reaches the Old Gate" — it carries no lamp by ruling. |

## What would falsify the reading behind these numbers

The belief under all three is **legibility follows the light sources, not the exposure**
— the same claim the sky ladder produced when tripling the sky moved woodroad's max from
32.8 to 51.3 and bought no legibility at all.

* If `woodroad` scores materially ABOVE 0.25, then ground-plane geometry alone carries a
  route without any practical in frame, and the argument for adding a light to the
  opening shot is weaker than the luminance numbers suggest.
* If `square` scores BELOW 0.45 despite having the town's only real light sources, the
  problem is composition (camera height / exit legibility), not the grade — and no
  lighting change would fix it.
* If `gatefield` scores near `square`, darkness is not what drives this metric and the
  whole premise above is wrong.

Noise is +/-0.20 per shot at N=5, so these run at **N=10** and the judge stays PINNED.

---

## SCORED 2026-08-02 — two of the three falsifiers fired

Runs: `run-emb-town-n10` (all 11 shots, N=10) and `run-emb-square-n10` (square alone,
N=10). Judge pinned `gemini-3.6-flash` as required. Town score 0.536, 4 of 11 >= 0.80.

| shot | predicted | measured | verdict |
|---|---|---|---|
| `woodroad` | 0.0–0.25, HIGH | **1.00** | wrong, by the whole range |
| `square` | 0.45–0.70, medium | **0.15** (0.10 and 0.20 over two independent N=10 runs; N=20) | wrong, below the band |
| `gatefield` | 0.0–0.25, HIGH | **0.00** | right |

**The belief under all three — "legibility follows the light sources" — is falsified.**
`woodroad`, the frame this file called functionally black with no light source anywhere in
it, got **ten of ten** naive readers out. And `gatefield` (0.00) does score near `square`
(0.15) while the darkest plate in the town scores 1.00, which is this file's own third
falsifier: darkness is not what drives this metric. No lighting change would have moved
`square`, and the case for adding a light to the opening shot is weaker than the luminance
table suggested.

`square`'s miss is not composition either — the second falsifier's stated alternative.
`--judge oracle-world` (ground-truth world points handed straight to the walker: no image,
no judge, no plate) is **0.00 on `square`** and 0.727 town-wide. The designed route through
Festival Square ends inside the Heartlight, which stands on the plaza landmark's own centre
point and has its footprint cut out of the plaza's walk floor. The plate is not what fails
this shot; **the walk network is** — 206 m2 of the r14 disc is unwalkable and 77.4 m2 of
that has nothing standing on it. Full measurement, instruments and costed fixes:
`docs/qa/DAYLOG.md`, 2026-08-02 entry.
