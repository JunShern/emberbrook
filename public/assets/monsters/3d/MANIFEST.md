# 3D Monster Models — Provenance & Licensing

**These are PLACEHOLDER stand-ins, not final art.** They exist only to judge scale, silhouette,
grounding and composition in the 3D battle arena. Every one of them is expected to be replaced by
bespoke art before release.

**CC0 / public-domain ONLY.** Nothing in this directory may be CC-BY, CC-BY-SA, NC-restricted,
GPL-encumbered, "free for non-commercial", or ripped from a commercial game. Every file below was
sourced from a page whose license field was read directly and is quoted verbatim in this document.
If you add a file here, you must verify the license on the asset page itself — never trust a
filename, a repo name, or a mirror — and record it in the table below.

All six slots are filled. Nothing was skipped, and no non-CC0 substitute was used. Every model is
**by Quaternius** and every one carries a **CC0 1.0 Universal** dedication, verified on the
quaternius.com pack page and — for four of the six packs — in a `License.txt` shipped inside the
download itself. Several CC-BY candidates were rejected during the search (Poly Pizza carries a
large amount of CC-BY 3.0 material; see "Rejected candidates" at the bottom).

## Summary table

| File | Monster slot | Concept | Bytes | Native H (own units) | Clips | Pack | Author | License |
|---|---|---|---|---|---|---|---|---|
| `reed-nibbler.glb` | reed-nibbler | pale-green slime blob | 174,396 | 1.948 | 4 | Animated Monster Pack (2018-08) | Quaternius | CC0 1.0 Universal |
| `brook-sprite.glb` | brook-sprite | white round ghost / spirit | 288,400 | 1.408 | 10 | Cute Animated Monsters Pack (2020-08) | Quaternius | CC0 1.0 Universal |
| `duskpad.glb` | duskpad | four-legged grey wolf | 1,920,324 | 2.674 | 12 | Ultimate Animated Animal Pack (2021-07) | Quaternius | CC0 1.0 Universal |
| `bramble-shade.glb` | bramble-shade | bark-textured tree creature with branch antlers | 402,776 | 2.859 | 9 | Cute Animated Monsters Pack (2020-08) | Quaternius | CC0 1.0 Universal |
| `scree-shell.glb` | scree-shell | red armoured crab, wide and low | 372,408 | 1.577 | 10 | Cute Animated Monsters Pack (2020-08) | Quaternius | CC0 1.0 Universal |
| `weir-eel.glb` | weir-eel | coiled teal serpent, head raised | 216,696 | 3.180 | 4 | Easy Enemy Pack (2019-01) | Quaternius | CC0 1.0 Universal |

**Total added: 3,375,000 bytes (3.22 MiB).** All downloads dated **2026-07-30**.

## Licence text seen, verbatim

### quaternius.com pack pages (all four packs)

Each pack page carries an info panel whose License row reads exactly:

```html
<div class="infoitem"><img src="/assets/svg/license.svg" class="iconBig"> License<div
class="text-right"><a href="https://creativecommons.org/publicdomain/zero/1.0/" target="_blank"
>CC0</a></div></div>
```

i.e. the license is stated as **CC0**, hyperlinked to
`https://creativecommons.org/publicdomain/zero/1.0/`. Each pack description additionally states the
models are "*free to use in personal and commercial projects.*"

### `License.txt` shipped inside the download

**Ultimate Animated Animal Pack** — `/License.txt` in the pack's Drive folder, verbatim:

```
------------------------------------------------------
LowPoly Models by @Quaternius
Consider supporting me on Patreon, even $1 helps me a lot!

https://www.patreon.com/quaternius
-------------------------------------------------------

License:
CC0 1.0 Universal (CC0 1.0) 
Public Domain Dedication
https://creativecommons.org/publicdomain/zero/1.0/
```

**Easy Enemy Pack** — `/License.txt`, verbatim: identical to the block above (byte-for-byte).

**Animated Monster Pack** — `/License.txt`, verbatim:

```
------------------------------------------------------
Animated Monsters by Quaternius
Consider supporting me on Patreon, even $1 helps me a lot!

https://www.patreon.com/quaternius
-------------------------------------------------------

License:
CC0 1.0 Universal (CC0 1.0) 
Public Domain Dedication
https://creativecommons.org/publicdomain/zero/1.0/

-------------------------------------------------------
If you want to credit me just say:
Animated Monsters by Quaternius
https://www.patreon.com/quaternius
```

