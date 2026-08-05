# Scene Layout — the concept-driven pipeline

Status: **method proven via the square pilot (2026-07-28); pilot transcription
awaiting director judgment on branch `concept-driven-square-layout`; full
13-scene rollout pending that call.**

## Why this exists

Agent-placed layouts optimize for collision safety, not composition — the
result is "composition-by-BFS": every prop reachable, nothing *arranged*.
The director's verdict on those layouts: "props placed randomly and
scattered… no real consideration of where things should actually be."
The fix follows this project's most repeated lesson (**showing beats
telling** — placeholder boxes beat spatial prose, master images beat style
descriptions): give the layout work a picture to imitate.

Precedent that proved it before we named it: `dellhollow-master-6b.png`
drove every Dellhollow design decision; the aspirational illustration from
the first iso exploration showed single-shot generations compose (density,
focal hierarchy, negative space) far better than coordinate-reasoning
agents.

## The pipeline (three steps)

1. **Concept.** Generate 1–2 full-scene illustrations per scene: prompted
   with the scene's fixed anatomy (buildings, hero props, exits), its story
   needs, the *available catalog vocabulary by name*, composition language
   (focal hierarchy, clustered density with breathing room, framed edges),
   and the verbatim style-B block from `specs.json`. The concept is
   **composition authority only** — it never ships, is never sliced. (The
   iso-era concept sheets lived in `public/assets/iso/refs/`, deleted with
   the iso prototype 2026-08-05 — in git history before commit 7656b60.)
2. **Transcription.** Rebuild the scene JSON to match the concept's
   **arrangement, not pixels**, using only existing catalog blocks:
   - copy where it clusters, how it frames the focal anchor, where
     negative space breathes;
   - **touching groups, never scattered singletons** (a haybale AGAINST a
     stall's leg, crates BESIDE the cart);
   - keep the scene's functional contract intact (same doors, same exits,
     spawn safety);
   - props the concept invents but the catalog lacks → append to
     `docs/prop-wishlist.md` and substitute nearest-equivalent. The
     wishlist seeds the next (cheap, gated) art round.
3. **Gates as gates.** BFS trigger/spawn connectivity, walkable sweeps,
   and zero-error boots run as **post-checks on the designed layout** —
   demoted from design driver back to safety net.

## Pilot results (the square)

Winning concept: `square-concept-B.png` (deleted with `assets/iso/`, in
git history before 7656b60) — chosen
over candidate A because its diamond symmetry (buildings at four corners,
roads at the four cardinal gaps, open center) transcribes almost 1:1 onto
the iso grid. Prompt clauses that did the work are recorded in the pilot
agent's report; the load-bearing ones: the plinth "commands the exact
CENTER… the brightest thing in frame," dressing "HUDDLES INTO TOUCHING
GROUPS around anchors, never scattered singletons," plaza center kept
"OPEN negative space so the flame reads clearly."

What the concept taught that the scatter lacked (the five arrangement
moves): a sacred ring (benches/braziers/lampposts *facing* the plinth on a
centered cobble diamond) instead of loose furniture; the market as one
dense lane instead of floating stall columns; dressing huddled into
touching clusters; deliberate open space so the hero reads; framed edges
(bunting posts, corner trees, a foreground tree).

Three-way comparison (concept / old / new) lived at the top of
`public/iso-review.html` (deleted with the iso prototype, Bet 6 2026-08-05);
old layout was preserved as `review/world2-03-square-old.jpg`.

**Orchestrator critique of the pilot transcription (fix before shipping):**
the thatch cottage drifted off its corner and crowds the plaza's front
edge, partially screening the ring it exists to showcase (a knock-on from
a correct occlusion fix — see caveat below); the market lane thinned to
three stalls (denser in both concept and brief); breathing room overshot
into barren margins left and lower-right. All placement-level, none
method-level.

## Caveats and standing rules

- **Iso-projection nudge (~1 in 4 scenes):** the flat concept can't
  predict grid-to-screen quirks — e.g. the SE grid corner maps to
  screen-bottom-center, so a world-centered hero can be occluded by a
  corner building's roof. Budget one verify-and-adjust loop per scene;
  the fix must preserve the concept's composition intent, not just clear
  the occlusion (the pilot's cottage crowding came from fixing occlusion
  without re-checking the frame).
- **Settled-capture rule (hard, engine-wide):** every screenshot only
  after `G.fade.mode === 'idle' && G.fade.a === 0` plus ~1s settle. Three
  separate agents shipped dark mid-fade captures before this became law.
  Also: hidden tabs pause rAF — foreground the tab if the fade freezes.
- **Known art nit:** a rod/string artifact protrudes from the guildhall
  wall across two independent layouts — it belongs to the building sprite
  or its bunting attachment, not to placement. On the art-nit list.

## Scaling estimate (13 scenes)

~2 concept generations per scene (≈26 images, ~£1 total); the real cost
is transcription + verify-adjust, ~1–2 h/scene (interiors cheaper —
shell-bounded, fewer props). Full pass ≈ 2–3 days of agent time. The
pilot's validator pattern (`build_square.mjs`-style offline check with
real footprints, then in-engine BFS + settled captures) templates per
scene.

## Open decision (director)

(a) fix-iterate the square pilot, re-judge, then scale; (b) accept
direction from the comparison page — fix the square and launch the full
13-scene wave together; (c) review the page first. The pilot branch holds
the new square until this call is made.
