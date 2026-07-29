# Emberbrook → 3D FF-Hybrid migration

Living plan + progress log for re-architecting the renderer from painted-2D backdrops to
the **pre-rendered-3D "FF-hybrid"** system (see the prototype in `../rpg-3d/` and its
`docs/TARGET_SYSTEM.md`). Working on branch `migration/3d-hybrid`; `main` (fully pushed to
`origin`) is the restore point. No back-compat: deprecated art/code is deleted **per scene
as it's migrated** (never wholesale up front — that would leave the game broken mid-flight).

---

## Guiding principle
Replace **how the world is drawn**, preserve **everything else**. The engine is cleanly
seamed: keep the entity model, collision, story/cutscene glue, exits, HUD, and
display-authoritative multiplayer; swap only the inside of the render seam.

## The four architecture decisions
1. **Orthographic pre-render.** The camera pans/zooms within the backdrop to frame both
   couch players. A perspective pre-render can't pan without parallax error; an ortho one
   pans as a pure 2D translation, and real-time 3D characters composite correctly through a
   matching ortho camera. → preserves `Field.updateCamera`, adds true depth occlusion.
2. **Geometry-derived walkmask.** Bake the 336×192 `mask.png` from the Blender geometry
   (raycast) instead of flood-painting. → `Field.walkable`, movement, exits, `navGate` all
   unchanged; the mask stays "collision authored separately, simpler than the art."
3. **WebGL world layer + existing 2D HUD.** Replace the *body* of `Field.draw` with a
   Three.js layer (stylized bg + invisible depth geometry + characters). Keep
   `Field._lastView` / `Field.worldToScreen` exactly → the whole 2D HUD (dialog, markers,
   prompts, name tags, choice cards) is untouched.
4. **Pluggable characters** bound to the existing entity contract
   (`{char,x,y,dir,moving,animT,h,tint,hidden,alpha,lightCarrier}`): each character is
   either a **3D model** (Rodin→Mixamo) or an **HD-2D billboard** (existing sprite sheet),
   decided per character. Both occlude via the depth buffer.

## What a migrated scene is (the bundle)
Per scene folder `public/assets/scenes/<key>/`:
| File | Source | Role |
|---|---|---|
| `stylized.png` (+ per state) | Blender ortho render → nano-banana | shipped background |
| `scene.glb` | Blender glTF (invisible/depth-only at runtime) | occlusion + collision-source |
| `mask.png` | raycast bake from `scene.glb` | 336×768→336×192 `Field.walkable` grid |
| `scene-cam.json` | Blender export | ortho affine: backdrop-px ↔ 3D ground (place entities) |
Exits / lamps / plates / spawns stay authored in **backdrop pixels** in the chapter file —
unchanged. States become either re-renders or the cheap tint-grade we already have.

## Seam mapping (old → new)
| Current (2D) | New (3D FF-hybrid) |
|---|---|
| `Field.draw` paints backdrop PNG + y-sorts sprites | Three.js: draw `stylized.png`, depth-write `scene.glb`, render characters with GPU z-test |
| occlusion = y-sort / (unused) occluders | GPU depth buffer (real per-pixel) |
| `Field.walkable` ← flood-painted `mask.png` | `Field.walkable` ← **geometry-baked** `mask.png` (same format) |
| sprite from sheet (`sprites2.js`) | 3D mesh **or** billboard, per entity |
| `viewH/charH` in backdrop px, perspective-free 2D cam | same values drive an **ortho** Three camera pan/zoom |
| states = duplicate PNG + tint | re-render per state, or keep tint-grade |

## Coordinate reconciliation
World stays **backdrop pixels** (1344×768, y = depth). The ortho render fixes an affine
`backdrop-px (x,y) ↔ 3D ground point`; exported in `scene-cam.json`. Runtime places each
entity's mesh/billboard at that ground point; the ortho Three camera uses the same pan/zoom
as `Field.updateCamera`. So entities keep their existing `x,y`, exits/spawns keep their
coords, and nothing in movement/story needs reprojection.