**Cute Animated Monsters Pack** — ⚠️ this pack's Drive folder does **not** contain a `License.txt`
(contents are `glTF/`, `Blends/`, `FBX/`, `OBJ/`, `Textures/`, `Preview.jpg` and nothing else). Its
licence therefore rests on the pack page's `CC0` field quoted above, which is the same field and the
same CC0 1.0 link used by every other Quaternius pack, plus the description line "*free to use in
personal and commercial projects*". Three of the six files here come from that pack; if that
second-hand-ness is not acceptable for a given use, those three should be re-verified or replaced.

### itch.io mirror (independent corroboration for the Animated Monster Pack)

<https://quaternius.itch.io/lowpoly-animated-monsters> states verbatim:

```
CC0 License https://creativecommons.org/publicdomain/zero/1.0/
```

### Poly Pizza asset pages (the two files re-hosted through Poly Pizza)

Both pages render the metadata line:

```
Jul 11, 2022 • FBX/GLTF format • Public Domain (CC0)
```
```
Aug 19, 2021 • FBX/GLTF format • Public Domain (CC0)
```

with "Public Domain (CC0)" hyperlinked to `https://creativecommons.org/publicdomain/zero/1.0/`, and
the page's embedded model record carries the field `"Licence":"CC0 1.0"` with
`"Creator":{"Username":"Quaternius"...}`.

