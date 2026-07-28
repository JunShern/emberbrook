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

### Verified: the whole FF-hybrid + a scalable authoring template work in the target repo.
### Remaining = keep authoring scenes on the template, + wire into the live 2-player engine.

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