## Scene-authoring workflow — THE TEMPLATE (`tools/scenekit.py`)
Every scene is authored the **same way**, via the reusable kit — no bespoke per-scene code.
A scene script is short and declarative:
```python
import sys; sys.path.insert(0, '<repo>/tools')
import importlib, scenekit; importlib.reload(scenekit); from scenekit import SceneKit
K = SceneKit('square3d')          # collection + blockout materials + ortho cam + light
K.walkpath_disc(r=13)             # 1. WALK-FIRST: author the walkable area
K.heartlight(0,0); K.cottage_ring(11.5, 8); K.lantern_ring(); K.stall(6,-9,20)   # 2. playable scenery
K.fill_town(r0=15, r1=28, count=86); K.trees(count=46); K.landmark(-8,24)         # 3. WORLD-FILL
K.set_ortho(scale=42)
K.export()                        # 4. background.png + mask.png + scene.glb (ATOMIC, same cam)
```
Then: `node tools/genart.mjs .../stylized.png --ref .../background.png --ref .../ref.png "<style>"`.
The kit owns: blockout palette (procedural — no external-texture dependency), primitive +
building + fill builders, walk-first mask derivation, ortho camera, and the atomic bundle export
(render + glb-of-playable-core-only + walkmask, glTF log suppressed).
**Rule: if a scene needs something the kit lacks, extend the kit — never patch per-scene.**
New scene *types* (interiors, roads, gorges) add builders to the kit as they're first needed.

## Scene design principles (apply to every scene)
- **Walk-first.** Sketch the intended **walkable path/area first** in Blender (a flat
  `walkpath` region — the plaza + connecting streets the player actually uses), then build
  all scenery *around and bordering* it. The `mask.png` derives from that authored walkpath,
  so playability is intentional, not accidental. (Mirrors the old `tools/walkfirst.mjs` idea.)
- **World feels large.** The playable core is small; the *visible* world must be big. Fill
  everything beyond the playable ring with **non-collidable set dressing** — a dense town
  receding into distance, trees/forest, terrain, distant landmarks (spire/tower) — plus
  atmospheric haze. Rough background geometry is enough; the stylization pass fleshes it out
  (see `square3d`: ~40 background houses + trees → a whole misty town). **No empty space.**
- **Redesign freely.** Treat old 2D scenes as narrative briefs (mood, POIs, exits), not
  layouts to trace — rebuild for depth.

## Per-scene migration recipe (mechanical once tooling is in)
1. **Sketch the `walkpath`** (walkable area/streets) — flat, intentional.
2. Build the playable scenery bordering the path; then **fill the surroundings** densely
   (background town/forest/terrain + haze) so the ortho frame is full.
3. Set the **ortho** camera to frame the scene into 1344×768.
4. Render `background.png` (transparent) + export `scene.glb` (+ ortho camera) atomically.
5. `genart.mjs` → `stylized.png` (concept `ref.png` + shared style prompt for cohesion).
6. Bake `mask.png` from the `walkpath` (screen-space through the ortho cam); run `navGate`.
7. Point the chapter scene def at the bundle; keep exits/lamps/spawns.
8. Delete the scene's old painted PNG(s) once it passes.

---

## Scene inventory & priority (16 implemented)
Hubs first (highest play value), then spokes, cutscene-only last.
| Scene | Chapter | Type | States | Priority | Status |
|---|---|---|---|---|---|
| dellhollow | 2 | hub | day/night | **P0 pilot** | in progress (prototype exists) |
| square | 1 | hub | festival/gray | P1 | todo |
| lanternstead | 3 | hub | 4 states | P1 | todo |
| stairs | 2 | spoke | day/night | P2 | todo |
| lockfive | 2 | spoke | dim/night | P2 | todo |
| cottage | 2 | interior | dusk/night | P2 | todo |
| forest,entrance,interior,lane | 1 | spokes | 1 | P2 | todo |
| road, lanternstead-int | 3 | spoke/interior | — | P3 | todo |
| descent | 2 | spoke | 1 | P3 | todo |
| vista, landing | 2 | cutscene-only (no mask) | — | P3 | todo |

~8–10 more locations (Ch4–10) are outline-only — new builds, not migrations.