Attribution is **not** required under CC0, but crediting **Quaternius**
(<https://quaternius.com>, <https://www.patreon.com/quaternius>) is appreciated by the author and
costs us nothing.

## Two acquisition routes (and why)

Quaternius distributes each pack as a public Google Drive folder linked from the pack page. Some
packs ship a `glTF/` directory; the older ones ship only `FBX/`, `OBJ/` and `Blends/`.

- **Route A — source glTF, repacked to GLB (4 files).** Where the pack ships glTF, the `.gltf` was
  downloaded straight from the author's own Drive folder and repacked into a `.glb` container. This
  is the authoritative artefact, keeps the original clip names, and needs no third party.
- **Route B — Poly Pizza (2 files: `reed-nibbler`, `weir-eel`).** The Animated Monster Pack and the
  Easy Enemy Pack ship **no glTF at all**, and Blender is not installed on this machine, so FBX
  could not be converted locally. Poly Pizza hosts Quaternius's own uploads as ready-made GLB
  (converted by them with FBX2glTF v0.9.7) and states the CC0 licence on the asset page. Those two
  files are byte-for-byte as Poly Pizza serves them, renamed only.

### Repack procedure used for Route A (lossless)

The Quaternius `.gltf` files embed their whole binary payload as a single
`data:application/octet-stream;base64,…` buffer URI, and their PNG texture is already stored in a
`bufferView` (no external image `uri`). Converting to `.glb` is therefore a pure container change:

1. Assert exactly one buffer, and that its `uri` is a `data:` URI (refuse otherwise).
2. Base64-decode it and assert the decoded length equals `buffers[0].byteLength`.
3. Assert no `images[i].uri` exists (i.e. no external texture would be dropped).
4. Delete `buffers[0].uri`, re-serialise the JSON, and write the standard 12-byte GLB header +
   `JSON` chunk (space-padded to 4 bytes) + `BIN` chunk (zero-padded to 4 bytes).

No geometry, animation, material or texture data is re-encoded, resampled, decimated, recoloured or
re-quantised. Nothing is scaled or re-oriented. The script lives in the scratchpad only; it is
25 lines and is trivially reproducible from the description above.

## Verification

`tools/glb_read.mjs` is an ES **module with no CLI entry point** (it exports `loadGlb`/`WALK_RE` and
has no `process.argv` handling), and by its own doc-comment it deliberately reads "no materials, no
animations". It was therefore *imported* by two throwaway Node scripts rather than shelled out to:

- `loadGlb()` from `tools/glb_read.mjs` parsed all six files successfully (chunk walk, accessor
  decode, node hierarchy, world matrices) — this is the same reader the scene-graph tooling uses, so
  a parse here means the runtime bundle reader accepts the file.
- A second script implements the full glTF skinning equation at the **rest pose** (each node's
  default TRS, joint matrix = worldTransform(joint) × inverseBindMatrix, weighted by
  `JOINTS_0`/`WEIGHTS_0`) to get a true visual bounding box. This matters: the raw `POSITION`
  accessor min/max over-reports width on several of these rigs (e.g. `duskpad` reads D=5.553 raw vs
  D=5.274 skinned). **The "rest-pose bbox" numbers below are the ones to scale against.**

Every file: valid GLB v2.0, one BIN chunk, parses clean, has ≥1 skin and ≥4 animation clips.

## Scaling against a 1.7 m character

These models are **not** in metres. Multiply by the factor below to hit the brief's target size.
All are Y-up (glTF convention) and sit on Y≈0 (see `groundY`).

| Slot | Target | Rest-pose W × H × D | groundY | Scale for target H | Resulting W × D at that scale | Faces |
|---|---|---|---|---|---|---|
| reed-nibbler | 0.6 m tall | 2.537 × 1.948 × 3.062 | −0.014 | **0.308** | 0.78 × 0.94 m | **+X** |
| brook-sprite | 0.8 m | 1.452 × 1.408 × 1.462 | −0.005 | **0.568** | 0.82 × 0.83 m | +Z |
| duskpad | 1.0 m at shoulder | 1.056 × 2.674 × 5.274 | −0.010 | **0.50–0.55** (see note) | 0.55 × 2.7 m | +Z |
| bramble-shade | 1.8 m | 2.811 × 2.859 × 1.727 | −0.041 | **0.630** | 1.77 × 1.09 m | +Z |
| scree-shell | 1.2 m | 2.567 × 1.577 × 1.417 | −0.029 | **0.761** | 1.95 × 1.08 m | +Z |
| weir-eel | 1.5 m coiled | 1.054 × 3.180 × 2.729 | −0.003 | **0.472** | 0.50 × 1.29 m | +Z |

Notes:

- **`duskpad` shoulder vs total.** Its bbox height (2.674) is measured to the top of the raised
  head, not the shoulder. The `Head` joint sits at y=2.11 and the spine/shoulder region around
  y≈1.9–2.0, so shoulder ≈ 0.72 × total. Scaling by **0.374** gives a 1.0 m *total* height (too
  small); scaling by **≈0.52** gives a ≈1.0 m *shoulder* and a ≈1.39 m overall wolf, which is what
  the brief asks for. The body is 5.27 units long — at 0.52 that is a **2.7 m** long animal, which
  is large for a wolf; the mesh is genuinely elongated (nose-to-tail-tip including a long tail:
  `Head` at z=+1.88, `Tail8` at z=−2.43). Consider ≈0.45 if footprint matters more than shoulder
  height.
- **`scree-shell` is wide.** At the height-matched 0.761 it is 1.95 m across the claws. If 1.2 m is
  meant as overall bulk rather than height, use ≈0.47 (1.2 m wide, 0.74 m tall) — it is a squat,
  wide silhouette by design.
- **`reed-nibbler` faces +X, everything else faces +Z.** The slime came through FBX2glTF, which
  applied a different axis convention: its `RightEye`/`LeftEye` joints are separated along ±Z and
  both sit at x=+0.37 in front of `Head`. Apply a **+90° yaw** (or −90°, depending on your
  handedness convention) to line it up with the other five. Verified by joint world positions, not
  by eyeballing the mesh.
- Facing was determined from named joint world positions (`Head`/`Mouth`/`Tongue`/`Tail`), not
  guessed.

## Per-file detail

### `reed-nibbler.glb`

- Slot: **reed-nibbler** — small critter / slime / blob grazer
- Depicts: a pale-green low-poly slime blob with two large black eyes and two stubby arms
- Pack: **Animated Monster Pack** (August 2018) — 4 animated monsters (Bat, Dragon, Skeleton, Slime)
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/animatedmonster.html>
- Pack download folder (author's own): <https://drive.google.com/drive/folders/102H-oyUM8SGYi1mW0GOgkjEu7xSdaORA>
- itch.io mirror of the same pack: <https://quaternius.itch.io/lowpoly-animated-monsters>
- **Acquired from:** Poly Pizza (Route B — the pack itself ships only `Blend/Slime.blend`,
  `FBX/Slime.fbx`, `OBJ/Slime.obj`; no glTF, and no local FBX converter)
  - Asset page: <https://poly.pizza/m/LyjSUKHKnh>
  - Direct download: <https://static.poly.pizza/195565b4-842a-44e9-a59a-5ebb1d133255.glb>
- License: **CC0** — `"Licence":"CC0 1.0"` / "Public Domain (CC0)" on the Poly Pizza page; `CC0` on
  the quaternius.com pack page; the pack's own `License.txt` says "CC0 1.0 Universal (CC0 1.0)
  Public Domain Dedication" (full text quoted above)
- Downloaded: **2026-07-30**
- Original filename: `195565b4-842a-44e9-a59a-5ebb1d133255.glb` as served by Poly Pizza; upstream
  the same model is `Slime.fbx` / `Slime.blend` in the Quaternius archive
- Processing: **none** — copied byte-for-byte and renamed
- sha256: `21d9819032c8cf6e5cacd20ffb83c4bc781f65843f707b2a0dcc71ba6e75d75a`
- Generator: `FBX2glTF v0.9.7` · 1 mesh (`Slime`) · 1,440 tris · 2 materials · **0 textures**
  (flat material colours) · 1 skin · 19 nodes
- Animation clips (4): `Armature|Slime_Attack`, `Armature|Slime_Death`, `Armature|Slime_Idle`,
  `Armature|Slime_Walk`
- Native bbox (rest pose): min `[-1.268, -0.014, -1.531]` max `[1.268, 1.934, 1.531]` →
  **W 2.537 × H 1.948 × D 3.062**
- Style-matched alternative from the Cute Monsters pack (matches the other three files here):
  `glTF/Mushroom.gltf`, H 2.081, 10 clips, ~270 KB after repack

### `brook-sprite.glb`

- Slot: **brook-sprite** — wisp / floating light spirit
- Depicts: a round white ghost blob with big eyes and a draped hem — the most orb-like silhouette in
  the set, which is why it was chosen over the darker wraith-shaped "Ghost" in the Ultimate Monsters
  pack
- Pack: **Cute Animated Monsters Pack** (August 2020) — 21 cute animated monsters
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/cutemonsters.html>
- Pack download folder: <https://drive.google.com/drive/folders/1zLLO_7ZoWgUsS4uooYnVSErQYRu1VdS0>
- Direct download: `https://drive.usercontent.google.com/download?id=1NJL2LzA-v3n72SaJ5xRNlCLV0gWXNjIC&export=download`
- License: **CC0** — pack page License field is `CC0` linked to
  <https://creativecommons.org/publicdomain/zero/1.0/>; description says "free to use in personal
  and commercial projects". ⚠️ no `License.txt` inside this particular pack's folder (see above).
- Downloaded: **2026-07-30**
- Original filename inside the archive: **`glTF/Ghost.gltf`** (457,860 bytes)
- Processing: **.gltf → .glb container repack only** (procedure above). No re-encoding.
- sha256: `4b73eefc407fe67345b02183114adbfe704bb22d03bb92441dde1932f3313b08`
- Generator: `Khronos glTF Blender I/O v1.6.16` · 1 mesh (`Sphere.030`) · 1,000 tris · 1 material ·
  1 embedded PNG texture · 1 skin · 9 nodes · root node `MonsterArmature`
- Animation clips (10): `Bite_Front`, `Bite_InPlace`, `Dance`, `Death`, `HitRecieve`, `Idle`,
  `Jump`, `No`, `Walk`, `Yes`
- Native bbox (rest pose): min `[-0.726, -0.005, -0.726]` max `[0.726, 1.403, 0.736]` →
  **W 1.452 × H 1.408 × D 1.462**
- Note: it does **not** hover — `groundY ≈ 0`, it stands. Lift it in the scene if it should float.

### `duskpad.glb`

- Slot: **duskpad** — wolf / hound / beast
- Depicts: a grey-and-tan four-legged wolf, standing, head raised, long tail
- Pack: **Ultimate Animated Animal Pack** (July 2021) — 12 animals, 12+ animations each
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/ultimateanimatedanimals.html>
- Pack download folder: <https://drive.google.com/drive/folders/1uJ3N5HfB7jKTseJUNQr3N4YaN0UuEtHk>
- Direct download: `https://drive.usercontent.google.com/download?id=1lFQoQ9ln2Z2wGuFFWObj9i5jHqUl_ftG&export=download`
- License: **CC0** — pack page License field `CC0`; `License.txt` in the same folder
  (`https://drive.usercontent.google.com/download?id=1F2uy8T2fRpdc6gZ4mnS02_C2E63WvKtn&export=download`)
  reads "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication" (full text quoted above)
- Downloaded: **2026-07-30**
- Original filename inside the archive: **`glTF/Wolf.gltf`** (3,175,890 bytes)
- Processing: **.gltf → .glb container repack only.** No re-encoding.
- sha256: `142291b6f9114c2fc9ac8e51ffda8d9f959c5726036c3ea9946be173b608a5aa`
- Generator: `Khronos glTF Blender I/O v1.6.16` · 1 mesh (`Cube`) · 1,962 tris · 4 materials ·
  **0 textures** · 1 skin · 53 nodes · root node `AnimalArmature`
- Animation clips (12): `Attack`, `Death`, `Eating`, `Gallop`, `Gallop_Jump`, `Idle`, `Idle_2`,
  `Idle_2_HeadLow`, `Idle_HitReact1`, `Idle_HitReact2`, `Jump_ToIdle`, `Walk`
- Native bbox (rest pose): min `[-0.528, -0.010, -2.713]` max `[0.528, 2.664, 2.561]` →
  **W 1.056 × H 2.674 × D 5.274**
- **Size caveat.** 1.92 MB — the largest file here and 57 % of the total, because the Blender
  exporter writes translation + rotation + scale channels for all 53 joints in all 12 clips
  (1,836 channels, 1.49 MB of the 1.92 MB is animation). If that is too heavy, Poly Pizza hosts the
  same model as a 986,712-byte GLB at <https://poly.pizza/m/P1gU3Qkr9r> (direct:
  `https://static.poly.pizza/f1d12388-e39b-4157-b32a-646a1d089fc4.glb`, same CC0 statement, same
  1,962 tris). Downside: their FBX2glTF pass emits **24** clips — each of the 12 twice, once bare
  (`Idle`) and once prefixed (`AnimalArmature|Idle`), with genuinely duplicated channel data — so
  the clip list is confusing even though the file is half the size. The source-of-truth version was
  preferred here.

### `bramble-shade.glb`

- Slot: **bramble-shade** — plant creature / treant / vine monster
- Depicts: a bark-textured brown tree creature with two branching antlers, big eyes and a wide mouth
- Pack: **Cute Animated Monsters Pack** (August 2020)
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/cutemonsters.html>
- Pack download folder: <https://drive.google.com/drive/folders/1zLLO_7ZoWgUsS4uooYnVSErQYRu1VdS0>
- Direct download: `https://drive.usercontent.google.com/download?id=1qZtei_Pg0wK-P4bV-6-zP4nThj_XgQCt&export=download`
- License: **CC0** — as for `brook-sprite.glb` above (same pack, same caveat about no `License.txt`)
- Downloaded: **2026-07-30**
- Original filename inside the archive: **`glTF/Tree.gltf`** (603,264 bytes)
- Processing: **.gltf → .glb container repack only.** No re-encoding.
- sha256: `a07772874d88ff27fba5687cdff3669afce20458270029e2ed61f670de3c430b`
- Generator: `Khronos glTF Blender I/O v1.6.16` · 1 mesh (`Sphere.000`) · 1,368 tris · 1 material ·
  1 embedded PNG texture · 1 skin · 9 nodes · root node `MonsterArmature`
- Animation clips (9): `Bite_Front`, `Bite_InPlace`, `Dance`, `HitRecieve`, `Idle`, `Jump`, `No`,
  `Walk`, `Yes` — **note: this is the one model in the set with no `Death` clip.** Use `HitRecieve`
  or a fade-out for its defeat beat.
- Native bbox (rest pose): min `[-1.406, -0.041, -0.960]` max `[1.405, 2.818, 0.767]` →
  **W 2.811 × H 2.859 × D 1.727** — the tallest model here; the antlers account for most of it
- Alternatives considered, both CC0 Quaternius, both with a full 14-clip humanoid set
  (`Idle`/`Walk`/`Run`/`Punch`/`Death`/`HitReact`/…): `Cactoro` (<https://poly.pizza/m/IGn9lhdama>,
  471,704 B, H 3.834) — a spiky green cactus biped, arguably a better "bramble" silhouette but it
  wears a sombrero; and `MushroomKing` (<https://poly.pizza/m/grnFTziU8u>, 444,228 B, H 3.451).

### `scree-shell.glb`

- Slot: **scree-shell** — turtle / armored shell / rock golem
- Depicts: a dark-red armoured crab — rounded carapace, two raised claws, low and wide
- Pack: **Cute Animated Monsters Pack** (August 2020)
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/cutemonsters.html>
- Pack download folder: <https://drive.google.com/drive/folders/1zLLO_7ZoWgUsS4uooYnVSErQYRu1VdS0>
- Direct download: `https://drive.usercontent.google.com/download?id=1uvKAEskF10jW0zFo6SRhnTR7PBPxRfUi&export=download`
- License: **CC0** — as for `brook-sprite.glb` above (same pack, same caveat)
- Downloaded: **2026-07-30**
- Original filename inside the archive: **`glTF/Crab.gltf`** (569,872 bytes)
- Processing: **.gltf → .glb container repack only.** No re-encoding.
- sha256: `308de5e2711fcff960b72bdce71ed71ddceb9268957fc6190252148bff1474d1`
- Generator: `Khronos glTF Blender I/O v1.6.16` · 1 mesh (`Cube.030`) · 1,820 tris · 1 material ·
  1 embedded PNG texture · 1 skin · 9 nodes · root node `MonsterArmature`
- Animation clips (10): `Bite_Front`, `Bite_InPlace`, `Dance`, `Death`, `HitRecieve`, `Idle`,
  `Jump`, `No`, `Walk`, `Yes`
- Native bbox (rest pose): min `[-1.283, -0.029, -0.686]` max `[1.283, 1.548, 0.730]` →
  **W 2.567 × H 1.577 × D 1.417** — squat and wide, the shortest model here
- **Why a crab and not a turtle.** There is no turtle, tortoise or rock golem anywhere in the
  Quaternius, KayKit or Kenney catalogues (checked). Every "Turtle" on Poly Pizza is **CC-BY 3.0**
  (see rejected list). Quaternius's `Goleling` / `Goleling_Evolved`, despite the name, are green
  winged bat-heads, not golems. The crab was chosen because it is the only CC0 candidate that reads
  as *armoured, bulky and low-slung*, which is what the slot is for.

### `weir-eel.glb`

- Slot: **weir-eel** — snake / serpent / eel
- Depicts: a pale-teal serpent coiled on the ground with its head raised and forked tongue out
- Pack: **Easy Enemy Pack** (January 2019) — 5 animated enemies (Frog, Rat, Snake, Spider, Wasp)
- Author: **Quaternius**
- Pack source page: <https://quaternius.com/packs/easyenemy.html>
- Pack download folder (author's own): <https://drive.google.com/drive/folders/1VbJIslXPWK-1KybQN6yezZrfJcw608qe>
- **Acquired from:** Poly Pizza (Route B — the pack ships only `Blends/Snake.blend`,
  `FBX/Snake.fbx`, `OBJ/Snake.obj`; no glTF, and no local FBX converter)
  - Asset page: <https://poly.pizza/m/x9x0viZs8V>
  - Direct download: <https://static.poly.pizza/0f3a551e-743e-48f5-936f-804c6c3b88bd.glb>
- License: **CC0** — `"Licence":"CC0 1.0"` / "Public Domain (CC0)" on the Poly Pizza page; `CC0` on
  the quaternius.com pack page; the pack's own `License.txt`
  (`https://drive.usercontent.google.com/download?id=11VW7sXB197a4ZAVxuwVdEtWL1rAySIfI&export=download`)
  reads "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication" (full text quoted above)
- Downloaded: **2026-07-30**
- Original filename: `0f3a551e-743e-48f5-936f-804c6c3b88bd.glb` as served by Poly Pizza; upstream
  the same model is `Snake.fbx` / `Snake.blend` in the Quaternius archive
- Processing: **none** — copied byte-for-byte and renamed
- sha256: `70b4af1088dec939e167b07c0a5e69992a4851beac8bd24a9da1189b65ae101c`
- Generator: `FBX2glTF v0.9.7` · 1 mesh (`Snake`) · 1,618 tris · 7 materials · **0 textures** ·
  1 skin · 23 nodes
- Animation clips (4): `SnakeArmature|Snake_Attack`, `SnakeArmature|Snake_Idle`,
  `SnakeArmature|Snake_Jump`, `SnakeArmature|Snake_Walk` — **no `Death` clip**
- Native bbox (rest pose): min `[-0.553, -0.003, -1.046]` max `[0.500, 3.178, 1.683]` →
  **W 1.054 × H 3.180 × D 2.729**
- The pack also contains `Snake_Angry` (a second, aggressive-posed variant) but it is not on Poly
  Pizza, so it is only obtainable as FBX/OBJ/Blend.

## Rendering notes for the battle screen

- All six are **skinned** meshes. Play `Idle` on entry; `*_Attack` / `Bite_Front` for the attack
  beat; `HitRecieve` / `Idle_HitReact*` for damage; `Death` for defeat — except `bramble-shade` and
  `weir-eel`, which have no `Death` clip.
- Clip naming is **not** uniform across packs: the two FBX2glTF files prefix every clip with the
  armature name (`Armature|Slime_Idle`, `SnakeArmature|Snake_Idle`) while the four Blender-exported
  files use bare names (`Idle`). Match on a suffix, not on equality.
- Four of the six (`brook-sprite`, `bramble-shade`, `scree-shell` + the Cute Monsters alternatives)
  share one visual style — big flat eyes, blobby body, matte texture. `duskpad` (realistic-ish
  quadruped) and `reed-nibbler` / `weir-eel` (flat untextured materials) do not match it. This is
  fine for a placeholder pass but is the most visible seam if these ever ship.
- Only the three Cute Monsters files carry a texture; the other three are untextured flat-material
  meshes, so they will read as noticeably flatter under the same lighting.
- **All three Cute Monsters files (`brook-sprite`, `bramble-shade`, `scree-shell`) declare
  `KHR_materials_unlit`** in `extensionsUsed`, and their single material carries the extension. That
  means they are authored to render **fullbright, ignoring scene lighting**. Three.js supports the
  extension and will honour it — so these three will *not* receive the arena's lights, shadows or
  fog tint and will look flat/pasted-on next to the character unless the extension is stripped or
  the materials are swapped for `MeshStandardMaterial` at load time. `duskpad`, `reed-nibbler` and
  `weir-eel` declare no extensions and light normally. This is the single biggest integration
  gotcha in this batch.
- Nothing here has been scaled, re-oriented or re-centred; use the scale table above.

## Rejected candidates (non-CC0 — do not use)

Recorded so the same dead ends are not re-walked. All licences read off the Poly Pizza asset page's
own licence field:

| Model | Author | Licence | Why it was tempting |
|---|---|---|---|
| `Turtle` ×4 (`2LCcq8vhqJ3`, `fklSEvGm1Q8`, `c6n73UnGEP4`, `bXreDp3oSqy`) | Poly by Google | **CC-BY 3.0** | the obvious `scree-shell` fit |
| `Turtle` (`0Sylqo1dCfu`) | jeremy | **CC-BY 3.0** | ditto |
| `Turtle` (`RvTg4XTOUH`) | marioba | **CC-BY 3.0** | ditto |
| `Long-Necked Turtle` (`4kQR07PFTq`) | Crispy_Prawn | **CC-BY 3.0** | ditto |
| `Golem` (`aqrX9Hly1W`) | joney_lol | **CC-BY 3.0** | `scree-shell` rock-golem reading |
| `Slime Enemy` (`SW5h0gbCtq`) | J-Toastie | **CC-BY 3.0** | `reed-nibbler` |
| `Slime Enemy` (`6O6XUMssAW`, `kYEhGbVpvj`) | Charlie | **CC-BY 3.0** | `reed-nibbler` |
| `Simple Green Slime` (`az-ryr8W44N`) | Garrett LeFever | **CC-BY 3.0** | `reed-nibbler` |
| `Eel` (`eRb-GgLCnA7`) | Poly by Google | **CC-BY 3.0** | literally named for the `weir-eel` slot |

`Turtle Character` (`xmwfRzGvPv`, Polygonal Mind) **is** CC0 but is a static humanoid avatar with no
rig and no animations, so it was passed over for the animated crab.
