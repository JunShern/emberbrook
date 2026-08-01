<!-- RESCUED 2026-08-02 from the rpg-3d sandbox (docs/TARGET_SYSTEM.md) immediately
     before that directory was deleted. This is the FOUNDING rationale for the rendering
     approach the game still runs on: pre-rendered stylized backgrounds + an invisible
     depth-writing GLB for occlusion and raycast collision. CLAUDE.md's Runtime section
     assumes this design without restating why it was chosen; this is the why. Paths and
     tool names below are sandbox-era and mostly superseded — read it as history, not as
     current instructions. -->

# Target system — the FF-hybrid pipeline (migration destination)

This documents the rendering approach we prototyped in `rpg-3d/`, which the Emberbrook
game will migrate to. It is the "known-good" end state; the migration plan maps the
current 2D painted-background system onto this.

## One-line summary
**Pre-rendered, stylized backgrounds (FF9-style) with a real-time 3D layer for depth
occlusion and collision (FF7/9), plus real-time characters.** Each scene ships as a
small bundle of files; one runtime loads any scene.

## Per-scene artifacts (what a "scene" becomes)
A migrated scene is a folder of:
| File | Made by | Purpose |
|---|---|---|
| `background.png` | Blender render (transparent bg) | the raw 3D render (1344×768) |
| `stylized.png` | nano-banana img2img over `background.png` | the **shipped** painterly image + painted-in background |
| `scene.glb` | Blender glTF export (`export_yup`) | the geometry, loaded **invisible/depth-only** for occlusion + raycast collision; includes the scene camera |
| `camera.json` | Blender export (view matrix + frame extents) | world↔screen projection (only needed if compositing without the GLB camera) |

No hand-authored walkmask, no baked occluders — **collision and occlusion are derived
from the GLB geometry at runtime.**

## Authoring pipeline (per scene, in order)
1. **Model** the scene in Blender (blockout is enough — the stylization adds detail).
   Reusable parameterized builders exist (`house()`, `tier()`, `stairflight()`, props).
2. **Materials/lighting**: PolyHaven PBR via `build_pbr()`; HDRI as a *light source only*
   (`film_transparent=True` so the literal HDRI isn't the visible backdrop).
3. **Fixed camera** at a consistent 3/4 angle.
4. **Render + export atomically** (same geometry+camera in one pass):
   `background.png` (transparent) + `scene.glb` (+camera) + `camera.json`.
   > Hard-won lesson: regenerate all passes together or they desync.
5. **Stylize**: `node tools/genart.mjs stylized.png --ref background.png --ar 16:9 "<style prompt>"`
   — nano-banana (`gemini-2.5-flash-image`), ~$0.04/scene. Geometry is preserved, so the
   GLB depth still aligns with the painting. The shared style prompt = cross-scene cohesion.

## Runtime (`web/play3d.html`, Three.js r128) — one engine, any scene
- Loads `scene.glb`; sets every mesh `colorWrite:false` + `renderOrder:-1` → **invisible
  but depth-writing**, drawn before the character so the GPU z-buffer occludes correctly.
- `scene.background` = `stylized.png` (the painterly image shows through).
- Camera = the GLB's own camera (`gltf.cameras[0]`) → no coordinate math needed.
- **Character** = either:
  - **3D model** (KayKit rig or a Rodin→Mixamo custom char): AnimationMixer, Idle/Walk/Jump,
    faces movement via `rotation.y = atan2(dx,dz)`.
  - **HD-2D billboard** (`web/play_hd2d.html`): the existing 2D sprite as a depth-occluded
    plane (alphaTest silhouette), 4-dir facing, walk-frame cycling. Octopath-style.
- **Collision/physics** (visual-independent): raycast the GLB meshes — down-ray for
  ground/stairs (normal.y>0.5, limited to step height), 3-ray-wide horizontal sweep above
  step height for walls (so stairs are walkable but pillars/railings block). Capsule radius.
- **Jump/gravity**, edge-blocking, multi-level ground-following all derived from geometry.

## Why this scales (the migration thesis)
The consistency-critical, usually-hard parts — **occlusion, collision, and a cohesive art
style** — are solved once and are **free per new scene** (occlusion+collision come from the
geometry; style comes from the shared stylization prompt). The remaining per-scene cost is
"build a 3D blockout + fixed camera," which is normal level-building and is the main lever
to streamline (modular kits, GUI authoring, leaning on the stylization to keep blockouts rough).

## Reusable tooling built so far (the playbook)
- `tools/genart.mjs` — nano-banana img2img (stylization). Reused per scene.
- `build_pbr()` material builder + PolyHaven textures — reusable palette.
- Blender render/export scripts (beauty + GLB + camera, atomic).
- Parameterized geometry builders (house/tier/stair/props) — the start of a scene kit.
- The Three.js runtime (`play3d.html` / `play_hd2d.html`) — loads any scene bundle.
- Nav derivation (raycast collision) + accessibility flood-fill checker (`tools/check_nav.mjs`).

## Open decisions carried into the migration (for discussion)
- **Character route**: HD-2D sprites (reuse existing 2D cast, Octopath) vs custom 3D
  (Rodin→Mixamo). Both work in this engine; pick per project.
- **Runtime home**: keep Three.js as a parallel renderer, or fold into the existing
  vanilla-JS engine. (Depends on how the current engine composites — pending research.)
- **Style drift** across many scenes → add reference-image conditioning to `genart.mjs`.
