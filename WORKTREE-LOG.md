# wt/transitions — IN-PLACE SCENE SWAPS

Branch `wt/transitions` off `migration/3d-hybrid`. Isolated worktree; the coordinator
merges after review. Nothing here was pushed or merged by me.

## What changed

`transitionTo()` is still the only place a scene change happens and its signature and
return value are unchanged. Its **body** changed: a cross-scene edge no longer calls
`location.assign()`. It now disposes the old bundle, loads the new one in the same
document, and tells the modules through one event.

The original comment said the full page load was deliberate — "state-free, robust, no
leaked state, correct by construction". That robustness was **free**. The swap has to
buy it, and it pays in three places:

| price | mechanism |
| --- | --- |
| no leaked GPU memory | `sceneDispose()` hands every geometry/material/texture back to three.js, verified against `renderer.info` |
| no leaked async state | `EPOCH` — a response that arrives for a scene the player has left is dropped **and disposed** |
| no leaked module state | one documented event, `eb-scene`, handled by each module |

Plus: `?reload=1` restores the old path completely, and any throw in the swap falls
back to `location.assign(url)`. The old path is the floor, not a memory.

## The module event contract

`window` CustomEvent **`eb-scene`**, fired **once** per scene change, **after** the new
bundle is fully built (collide/walkRef/allMeshes rebuilt, spawn chain run, camera and
depth applied, one frame rendered) and **before** the veil comes down.

```js
detail = { scene, prev, spawn:[x,y,z], edge, kind, inPlace:true }
```

`history.replaceState` runs **before** the dispatch, so a handler reading
`location.search` reads the truth. **Not** fired on a fresh page load: every module's
load-time self-arming path is untouched, which is exactly what keeps `?reload=1` and
deep links working. A handler is always "do again what you did at load time".

| module | handler | why |
| --- | --- | --- |
| `music.js` | `Music.scene(key)` | same track → `start()` sees the live voice and returns; the AudioContext, the GainNode and the AudioBufferSourceNode are **never touched**. Different track → normal 1.5 s crossfade. No sessionStorage dance either way. |
| `encounters.js` | `boot()` (idempotent) + `rescene('scene')` | re-baseline `last` (else the door reads as travel between two worlds), re-grace (a doorway is never an ambush), move the respawn anchor to the arrival. Counters survive: they measure a session. |
| `shop.js` | `registerPrompts()` | re-reads `?scene=`, re-resolves the shop and the counter pad against the new bundle's `SIM.pad`. |
| `route_overlay.js` | drop + dispose its own `THREE.Group`, reload for the new scene | play3d only disposes what play3d added; the overlay owns its geometry. Overlay on/off is a view preference and survives. |
| `game_state.js` | **nothing** | GS is page state and persists untouched — no save, no load. |

## Verification

All in this worktree, server on `:8123`, `--nomusic` deliberately **not** used (music
continuity is under test; the run is muted at the source instead).

| oracle | before | after |
| --- | --- | --- |
| `tools/slice_test.mjs` | 514 / 0 | **514 / 0** |
| `tools/seam_walk.mjs` | 9/9 | **9/9** |
| `tools/cine_test.mjs` | 636 / 0 / 3 warn | **636 / 0 / 3 warn** |
| `tools/transition_test.mjs` (new) | — | **160 / 0** |
| `tools/transition_test.mjs --reload` (new) | — | **32 / 0** |

No harness needed updating: all three oracles are file-based node tests, so they were
never sensitive to the transition mechanism.

### Memory table (24 mixed transitions)

Every repeat visit to a `(scene, shot)` has **identical** geometry/texture/mesh/material
counts. 12 repeat visits across 12 distinct states, zero drift.

```
   door  ->scene            shot            ms   geoms   texs  meshes  mats  art
      0  del-inn-int       -              2175    233      6     228   523    0
      1  del-cine          shelf-west     2439    491      7    2332  4817    3
      2  del-item-int      -              2062    153      6     182   410    0
      3  del-cine          shelf-west     2824    491      7    2332  4817    3
      4  ow-valley         -              6409     44     52      39    97    0
      5  del-cine          gate           2457    346      7    2332  4817    2
      9  del-cine          shelf-east     2005    651      7    2332  4817    3
     11  del-cine          quay-west      2415    819      7    2332  4817    5
     12  del-cottage-int   -              1682   1029      6    1033  2107    0
     13  del-cine          cottage        2223    362      7    2332  4817    4
     16  del-inn-int       -              1927    233      6     228   523    0   <- = door 0
     17  del-cine          shelf-west     2099    491      7    2332  4817    3   <- = door 1
     21  del-cine          gate           2359    346      7    2332  4817    2   <- = door 5
     23  del-cine          cottage        2069    362      7    2332  4817    4   <- = door 13
```

