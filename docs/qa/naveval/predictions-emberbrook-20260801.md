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