## Phasing
- **Phase A (now):** renderer integration + Dellhollow pilot playable in the real engine.
- **Phase B:** migrate the two other hubs (square, lanternstead) → proves variety + states.
- **Phase C:** batch the spokes/interiors using the settled recipe + kit.
- **Phase D:** cutscene-only scenes, character roster (3D vs HD-2D per cast member), cleanup
  (delete the old 2D art pipeline `tools/*` + `iso/` POC once nothing references them).

## Open decisions for review
- **Characters:** HD-2D (reuse 2D cast) vs 3D (Rodin→Mixamo per character) vs mix. Prototyped both.
- **States:** re-render per lighting state (best) vs keep cheap tint-grade (fast). Likely mix.
- **Renderer home:** Three.js layer beside the 2D canvas (chosen) — revisit if perf/complexity bites.

---

## PROGRESS LOG (autonomous session)
- [x] Verified `main` pushed to origin (safe); created `migration/3d-hybrid` branch.
- [x] Wrote this plan + `../rpg-3d/docs/TARGET_SYSTEM.md`.
- [x] **Validated ortho pre-render** (decision #1) — dellhollow re-rendered orthographic; pans without parallax.
- [x] **Pilot scene bundle** `public/assets/scenes/dellhollow3d/`: `background.png`, `stylized.png`
      (nano-banana), `scene.glb` (347 meshes + ortho camera), `mask.png` (walkable=white, screen-space
      through the same ortho cam → drops into `Field.walkable`).
- [x] **Verified in the game repo**: `public/test3d.html` (+`public/lib/three.min.js`,`GLTFLoader.js`)
      loads the bundle with the GLB's ortho camera → painterly backdrop + invisible depth geometry +
      capsule with raycast collision + **correct depth occlusion**. This is the core of `render3d.js`.

- [x] **Reusable template** `tools/scenekit.py` — walk-first walkpath + building/fill/tree/
      tower/courtyard/well builders + ortho cam + atomic `export()` (bg+mask+glb). New scene
      *types* extend the kit (never per-scene ad hoc).
- [x] **Generalized runtime** `public/play3d.html?scene=&char=` — loads any bundle + HD-2D char.
- [x] **3 hub scenes migrated via the template** (concept→3D→stylized, walk-first, world-filled):
      `dellhollow3d`, `square3d` (festival square + full background town), `lanternstead3d`
      (Order waystation — proved the kit scales to a new scene type).

- [x] **10 / 16 scenes migrated via the template** (concept→3D→stylized, walk-first, world-filled):
      dellhollow3d, square3d, lanternstead3d, road3d, cottage3d, forest3d, entrance3d, lane3d,
      gate3d (deliberate `walkpath_poly` route + mask-verified), interior3d.
      Kit builders now cover: town/cottage/ring, tower+great-lantern/courtyard/well, road/lamp,
      interior room+furniture, waystone, walkpath disc/rect/strip/**poly**, exit_marker, fill/forest.
- [ ] Remaining 6: lanternstead-int (interior, kit-ready), vista + landing (cutscene backdrops,
      no walkmask), stairs (needs scaffold/stilt builders), lockfive (dark lock-chamber interior),
      descent (gorge switchback — needs cliff/terrain builders). Extend the kit for the last 3 types.

- [x] **CH1 + CH2 FULLY MIGRATED (13 scenes)** — the user's focus. All via the template, with
      **interesting walk-first paths** (irregular plazas, winding trails, branching/forking streets,
      switchbacks, gantry ledges — no plain circles/lines) and world-fill:
      - Ch1: forest3d, entrance3d, interior3d, lane3d, square3d, gate3d
      - Ch2: dellhollow3d, descent3d, vista3d, cottage3d, landing3d, lockfive3d, stairs3d
      (Ch3 — road3d/lanternstead3d/lanternstead-int3d — built earlier; deprioritized per user, left as-is.)
- Path-quality pass: earlier scenes' lazy disc/strip walkpaths were **redesigned** (square,
  forest, lane, entrance) into unique routes; mask-checked for connectivity.

### Verified: full FF-hybrid + scalable template + all Ch1&2 scenes done in the target repo.
### Remaining: wire the runtime into the live 2-player engine (needs controllers); polish; Ch3/Ch4+ later.

## NEXT (in-game integration — best done with your 2-player test setup)
1. **`public/js/render3d.js`** — promote `test3d.html`'s logic into a module:
   `Render3D.init(canvasEl, sceneBundle)`, `.setView({camX,camY,viewH})`, `.setEntities(list)`, `.frame()`.
   - Character per entity: HD-2D billboard (existing sheet) or 3D model, placed by **raycasting the
     entity's backdrop-px down the ortho camera to the visible ground** (handles the visual tiers while
     gameplay stays 2D on the mask).
2. **Hook `Field.draw`** (`field.js`) behind `Field.mode3d` (per-scene flag): when on, draw the WebGL
   world layer under the existing 2D canvas; keep `Field._lastView`/`worldToScreen` so the entire HUD
   is untouched. Old 2D scenes keep working during migration.
3. **Camera-pan alignment**: map `Field.updateCamera`'s `camX,camY,Z` to the ortho camera's frustum
   window so bg + geometry + HUD stay locked as it pans to frame both players. (Open item — the one
   piece test3d.html doesn't yet exercise; verify against a scene that scrolls.)
4. **Wire the pilot as a real scene**: point a `dellhollow3d` scene def at the bundle (states/exits can
   reuse dellhollow's), boot the game, verify 2 players + collision + exits + dialog + HUD.
5. **Characters**: drop vesper in (HD-2D sheet is proven in `../rpg-3d/web/play_hd2d.html`; Rodin-3D
   mesh is in `../rpg-3d/assets/vesper/` awaiting Mixamo rig).
6. Then batch the other scenes via the recipe; delete each scene's old 2D art as it's migrated.

## Files added this session (on `migration/3d-hybrid`)
- `MIGRATION.md` (this)
- `public/assets/scenes/dellhollow3d/{background,stylized,mask}.png`, `scene.glb`
- `public/test3d.html`, `public/lib/{three.min.js,GLTFLoader.js}`

---

## QA sweep + architecture correction (2026-07-28) — collision is 3D raycast, NOT the 2D mask

Ran a walkmask connectivity audit across all Ch1/Ch2 bundles (flood-fill of `mask.png`, with a
component-overlay visualization over each backdrop). Two classes of result:

- **Flat scenes** (square/forest/lane/entrance/gate courtyard): the walkpath masks as one large
  connected region plus a few tiny fragments where set-dressing (trees, waystones, stalls) nicks the
  path, and thin path-ends at the scene edges. Cosmetic — the raycast collision crosses them fine
  (square3d verified fully walkable: plaza + all 3 branch streets).
- **Vertical / scaffold scenes** (stairs3d, and by extension lockfive3d + the whole Dellhollow town):
  **a staircase projects top-down to ONE DISCONNECTED STRIP PER TREAD.** stairs3d masks as ~6 floating
  islands (lower landing, 6 tread strips, upper platform — all separate components). See
  `scratchpad/ov_stairs3d.png`.

### Consequence — corrects Decision #2
Decision #2 ("geometry-derived 2D walkmask drops into `Field.walkable`") is **wrong for any scene with
vertical structure**. A mask-lookup engine makes stairs unclimbable → fatal for the scaffold scenes,
which are the whole point of Dellhollow (the hardest / most-wanted scene).

**Corrected architecture:** movement collision for 3D scenes is resolved by the **3D raycast over the
invisible depth geometry** — `Render3D.resolveMove(pos, dx, dz)` (ported from the proven
`play3d.html` `ground`/`wall`/`step`; handles multi-level climbs AND flat ground; verified). The engine
calls `resolveMove` in place of a mask sample. `mask.png` is retained only as an optional coarse hint
(minimap / far-AI pathfinding), never as the movement authority.

Wiring note for `field.js`: for `Field.mode3d` scenes, replace the `Field.walkable(x,y)` tile test in
the movement step with `Render3D.resolveMove`, converting the entity's backdrop-px (x,y) ↔ 3D world
via the same ortho projection the renderer uses. Flat 2D (non-mode3d) scenes keep the tile mask.

### Files touched
- `public/js/render3d.js` — added the collision API (`RAD/STEP_UP/STEP_DN`, `ground`, `floors`,
  `wall`, `resolveMove`) as the movement authority; no longer a TODO stub.

---

## Ready-to-apply engine wiring spec (exact seams — apply with the game running)

Verified the live seams. Three hooks, all behind a per-scene `Field.mode3d` flag so 2D scenes are untouched:

1. **Render layer** — `main.js:687` `Field.draw(g, entities, dt, act)` → inside `field.js` `draw()`
   (`field.js:215`): if `mode3d`, call `Render3D.setView(view.camX, view.camY, view.viewH)` (the
   values `updateCamera()` already returns, `field.js:205`), then `Render3D.setEntities(drawList)`,
   `Render3D.frame()`, and SKIP the 2D backdrop `drawImage` + painter's layer list. Keep
   `this._lastView = view` (`field.js:222`) so the HUD's `worldToScreen` (`field.js:208`) is untouched.
   The WebGL canvas sits under the 2D HUD canvas.

2. **Collision** — `main.js:618` `fieldWalkable(sceneKey, x, y)` is the boolean px test the movement
   loop calls. For flat mode3d scenes it can stay boolean (map px→world, `Render3D.floors(x,z).length>0`).
   **For multi-level scenes it must become stateful:** the entity needs a height/level field, and the
   movement step calls `Render3D.resolveMove({x,y,z}, dx, dz)` (returns the climbed/slid position)
   instead of testing a px. This is the one real movement-loop change — needs live 2-player iteration.

3. **px ↔ world mapping** — the single calibration both hooks share: entity backdrop-px (x,y) ↔ 3D
   world, using the same ortho projection the renderer places characters with. Calibrate against a
   loaded scene (place a known-px entity, read its world pos) — the one thing that needs the running game.

`_mask` bitmap path (`field.js:149`, `field.js:67`) stays for flat/legacy scenes; mode3d scenes bypass it.

### State at this checkpoint
- Ch1 + Ch2: 13 scenes migrated (concept→3D→stylized, walk-first designed paths, world-fill). DONE.
- `render3d.js`: render + **3D-raycast collision authority** (`resolveMove`) — the module the wiring targets.
- Remaining: apply the 3 hooks above + calibrate px↔world + boot 2 players. Needs the running game.

---

## Playability verification via programmatic locomotion (2026-07-28)

Drove the actual `step()` collision (not just floor-existence) headlessly across scenes. Two findings:

1. **False-floor perch bug (FIXED)** — raycast collision treated every upward face as floor, so
   props/awnings/lantern-bars became floors. square3d spawned Vesper at y=2.6 on a lantern-bar and
   she couldn't move. Fix (committed): collision raycasts **`walk_` meshes only**; occlusion still
   uses all geometry. Flat scenes now spawn on ground (y=0) and walk freely — verified on square3d
   (full 3×3 plaza traversal) and entrance3d (3u each direction).

2. **Scaffold vertical-scale bug (OPEN)** — stairs3d treads step ~**2.8 units** each
   (heights 0.4, 3.2, 6, 8.8, … 39.6) vs `STEP_UP=0.55`, so the staircase is unclimbable and Vesper
   spawns on a high tier (y=22.8) off the visible stairs. The scaffold geometry is ~6× too tall
   vertically — a `stair_flight`/`platform` height-scale error in the scenekit build for the scaffold
   scenes. Affects **stairs3d** and likely lockfive3d / descent3d / dellhollow3d.

### Play status right now
- **Playable** (flat Ch1): square3d, entrance3d, lane3d, forest3d, gate3d, interior3d, cottage3d —
  walk with WASD via `public/play.html` → scene → play3d. Spawn-on-ground + free movement confirmed.
- **Renders but not walkable** (scaffold/multi-level): stairs3d, lockfive3d, descent3d, dellhollow3d —
  need the tread/platform vertical scale rebuilt to ≤ STEP_UP per step, then re-export + re-test climb.

Next scaffold fix: correct `SceneKit.stair_flight`/`platform` vertical step (or scale the scaffold
scenes down ~6×), re-export, and re-run the greedy-climb test (must reach the top tier from the base).

---

## Overnight build 2026-07-29 (autonomous shift) — summary pointer

Full log with verdicts: `docs/qa/NIGHTLOG.md`. Review board: `/review/dellhollow-morning.html`.
Playable hub: `/play.html`. Headlines:
- **Dellhollow is walkable end-to-end**: whole-town gray blockout exported (`townwalk` scene),
  player-like grand tour passes **41/41 legs** (every landmark incl. spurs). All fixes are in
  map data + generator (durable), incl. flights-outside-flat-features, hairpin amplitude,
  vertical-extent wall test, threshold pads, corrected quay/gate/bridge/deep-stairs routes.
- **All six interiors** (cottage supper, item, inn, weapon, armor, cookhouse) built to the
  art gate, ACCEPTED, exported as playable runtime scenes, on the hub. Notes-polish applied.
- **First detailed exterior**: the Boatyard at true town coords, quality-gated to v10
  (accepted w/ notes), with the walk-preservation contract PROVEN (byte-identical walk meshes,
  909/909 ray coverage, playable through the finished art).
- **13 draft scene parcels + cameras** re-rendered as ortho/persp shot pairs; p-boatyard camera
  yaw corrected (agent caught it 180° off its own note).
- **emberbrook.map.json drafted** (town #2, validator-clean, real ch1 NPC names, draft-flagged).
- Kit library + KITLIB_MANIFEST (findings 1-40) — the accumulated craft lessons.
All on `migration/3d-hybrid`; nothing pushed; all taste gates (cameras, projections, art
verdicts) remain the user's.

### Architecture canon (2026-07-29, user-ratified): one town model, no composites
- `public/townmap/dellhollow.map.json` = source of truth for TOPOLOGY (landmarks, walk network,
  parcels). `tools/blends/dellhollow-master.blend` = source of truth for FORM.
- District detailing happens IN THE MASTER, one agent at a time (serial). Copy-out + composite
  is forbidden (town_master.py is deprecated after its one-time Boatyard amnesty).
- walk_/bar_ meshes are canonical topology: agents may never move/edit/delete them; map edits
  reach the master only through surgical scripts that touch blockout-owned objects exclusively.
- Interiors remain separate models (outside the town) and may build in parallel.
- Every master pass: rolling backup to tools/blends/backups/ (gitignored), walk-QA, townwalk
  re-export so the explorable town stays current.
- District gate (user, 2026-07-29): aesthetics bar = Boatyard v10, PLUS a geometry-coherence
  gate — no interpenetrating major objects, no unsupported/orphaned strays, and the walkable
  path must READ visually in-frame. Enforced by tools/geometry_audit.py in every district QA.
- Projection canon (user, 2026-07-29): PERSPECTIVE (~35deg vfov) is the default for all scene
  cameras — matches every accepted interior + Boatyard v10 and the FF7/8/9 originals. Ortho
  remains a deliberate per-shot exception only. (The board's gray ortho drafts were cameras
  buried in the cliffs by the fixed ortho standoff — retired along with the default.)
- Scene-type canon (user, 2026-07-29): TRANSIT VIGNETTES are legitimate scenes — a camera over a
  journey with no landmarks (parcels[].transit + throughEdges). First instance: del-crossing,
  the plank-bridge postcard. Validators exempt transit parcels from zero-exit errors.
- Character canon (user, 2026-07-29): the KayKit rogue is a STAND-IN; custom 3D characters
  (Vesper et al.) are a future workstream. Don't art-direct around KayKit style.
- COMBAT canon (user, 2026-07-29): the game WILL have combat (reversing the original no-combat
  premise). Weapon/armor shops are real. Combat design is an unopened workstream — encounters,
  stats, enemies TBD. Interlocks with the overworld (encounter zones).
- OVERWORLD canon (user, 2026-07-29): FF-style MINIATURE overworld (abbreviated scale, towns as
  landmarks) — real-time rendered in explore mode (not pre-rendered), worldmap.json topology +
  world master form, transit vignettes for overlooks. It is a GAMEPLAY space: combat encounters,
  economy (money/items/equipment/grinding), and unlockable transport — the tar-dark boat becomes
  drivable river/water traversal after the Dellhollow chapter's departure finale.
- OCCLUSION canon (user-ratified, 2026-07-29): fixed-camera scenes use EXACT-PIXEL depth-map
  occlusion. tools/depth_bake.py is THE bundle exporter: one Blender session on the ORIGINAL
  blend (read-only — never copy a blend, relative texture paths break: manifest 63) renders
  background.png, bakes depth.png/depth.json (view-space depth from the same camera; Cycles
  camera-space +Z: manifest 64), and exports scene.glb. Image and occlusion cannot disagree
  by construction. Runtime (play3d.html): depth.json present -> fullscreen quad writes
  gl_FragDepth, geometry never writes depth (collision only). The old workflow is DEAD:
  interior_export.py deprecated (delete once the interiors circulation agent lands — it was
  told to export via depth_bake.py), overhead-ghosting + small-prop heuristics removed from
  the runtime. Raw invisible-geometry depth remains ONLY as the fallback for legacy pilot
  scenes until they are rebuilt. townwalk is RT-explore (no backdrop occlusion — unaffected);
  del-boatyard re-bakes from the master when the Waterfront agent lands.
- PARALLEL BRANCH-DISTRICT protocol (user-ratified, 2026-07-29): serial custody still governs
  the LIVE master, but a NON-ADJACENT district may be built concurrently on a branch copy
  (same directory — relative texture paths, manifest 63) under strict rules: ADDITIVE-ONLY
  (new objects in one district collection, unique name prefix); the only permitted deletions
  are lm_ blockout shells fully inside the jurisdiction, each recorded in a deletions
  manifest JSON; walk_/bar_, shared light rigs, world, far-rim cliffs, fx_ silhouettes and
  everything outside the parcel extent are untouchable; walk QA must pass 367/367 zero-drift
  on the branch. Merge = scripted replay (delete manifest names, append the district
  collection, remap duplicate materials by name) followed by the full gates. First use:
  gate approach (p-gate: Porters' Yard, Gatehouse, Valley Gate, Cargo Winch head) branched
  while Locksfoot proceeds on the live master — chosen over the Weave because the Weave is
  vertically interleaved with Locksfoot AND is the Waterfront's backdrop (compose in-context).
- WEST-BRANCH TIER DESCENT (user, 2026-07-29): the gate branch continues DOWNWARD tier by
  tier on the same branch blend — after gate polish, the shelf tier (p-shelf-w + p-shelf-e:
  inn, item shop, shelf-homes) under the same protocol (own SHELF_DISTRICT collection,
  shelf_ prefix, own deletions manifest; inn/item lm_ shells deletable once replaced).
  Decoupled from the live master's east/river-level work (Locksfoot x>=65). Merge carries
  all branch districts together — still mechanical, one collection + manifest per district.
- RENDER NORM (user, 2026-07-29): agent renders are SELF-VERIFICATION, not presentation.
  Per-version EEVEE check spreads stay (an agent's only visual sense — the gates catch
  drift, not ugliness). CUT: final high-sample Cycles beauty sets (record at most 2-3
  shots, EEVEE acceptable); QA cameras are disposable scaffolding — never polish angles
  beyond "subject visible" (the real game cameras are authored later from the map's
  camera hints). The user reviews by WALKING scenes (townwalk / branch previews / hub),
  not by browsing stills.
- GLTF-SURVIVAL GATE FOR EXTERIORS (2026-07-29): 516/1587 townwalk prims export WHITE —
  procedural node-tree materials (foliage ramps, ropes/bunting, lock_four_dam stone) cannot
  cross glTF; Blender renders hid it because nodes run there. From now on EVERY master
  district pass verifies its new materials by GLB round-trip (vertex colors / textures /
  flat factors only), same as interiors always did. Legacy cure queued: a master-wide
  survivability pass (bake procedural albedo to vertex-color attributes; gradients survive)
  takes the next custody slot after the Weave tier.