**The baseline is per (scene, shot), not per page — and that is a finding, not a
convenience.** `renderer.info.memory.geometries` counts geometries that have been
*uploaded*, and a geometry uploads on its first render. In a town of sixteen fixed
cameras the number is a property of **which shot is up**: entering Dellhollow at the
valley gate uploads 346 shared geometries, at shelf-west 491, at quay-west 819.
Comparing across shots would report a 145-geometry "leak" that is nothing but a
different camera. The first draft of this test did exactly that and failed.

### Cost

| path | door-to-door, incl. both 350 ms fades |
| --- | --- |
| in-place swap | median **2.1 s**, min 1.4 s, max 6.4 s (`ow-valley`) |
| full reload (`?reload=1`) | median **2.6 s**, min 1.7 s, max 4.2 s |

In-page work, excluding the fades: total median **873 ms**; **dispose median 16 ms**
(max 18 ms — the price the reload did not pay, and it is negligible); load median
870 ms (fetch + parse + BVH + spawn — the reload paid this too).

So the win is real but **modest in wall-clock**, and the honest headline is not speed:
it is that the AudioContext survives, GS survives, and there is no load flicker or
module re-init. See "the swap is not yet much faster" below.

## Known limitations

1. **The swap is not yet much faster than the reload it replaces.** ~870 ms median of
   in-page work dominates, and essentially all of it is the GLB. Two reasons, both
   fixable and both out of scope tonight:
   - `scene.glb?v=' + Date.now()` **defeats HTTP caching on every swap**. It was
     harmless under the reload (a new page had a cold cache anyway); in place, it means
     re-downloading a bundle the tab fetched two minutes ago. Removing the cache-buster
     (or keying it to the bundle's `meta.json` export stamp) is the single biggest win
     available, but it interacts with the live-refresh `townwalk` workflow that relies
     on cache-busting to pick up re-exports — a deliberate call, not a drive-by.
   - The **fade-out and the load are serial**. Fetching the new bundle *during* the
     350 ms fade-out would take ~350 ms off every door for free; rule (3) still holds
     because installing (not fetching) is what must wait for black. This needs
     fetch/install to be split in `sceneLoad()`, which is a real refactor.
2. **`ow-valley` costs ~4 s of load** (52 textures, large terrain GLB). Same on both
   paths; it is the bundle, not the mechanism.
3. **In-scene camera cuts do not rewrite the URL.** Unchanged from before — the local
   handoff path was not touched — so F5 after a cut returns you to the door you came in
   by, not the shot you cut to. `?scene=` and `?sx/sy/sz` stay truthful, which is what
   constraint (5) asks for; going further would mean `replaceState` on every camera cut.
4. **`?reload=1` is opt-in per journey.** It propagates through `sgUrl`, so the whole
   journey stays on the old path once chosen — but there is no in-game toggle.
5. **The dev menu still uses `location.reload()`** for model/walklock/ghost changes
   (those are genuinely load-time flags). Left alone deliberately.

## Pre-existing defect found, NOT caused by this work

**Dellhollow's weapon-shop exit lands the player fully occluded.** Leaving the weapon
shop arrives at `[35.274, 19.07, -6.925]` under shot `shelf-west`, where the shot's own
baked depth map hides the character completely: 1417 px drawn, **0 px** survive the
depth test.

Verified to be a **content/data defect and not a regression**: loading that exact URL on
a **fresh page load** (no swap involved) gives byte-identical numbers. The runtime
handles it as designed — the presence marker ring is showing — so the player is marked,
not lost. But an arrival point behind an occluder is worth a look from whoever owns the
scene-graph spawn points. `tools/transition_test.mjs` now asserts the honest contract:
*drawn, and either visible or properly marked.*

## Files

- `public/play3d.html` — the swap (`sceneParams`/`sceneLoad`/`sceneDispose`/`sgSwap`/
  `EPOCH`), the depth-quad page singleton, the single-rAF guard, `SIM.scene/gpu/
  transitions/door`.
- `public/js/music.js` — `eb-scene` handler; comment block 2 amended (it described the
  reload as the only path).
- `public/js/encounters.js` — `Encounters.rescene()` + `eb-scene` handler.
- `public/js/shop.js` — `eb-scene` handler; reset moved before the not-a-shop early
  return (a stale prompt used to survive leaving a shop).
- `public/js/route_overlay.js` — `eb-scene` handler + self-disposal.
- `tools/transition_test.mjs` — new. Drives real Chrome over CDP, no new dependency.

## Harness hygiene

The suite reuses **one** Chrome profile dir (`$TMPDIR/transition-test-profile`) and
`rm -rf`s it from a `process.on('exit')` trap, so a failing run cleans up too. An
earlier draft minted one per pid at ~500 MB each and filled the machine's disk — fixed,
verified (no profile left after any run).
