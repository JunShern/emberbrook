"""overworld2_build.py — build tools/blends/overworld-proto2.blend (styles E–H).

  Blender -b --factory-startup -P tools/overworld2_build.py -- [e,f,g,h]

ROUND 2.  The user picked style D (textured naturalistic) out of round 1 and asked
for four variants pushed further toward realism, under one hard constraint: the
world map must cost FAR LESS authoring time than a town.  So round 2 does not
re-author anything — it imports round 1:

    overworld_lib.Field        the one analytic valley field, unchanged
    overworld_build.build_base the same blockout geometry, unchanged
    overworld_build.dusk_rig   the same dusk key, unchanged (the comparison holds)

and spends its entire budget on FOUR DIFFERENT TERRAIN/MATERIAL PIPELINES:

  E  PAINTED NATURALISM  bake albedo, bake the dusk LIGHTING on top of it, ship the
                         terrain UNLIT (emissive).  Long shadows and AO are painted
                         into the map.  2 Cycles bakes/tile.  Naturalism from light.
  F  PBR MINIATURE       NO bake at all.  Four tiled PolyHaven material slots on the
                         terrain (diffuse + normal + roughness), triplanar so cliffs
                         do not smear.  Crisp at any camera distance.  0 bakes/tile.
                         Naturalism from material.
  G  RELIEF MAP          six altitude/slope bands (meadow→scrub→scree→rock→snow),
                         macro albedo baked at 2048 with AO multiplied in, plus a
                         TILED DETAIL NORMAL on a second UV set (glTF allows the
                         normalTexture its own TEXCOORD).  Micro-relief displacement
                         on the mesh; sparse props.  2 bakes/tile.  Naturalism from
                         landform.
  H  LUSH CANOPY         cheapest ground of the four (one plain albedo bake) and the
                         whole budget in alpha-masked foliage: procedural leaf and
                         grass atlases, crossed canopy cards, meadow scatter,
                         hedgerows shaping the road into a corridor.  1 bake/tile.
                         Naturalism from vegetation.

EVERY variant carries boat_tar at the new village dock, and every variant names its
foliage veg_* (the runtime treats veg_ as never-standable).
"""
import bpy, bmesh, math, os, sys, time
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overworld_lib as L
import overworld_build as B
import overworld2_lib as O2

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEX = os.path.join(ROOT, "tools/textures")
TEXO = os.path.join(TEX, "overworld")
OUT_BLEND = os.path.join(ROOT, "tools/blends/overworld-proto2.blend")

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STYLES = tuple(argv[0].split(",")) if argv and argv[0] != "all" else ("e", "f", "g", "h")

srgb = B.srgb
sstep = L.sstep

# ---- classes: round 1's 0..19 plus round 2's boat / foliage roles ------------
(GRASS, GRASS_HI, AUTUMN, ROCK, PEAK, SAND, DIRT, WATER, WALL, ROOF, WOOD, STONE,
 FOL_A, FOL_B, FOL_C, TRUNK, EMIT, BASE, METAL, MIST) = range(20)
TAR, CANVAS, ROPE, LEAF, TUFT, LAMP = range(20, 26)

# GROUP maps an art class to the exported material it lands in.  Round 1's table is
# module state on overworld_build; extending it is how round 2's new classes reach
# their own materials without touching a single round-1 line.
B.GROUP.update({LEAF: "veg", TUFT: "veg", LAMP: "emit"})

PAL2 = {
    # E — painted naturalism: a real dusk palette, saturated where the light lands
    "e": {GRASS: "6b8340", GRASS_HI: "55704c", AUTUMN: "b0752e", ROCK: "796e63",
          PEAK: "9c948a", SAND: "b8a074", DIRT: "8a6440", WATER: "2b6f7c",
          WALL: "dccaa6", ROOF: "9e4b37", WOOD: "6f4e30", STONE: "8a837a",
          FOL_A: "3a6642", FOL_B: "9e7a30", FOL_C: "97452e", TRUNK: "4c3826",
          EMIT: "ffb44a", BASE: "3a352e", METAL: "6d6a63", MIST: "e8d8c0",
          TAR: "23201e", CANVAS: "ab9a78", ROPE: "8a7a5c", LEAF: "4a7440",
          TUFT: "6f8a45", LAMP: "ffc46a"},
    # F — PBR miniature: near-neutral.  These colours only TINT real photo albedo,
    # so they sit close to white; anything vivid fights the material response.
    "f": {GRASS: "9aa882", GRASS_HI: "8d9c86", AUTUMN: "b39a6e", ROCK: "9c968e",
          PEAK: "aaa49c", SAND: "b7a888", DIRT: "9c8a70", WATER: "35707c",
          WALL: "cdbfa4", ROOF: "a86b52", WOOD: "8a7052", STONE: "9a948c",
          FOL_A: "5c7a4e", FOL_B: "8e7a44", FOL_C: "8a5a3e", TRUNK: "6a5540",
          EMIT: "ffb44a", BASE: "44403a", METAL: "7d7a72", MIST: "e8d8c0",
          TAR: "2a2724", CANVAS: "c4b294", ROPE: "9a8a68", LEAF: "5e7a48",
          TUFT: "7d8a5c", LAMP: "ffc46a"},
    # G — relief map: the muted, slightly desaturated palette of an aerial photo
    "g": {GRASS: "76825a", GRASS_HI: "6a7358", AUTUMN: "9c8a5c", ROCK: "8b857c",
          PEAK: "b9b5ae", SAND: "b0a184", DIRT: "8f7a5e", WATER: "3a6b78",
          WALL: "c8bda6", ROOF: "94614c", WOOD: "7a6448", STONE: "938d84",
          FOL_A: "48603f", FOL_B: "7c6c42", FOL_C: "7a4f38", TRUNK: "584a38",
          EMIT: "ffb44a", BASE: "4a463f", METAL: "7d7a72", MIST: "e8dccc",
          TAR: "2a2724", CANVAS: "c4b294", ROPE: "9a8a68", LEAF: "4e6a42",
          TUFT: "77835a", LAMP: "ffc46a"},
    # H — lush canopy: deep, wet greens; the ground barely shows through
    "h": {GRASS: "4e7038", GRASS_HI: "3f6440", AUTUMN: "5d7a30", ROCK: "6e6a5e",
          PEAK: "918a80", SAND: "6e8040", DIRT: "7a5c3a", WATER: "27707a",
          WALL: "d4c39e", ROOF: "94462f", WOOD: "63462a", STONE: "7e7a70",
          FOL_A: "2f5c34", FOL_B: "6d8a2e", FOL_C: "8a4026", TRUNK: "43331f",
          EMIT: "ffb44a", BASE: "32302a", METAL: "6d6a63", MIST: "dfd4bc",
          TAR: "201d1b", CANVAS: "9a8965", ROPE: "857552", LEAF: "3c6a30",
          TUFT: "5c7a34", LAMP: "ffc46a"},
}
B.PAL.update(PAL2)
B.PAL_LIN.update({s: {c: srgb(h) for c, h in d.items()} for s, d in PAL2.items()})
PAL_LIN = B.PAL_LIN


# ------------------------------------------------------------------ node helpers
def tex(nt, path, uv_out, tile=(1.0, 1.0), noncolor=False):
    n = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(path, check_existing=True)
    n.image = img
    n.extension = "REPEAT"
    n.interpolation = "Smart"
    if noncolor:
        img.colorspace_settings.name = "Non-Color"
    if tile != (1.0, 1.0):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (tile[0], tile[1], 1.0)
        nt.links.new(uv_out, mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    else:
        nt.links.new(uv_out, n.inputs["Vector"])
    return n


def mixn(nt, a, b, fac_out=None, fac=0.5, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    s = lambda nm, t: [x for x in n.inputs if x.name == nm and x.type == t][0]
    nt.links.new(a, s("A", "RGBA"))
    nt.links.new(b, s("B", "RGBA"))
    if fac_out is not None:
        nt.links.new(fac_out, s("Factor", "VALUE"))
    else:
        s("Factor", "VALUE").default_value = fac
    return n.outputs["Result"]


def attr_node(nt, name):
    a = nt.nodes.new("ShaderNodeVertexColor")
    a.layer_name = name
    return a


def write_masks(me, arrays, name):
    """Write up to three per-vertex mask arrays into one CORNER colour attribute."""
    at = me.color_attributes.get(name) or me.color_attributes.new(name, "FLOAT_COLOR", "CORNER")
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    d = np.ones((len(me.loops), 4))
    for i, a in enumerate(arrays[:3]):
        d[:, i] = a.ravel()[lv]
    at.data.foreach_set("color", d.ravel())
    return at


def unlit(mat, img):
    """Ship a baked map as UNLIT: black base colour, the map on Emission.

    glTF carries this as emissiveTexture + a black baseColorFactor, so three.js
    renders the painted art exactly as baked and no runtime light doubles up on it.
    This is the pre-rendered-background contract applied to a 3D tile."""
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Emission Strength"].default_value = 1.0
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    return mat


def pbr_mat(name, base, nor=None, rough=None, tile=1.0, vcol=False, gain_to=0.44,
            uvname="UVMap", rough_default=0.9, alpha_clip=False, twosided=False):
    """One exportable PBR material: baseColor [* COLOR_0] + normal + roughness.

    All three are plain image->socket links, which is precisely the subset glTF
    carries.  When vcol is on, the class colour is pre-divided by the albedo's mean
    luminance (round-1 finding: baseColorTexture * COLOR_0 only ever DARKENS)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough_default
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = uvname
    bt = tex(nt, base, uv.outputs["UV"], (tile, tile))
    col = bt.outputs["Color"]
    if vcol:
        col = mixn(nt, bt.outputs["Color"], attr_node(nt, "Col").outputs["Color"],
                   fac=1.0, blend="MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    if nor and os.path.exists(nor):
        nt_ = tex(nt, nor, uv.outputs["UV"], (tile, tile), noncolor=True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 1.0
        nt.links.new(nt_.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if rough and os.path.exists(rough):
        rt = tex(nt, rough, uv.outputs["UV"], (tile, tile), noncolor=True)
        nt.links.new(rt.outputs["Color"], b.inputs["Roughness"])
    if alpha_clip:
        # glTF alphaMode MASK is NO LONGER read from Material.blend_method — since
        # Blender 4.2 the exporter sniffs the NODE TREE for an explicit clip, and a
        # material with blend_method='CLIP' but a bare Alpha link exports as BLEND
        # (order-dependent, sorts wrong, and not what a foliage card wants).
        # Alpha -> Math(GREATER_THAN, cutoff) -> BSDF Alpha is the pattern it detects.
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(bt.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs["Value"], b.inputs["Alpha"])
        m.blend_method = "CLIP"
        m.alpha_threshold = 0.5
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    if twosided:
        m.use_backface_culling = False
    m["albedo_mean"] = albedo_mean(bt.image)
    m["vcol_gain"] = float(np.clip(gain_to / max(m["albedo_mean"], 0.03), 1.0, 3.2))
    return m


_MEAN = {}


def albedo_mean(img):
    """Mean luminance of the OPAQUE pixels.  An alpha atlas is mostly transparent
    black, so a plain mean would send the vertex-colour gain straight to its clamp
    and blow the foliage out to white."""
    if img.name in _MEAN:
        return _MEAN[img.name]
    a = np.zeros(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(-1, 4)
    op = a[:, 3] > 0.5
    v = float(a[op, :3].mean()) if op.sum() > 64 else float(a[:, :3].mean())
    _MEAN[img.name] = v
    return v


def apply_gain(ob, gain, faces=None):
    ca = ob.data.color_attributes.get("Col")
    if ca is None:
        return
    d = np.zeros(len(ca.data) * 4)
    ca.data.foreach_get("color", d)
    d = d.reshape(-1, 4)
    if faces is None:
        d[:, :3] = np.clip(d[:, :3] * gain, 0.0, 1.0)
    else:
        sel = np.zeros(len(d), bool)
        for pi in faces:
            for li in ob.data.polygons[pi].loop_indices:
                sel[li] = True
        d[sel, :3] = np.clip(d[sel, :3] * gain, 0.0, 1.0)
    ca.data.foreach_set("color", d.ravel())


def assign_slots2(ob, mats, cls, group):
    groups = sorted({group.get(int(c), "matte") for c in cls})
    ob.data.materials.clear()
    for g in groups:
        ob.data.materials.append(mats[g])
    order = {g: i for i, g in enumerate(groups)}
    mi = np.array([order[group.get(int(c), "matte")] for c in cls], dtype=np.int32)
    ob.data.polygons.foreach_set("material_index", mi)
    return groups


# ---------------------------------------------------------------- terrain bands
def bands(F, style):
    """Per-vertex layer weights for the terrain blend.  Returns (layers, W) where
    layers is [(name, diff, nor, rough, tile_u, tile_v)] and W is (NV, len(layers))
    normalised.  layers[0] is the base; W[:,1:] drive the mix chain."""
    w7 = F.w.reshape(-1, 7)
    alt = (F.H - F.wl).ravel()
    sl = F.slope.ravel()
    dr = F.dr.ravel()
    drd = F.drd.ravel()
    P = lambda n: os.path.join(TEXO, n)
    Q = lambda n: os.path.join(TEX, n)

    if style in ("e",):
        layers = [("grass", P("leafy_grass_diff_1k.jpg"), P("leafy_grass_nor_gl_1k.jpg"),
                   P("leafy_grass_rough_1k.jpg"), 26, 20),
                  ("dry", P("withered_grass_diff_1k.jpg"), P("withered_grass_nor_gl_1k.jpg"),
                   P("withered_grass_rough_1k.jpg"), 17, 13),
                  ("rock", Q("rock_face_03_Diffuse.jpg"), Q("rock_face_03_nor_gl.jpg"),
                   Q("rock_face_03_Rough.jpg"), 13, 10),
                  ("dirt", P("stony_dirt_path_diff_1k.jpg"), P("stony_dirt_path_nor_gl_1k.jpg"),
                   P("stony_dirt_path_rough_1k.jpg"), 30, 23)]
        W = np.stack([w7[:, GRASS] + w7[:, GRASS_HI],
                      w7[:, AUTUMN] + w7[:, SAND],
                      w7[:, ROCK] + w7[:, PEAK],
                      w7[:, DIRT]], -1)
    elif style == "f":
        layers = [("grass", P("leafy_grass_diff_1k.jpg"), P("leafy_grass_nor_gl_1k.jpg"),
                   P("leafy_grass_rough_1k.jpg"), 30, 30),
                  ("dry", P("withered_grass_diff_1k.jpg"), P("withered_grass_nor_gl_1k.jpg"),
                   P("withered_grass_rough_1k.jpg"), 30, 30),
                  ("rock", Q("rock_face_03_Diffuse.jpg"), Q("rock_face_03_nor_gl.jpg"),
                   Q("rock_face_03_Rough.jpg"), 30, 30),
                  ("dirt", P("stony_dirt_path_diff_1k.jpg"), P("stony_dirt_path_nor_gl_1k.jpg"),
                   P("stony_dirt_path_rough_1k.jpg"), 30, 30)]
        # dry is halved: at argmax-per-face resolution a straw photo covering half
        # the valley is what made the first F pass read as one brown sheet
        W = np.stack([w7[:, GRASS] + w7[:, GRASS_HI] + 0.35 * w7[:, AUTUMN],
                      0.5 * (w7[:, AUTUMN] + w7[:, SAND]),
                      w7[:, ROCK] + w7[:, PEAK],
                      w7[:, DIRT]], -1)
    elif style == "g":
        # the landform IS the art direction: five bands by altitude x slope, plus
        # the road corridor.  Nothing here reads the class table round 1 built.
        rockw = sstep(0.62, 1.25, sl)
        steep = sstep(1.05, 1.70, sl)
        # snow_02 over the whole rim turns the tile into a chalk model: the band has
        # to start well ABOVE the rim's shoulder and thin out on the steepest faces,
        # which is also how real snow lies
        # tuned against the field's own statistics (alt p90 = 25.7, slope p90 = 1.71)
        # rather than by eye: snow lands on the top ~8% and slides off the steepest
        # faces, scree takes the shoulders, bare rock the true crags
        snow = sstep(23.5, 29.5, alt) * (1.0 - 0.80 * sstep(1.30, 2.20, sl))
        scree = sstep(0.85, 1.45, sl) * (1.0 - snow) * sstep(3.0, 9.0, alt)
        scrub = (1.0 - rockw) * sstep(5.0, 12.0, alt) * (1.0 - sstep(15.0, 22.0, alt))
        meadow = (1.0 - rockw) * (1.0 - sstep(6.0, 13.0, alt)) + 0.35 * (1.0 - sstep(2.0, 7.0, dr))
        dirt = (1.0 - sstep(0.95, 2.1, drd)) * sstep(2.2, 4.4, dr)
        layers = [("meadow", P("aerial_grass_rock_diff_1k.jpg"), P("aerial_grass_rock_nor_gl_1k.jpg"),
                   P("aerial_grass_rock_rough_1k.jpg"), 24, 18),
                  ("scrub", P("sparse_grass_diff_1k.jpg"), P("sparse_grass_nor_gl_1k.jpg"),
                   P("sparse_grass_rough_1k.jpg"), 20, 15),
                  ("scree", P("aerial_rocks_02_diff_1k.jpg"), P("aerial_rocks_02_nor_gl_1k.jpg"),
                   P("aerial_rocks_02_rough_1k.jpg"), 22, 17),
                  ("rock", P("dry_riverbed_rock_diff_1k.jpg"), P("dry_riverbed_rock_nor_gl_1k.jpg"),
                   P("dry_riverbed_rock_rough_1k.jpg"), 15, 12),
                  ("snow", P("snow_02_diff_1k.jpg"), P("snow_02_nor_gl_1k.jpg"),
                   P("snow_02_rough_1k.jpg"), 12, 9),
                  ("dirt", P("stony_dirt_path_diff_1k.jpg"), P("stony_dirt_path_nor_gl_1k.jpg"),
                   P("stony_dirt_path_rough_1k.jpg"), 30, 23)]
        W = np.stack([meadow, scrub, scree, steep, snow, dirt], -1)
    else:                                                     # h
        layers = [("lush", P("leafy_grass_diff_1k.jpg"), P("leafy_grass_nor_gl_1k.jpg"),
                   P("leafy_grass_rough_1k.jpg"), 30, 23),
                  ("floor", Q("forest_ground_04_Diffuse.jpg"), Q("forest_ground_04_nor_gl.jpg"),
                   Q("forest_ground_04_Rough.jpg"), 22, 17),
                  ("moss", P("mossy_rock_diff_1k.jpg"), P("mossy_rock_nor_gl_1k.jpg"),
                   P("mossy_rock_rough_1k.jpg"), 15, 12),
                  ("dirt", P("stony_dirt_path_diff_1k.jpg"), P("stony_dirt_path_nor_gl_1k.jpg"),
                   P("stony_dirt_path_rough_1k.jpg"), 30, 23)]
        shade = sstep(0.28, 0.75, sl) * (1.0 - sstep(14.0, 22.0, alt))
        W = np.stack([w7[:, GRASS] + w7[:, GRASS_HI] + w7[:, AUTUMN] + 0.6 * w7[:, SAND],
                      0.55 * shade,
                      sstep(0.80, 1.45, sl) + w7[:, PEAK],
                      w7[:, DIRT]], -1)

    W = np.maximum(W, 0.0)
    base = np.clip(1.0 - W[:, 1:].sum(-1), 0.0, 1.0)
    W[:, 0] = np.maximum(W[:, 0], base)
    W = W / np.maximum(W.sum(-1, keepdims=True), 1e-6)
    # two box passes so a mask boundary never lands on a single facet
    Wg = W.reshape(L.NX, L.NY, -1)
    for _ in range(2):
        k = np.zeros_like(Wg)
        for dx_, dy_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            k += np.roll(np.roll(Wg, dx_, 0), dy_, 1)
        Wg = k / 5.0
    W = Wg.reshape(-1, len(layers))
    W = W / np.maximum(W.sum(-1, keepdims=True), 1e-6)
    return layers, W


def art_colors(F, style):
    """The per-vertex art-direction colour the photo detail multiplies against."""
    pal = PAL_LIN[style]
    alt = (F.H - F.wl).ravel()
    sl = F.slope.ravel()
    dr = F.dr.ravel()
    if style == "g":
        # G's palette follows the same bands its textures do
        _, W = bands(F, "g")
        P = np.array([srgb(h) for h in ("7c8a5e", "8a8a68", "9a938a", "8d8780",
                                        "d8dee4", "8f7a5e")])
        c = W @ P
    else:
        P = np.array([pal[c] for c in range(7)])
        c = F.w.reshape(-1, 7) @ P
    if style == "e":
        # richer shifts by moisture / altitude / aspect — the "painted" part
        moist = (1.0 - sstep(3.0, 26.0, dr))[:, None]
        c = c * (1 - 0.28 * moist) + srgb("406b33") * (0.28 * moist)
        dry = (sstep(9.0, 24.0, alt) * (1.0 - sstep(0.9, 1.6, sl)))[:, None]
        c = c * (1 - 0.24 * dry) + srgb("a89a63") * (0.24 * dry)
        cool = sstep(16.0, 32.0, alt)[:, None]
        c = c * (1 - 0.22 * cool) + srgb("6b7288") * (0.22 * cool)
        gx, gy = np.gradient(F.H, L.STEP, L.STEP)
        nrm = 1.0 / np.sqrt(1.0 + gx * gx + gy * gy)
        aspect = ((-gx * 0.262 + gy * 0.720) * nrm + 0.643 * nrm).ravel()
        a = np.clip((aspect - 0.45) / 0.5, -1.0, 1.0)[:, None]
        c = c * (1 - 0.12 * np.abs(a)) + np.where(a > 0, srgb("e0b070"), srgb("5f6d8c")) * (0.12 * np.abs(a))
    if style == "h":
        wet = (1.0 - sstep(2.0, 34.0, dr))[:, None]
        c = c * (1 - 0.34 * wet) + srgb("35682e") * (0.34 * wet)
        shd = sstep(0.25, 0.85, sl)[:, None]            # damp shade under the canopy
        c = c * (1 - 0.22 * shd) + srgb("2c4a2a") * (0.22 * shd)
    c *= (1.0 + (F.shade.ravel() - 1.0) * 0.55)[:, None]
    return np.clip(c, 0.0, 1.0)


def write_vcol(ob, cols):
    me = ob.data
    a = B.ensure_col(me)
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    d = np.ones((len(me.loops), 4))
    d[:, :3] = cols[lv]
    a.data.foreach_set("color", d.ravel())


# ------------------------------------------------------------ terrain pipelines
def blend_chain(nt, uv_out, layers, mask_socks, which):
    """Mix `which` ('diff' | 'nor' | 'rough') maps of every layer by the masks."""
    idx = {"diff": 1, "nor": 2, "rough": 3}[which]
    nodes = [tex(nt, l[idx], uv_out, (l[4], l[5]), noncolor=(which != "diff"))
             for l in layers]
    col = nodes[0].outputs["Color"]
    for i in range(1, len(layers)):
        col = mixn(nt, col, nodes[i].outputs["Color"], mask_socks[i - 1])
    return col


def bake_terrain(ground, F, sc, style, size=2048, light=False, ao=False, made=None):
    """The shared bake recipe.  Returns the finished albedo image.

    HIDE-BEFORE-BAKE is not optional: walk_road / walk_village_green / walk_dockpath
    float 0.06-0.09u ABOVE the terrain and then sample the very map they are baked
    into.  Left visible they cast a hard shadow onto their own ground, and the road
    comes out of an E-style lighting bake pure black.  The 1.45u scale capsules do
    the same, and their shadow would be baked into the world forever."""
    B.planar_uv_terrain(ground)
    me = ground.data
    layers, W = bands(F, style)
    write_vcol(ground, art_colors(F, style))
    n_masks = len(layers) - 1
    write_masks(me, [W[:, 1 + i] for i in range(min(3, n_masks))], "masks")
    if n_masks > 3:
        write_masks(me, [W[:, 4 + i] for i in range(n_masks - 3)], "masks2")

    m = bpy.data.materials.new("ow_%s_bakesrc" % style)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = 0.95
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"

    seps = []
    for nm in ("masks", "masks2"):
        if nm in me.color_attributes:
            s = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(attr_node(nt, nm).outputs["Color"], s.inputs["Color"])
            seps.append(s)
    socks = []
    for i in range(n_masks):
        socks.append(seps[i // 3].outputs[i % 3])

    col = blend_chain(nt, uvn.outputs["UV"], layers, socks, "diff")
    # round-1 finding, kept: the photo supplies DETAIL (luminance remapped around
    # 1.0) and a little hue; the art-directed palette supplies the COLOUR.  Straight
    # photo albedo turns a 120x90 tile into one muddy sheet.
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(col, bw.inputs["Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.05
    mr.inputs["From Max"].default_value = 0.60
    mr.inputs["To Min"].default_value = 0.62
    mr.inputs["To Max"].default_value = 1.48
    mr.clamp = True
    nt.links.new(bw.outputs["Val"], mr.inputs["Value"])
    hue = {"e": 0.26, "g": 0.34, "h": 0.22}.get(style, 0.20)
    tinted = mixn(nt, attr_node(nt, "Col").outputs["Color"], col, fac=hue)
    final = mixn(nt, tinted, mr.outputs["Result"], fac=1.0, blend="MULTIPLY")
    nt.links.new(final, bs.inputs["Base Color"])

    me.materials.clear()
    me.materials.append(m)

    hidden = []
    for k in ("road", "green", "dockpath", "ref", "refdock"):
        if made and k in made:
            made[k].hide_render = True
            hidden.append(made[k])

    img = bpy.data.images.new("ow_%s_terrain" % style, size, size)
    img.filepath_raw = os.path.join(TEXO, "ow_%s_terrain.png" % style)
    img.file_format = "PNG"
    O2.set_bake_target(m, img)
    t0 = time.time()
    O2.bake(sc, ground, img, "DIFFUSE", samples=4, direct=False, indirect=False,
            color=True, margin=24)
    print("  bake albedo %dpx  %.1fs" % (size, time.time() - t0))
    alb = O2.img_array(img)

    if ao:
        aoi = bpy.data.images.new("ow_%s_ao" % style, size // 2, size // 2)
        O2.set_bake_target(m, aoi)
        t0 = time.time()
        O2.bake(sc, ground, aoi, "AO", samples=48, margin=16)
        print("  bake AO %dpx  %.1fs" % (size // 2, time.time() - t0))
        a = O2.img_array(aoi)[..., 0]
        a = np.repeat(np.repeat(a, 2, 0), 2, 1)[:size, :size]
        alb[..., :3] *= (0.34 + 0.66 * a)[..., None]
        bpy.data.images.remove(aoi)

    if light:
        li = bpy.data.images.new("ow_%s_light" % style, size, size)
        O2.set_bake_target(m, li)
        t0 = time.time()
        O2.bake(sc, ground, li, "DIFFUSE", samples=64, direct=True, indirect=True,
                color=False, margin=24)
        print("  bake LIGHT %dpx  %.1fs" % (size, time.time() - t0))
        lg = O2.img_array(li)[..., :3]
        # the render is Standard-transform, so the baked light must be exposure-
        # matched by hand: a plain multiply crushes the shadow side to mud
        lg = np.clip(lg, 0.0, 4.0)
        lg = lg * 0.92 + 0.16
        alb[..., :3] = np.clip(alb[..., :3] * lg, 0.0, 1.0)
        bpy.data.images.remove(li)

    for o in hidden:
        o.hide_render = False
    alb[..., 3] = 1.0
    O2.img_write(img, alb)
    img.save()
    print("  terrain map ->", img.filepath_raw)
    for nm in ("masks", "masks2"):
        if nm in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[nm])
    return img, layers


def micro_relief(ob, F, amp=0.11, seed=4, fr=None):
    """Style G only: break the analytic field with fine relief so the landform
    reads as rock rather than as a mathematical surface.  Masked to zero along the
    road/village/dock so the 0.09u walk ribbons never poke through."""
    me = ob.data
    n = len(me.vertices)
    co = np.zeros(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    rng = np.random.RandomState(seed)
    x, y = co[:, 0], co[:, 1]
    d = (np.sin(x * 1.07 + 0.4) * np.sin(y * 0.93 - 1.1)
         + 0.62 * np.sin(x * 2.31 - 2.0) * np.sin(y * 2.11 + 0.7)
         + 0.38 * np.sin(x * 4.7 + 1.2) * np.sin(y * 4.3 - 0.3))
    sl = F.slope_at(x, y)
    keep = sstep(0.18, 0.75, sl)
    keep *= sstep(3.2, 6.5, F.road_dist(x, y))
    keep *= sstep(1.0, 5.0, np.abs(F.river_dist(x, y) - 0.0))
    vx, vy = L.VILLAGE
    keep *= sstep(7.0, 13.0, np.hypot(x - vx, y - vy))
    ex = np.maximum(np.abs(x) / (L.TILE_X / 2), np.abs(y) / (L.TILE_Y / 2))
    keep *= (1.0 - sstep(0.93, 1.0, ex))       # the rim must still weld to the skirt
    if fr is not None:
        keep *= (1.0 - O2.pool_w(x, y, fr))    # and the mooring basin stays flat
    co[:, 2] += d * amp * keep
    me.vertices.foreach_set("co", co.ravel())
    me.update()


# ------------------------------------------------------------------ vegetation
def build_veg(coll, F, style, name_suffix, dens, leaf_img=None, tuft_img=None):
    """Trunks (solid) + veg_ canopies (never standable).  Styles E/F/G keep round
    1's cone/blob canopies; style H swaps in alpha-masked cards."""
    trunks = B.Prop("tree_trunks")
    canopy = B.Prop("veg_canopy")
    uvs = []
    sites = O2.scatter_trees(F, 20260730, dens["n"], min_d2=dens["min_d2"],
                             cluster=dens.get("cluster", 0.0))
    for (tx, ty, gz, s, k, rz) in sites:
        if style == "h":
            trunks.cone(TRUNK, (tx, ty, gz + 0.55 * s), 0.13 * s, 0.09 * s, 1.15 * s,
                        seg=6, rz=rz)
            nc = 6
            for i in range(nc):
                a = rz + i * (2 * math.pi / nc) + 0.12 * i
                r = 0.42 * s * (0.6 + 0.5 * ((i * 7) % 5) / 4.0)
                O2.card(canopy, LEAF,
                        tx + math.cos(a) * r, ty + math.sin(a) * r,
                        gz + (0.95 + 0.30 * ((i * 3) % 4) / 3.0) * s,
                        2.30 * s, 1.55 * s, a - math.pi / 2,
                        pitch=math.radians(38 + 34 * ((i * 5) % 4) / 3.0),
                        cell=(i + int(k * 4)) % 4, uvs=uvs)
        elif k < 0.36:
            trunks.cone(TRUNK, (tx, ty, gz + 0.3 * s), 0.11 * s, 0.09 * s, 0.6 * s, seg=6, rz=rz)
            canopy.cone(FOL_A, (tx, ty, gz + 1.05 * s), 0.78 * s, 0.30 * s, 1.35 * s, seg=8, rz=rz)
            canopy.cone(FOL_A, (tx, ty, gz + 1.95 * s), 0.52 * s, 0.02 * s, 1.15 * s, seg=8, rz=rz + 0.4)
        elif k < 0.76:
            trunks.cone(TRUNK, (tx, ty, gz + 0.45 * s), 0.14 * s, 0.10 * s, 0.95 * s, seg=6, rz=rz)
            canopy.ico(FOL_B, (tx, ty, gz + 1.55 * s), (0.92 * s, 0.92 * s, 0.72 * s), subd=2, rz=rz)
            canopy.ico(FOL_B, (tx + 0.35 * s, ty - 0.28 * s, gz + 1.95 * s),
                       (0.58 * s, 0.58 * s, 0.48 * s), subd=1, rz=rz + 1.1)
        else:
            trunks.cone(TRUNK, (tx, ty, gz + 0.6 * s), 0.09 * s, 0.07 * s, 1.25 * s, seg=6, rz=rz)
            canopy.ico(FOL_C, (tx, ty, gz + 1.75 * s), (0.50 * s, 0.50 * s, 0.90 * s), subd=2, rz=rz)
    to = trunks.finish(coll)
    to.name = "tree_trunks__" + name_suffix
    to.data.name = to.name
    co = canopy.finish(coll)
    co.name = "veg_canopy__" + name_suffix
    co.data.name = co.name
    if style == "h":
        O2.apply_card_uvs(co, uvs)
    print("  %s: %d trees" % (style, len(sites)))
    return to, co, sites


def build_meadow(coll, F, style, suffix, n=1200, seed=11):
    """Style H: grass-tuft cards near the road, the village and the river — the
    places a follow camera actually gets close to."""
    p = B.Prop("veg_meadow")
    uvs = []
    rng = np.random.RandomState(seed)
    vx, vy = L.VILLAGE
    placed = 0
    tries = 0
    while placed < n and tries < 60000:
        tries += 1
        tx, ty = rng.uniform(-58, 58), rng.uniform(-44, 44)
        drd = float(F.road_dist(np.array([tx]), np.array([ty]))[0])
        dv = math.hypot(tx - vx, ty - vy)
        w = max(0.0, 1.0 - drd / 9.0) + max(0.0, 1.0 - dv / 14.0)
        if rng.rand() > min(1.0, w):
            continue
        if drd < 1.35:
            continue
        gz = float(F.sample(np.array([tx]), np.array([ty]))[0])
        wlv = float(L.water_level(np.array([F._river_dist([tx], [ty])[1][0]]))[0])
        if gz < wlv + 0.6 or float(F.slope_at(np.array([tx]), np.array([ty]))[0]) > 1.0:
            continue
        s = rng.uniform(0.6, 1.0)
        a = rng.rand() * math.pi
        for j in range(2):
            O2.card(p, TUFT, tx, ty, gz - 0.06, 0.56 * s, 0.66 * s,
                    a + j * math.pi / 2, pitch=math.radians(12 + 16 * j),
                    cell=rng.randint(4), uvs=uvs)
        placed += 1
    ob = p.finish(coll)
    ob.name = "veg_meadow__" + suffix
    ob.data.name = ob.name
    O2.apply_card_uvs(ob, uvs)
    print("  meadow tufts: %d" % placed)
    return ob


def build_hedge(coll, F, suffix, seed=13):
    """Style H: hedgerows that turn the road into a corridor.  Placed by walking
    the road spline, which is why this is six lines and not an afternoon."""
    p = B.Prop("veg_hedge")
    uvs = []
    rng = np.random.RandomState(seed)
    rd, rh = F.road, F.road_h
    tg = np.gradient(rd, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    nx, ny = -tg[:, 1], tg[:, 0]
    n = len(rd)
    for i in range(2, n - 2):
        # skip the bridge and the two town ends
        if abs(i - F.bridge_i) < 9 or i < 8 or i > n - 10:
            continue
        for side in (-1, 1):
            if rng.rand() < 0.42:
                continue
            off = 2.5 + rng.rand() * 1.5
            x = rd[i, 0] + nx[i] * side * off
            y = rd[i, 1] + ny[i] * side * off
            gz = float(F.sample(np.array([x]), np.array([y]))[0])
            if gz < float(L.water_level(np.array([F._river_dist([x], [y])[1][0]]))[0]) + 0.8:
                continue
            s = 0.85 + rng.rand() * 0.5
            a = math.atan2(tg[i, 1], tg[i, 0])
            for j in range(3):
                O2.card(p, LEAF, x, y, gz - 0.1, 1.9 * s, 1.30 * s,
                        a + j * 1.05, pitch=math.radians(15 + 24 * j),
                        cell=rng.randint(4), uvs=uvs)
    ob = p.finish(coll)
    ob.name = "veg_hedge__" + suffix
    ob.data.name = ob.name
    O2.apply_card_uvs(ob, uvs)
    print("  hedge cards: %d" % len(uvs))
    return ob


# ---------------------------------------------------------------------- cameras
def add_cameras2(sc, F, base_objs, style, D):
    B.add_cameras(sc, F, base_objs["_charpos"][:3], base_objs["_charpos"][3], style)
    # boat shot: from the VILLAGE bank, looking across the hull at the far bank —
    # the dusk key comes from the south, so this is the only side of the river that
    # puts a lit background behind the boat instead of a black cliff.
    bx, by, bz = D["boat"]
    nx, ny = D["nrm"]
    tx, ty = D["tg"]
    cx_, cy_ = D["ctr"]
    eye = (cx_ - tx * 8.0 - nx * 1.9, cy_ - ty * 8.0 - ny * 1.9, D["wl"] + 1.95)
    aim = (bx - tx * 0.2, by - ty * 0.2, bz + 0.48)
    nm = "cam_boat__%s" % style
    cd = bpy.data.cameras.new(nm)
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(42.0)
    cd.clip_start, cd.clip_end = 0.05, 900.0
    ob = bpy.data.objects.new(nm, cd)
    sc.collection.objects.link(ob)
    ob.location = Vector(eye)
    ob.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    return ob


# ------------------------------------------------------------------ style build
BUILD_S = {}

STYLE_CFG = {
    "e": dict(trees=dict(n=58, min_d2=12.0), rocks=True, rig="furled",
              bake=dict(light=True, ao=False, size=2048)),
    "f": dict(trees=dict(n=54, min_d2=12.0), rocks=True, rig="mast", bake=None),
    "g": dict(trees=dict(n=22, min_d2=34.0), rocks=True, rig="bare",
              bake=dict(light=False, ao=True, size=2048)),
    "h": dict(trees=dict(n=96, min_d2=7.0, cluster=0.45), rocks=True, rig="canopy",
              bake=dict(light=False, ao=False, size=2048)),
}


def make_scene2(style, base_objs, F, atlases):
    t_start = time.time()
    sc = bpy.data.scenes.new("style_" + style)
    col = sc.collection
    B.dusk_rig(sc, F, style)
    cfg = STYLE_CFG[style]

    # ---- exported material set -------------------------------------------
    mats = {"matte": B.new_mat("ow_%s_matte" % style, rough=0.9),
            "water": B.new_mat("ow_%s_water" % style, rough=0.28, alpha=0.82, blend=True),
            "emit": B.new_mat("ow_%s_emit" % style, rough=0.6, emit=srgb("ff9f38"), emit_str=9.0),
            "mist": B.new_mat("ow_%s_mist" % style, rough=1.0, alpha=0.2, blend=True)}
    # two coplanar alpha-blended sheets (the river strip and the basin) sort per
    # fragment and flash pale quads across the water; turning off backface show
    # makes the ordering deterministic
    for k in ("water", "mist"):
        mats[k].show_transparent_back = False
    group = dict(B.GROUP)

    # ---- copy the shared blockout ----------------------------------------
    made = {}
    for key, ob in base_objs.items():
        if key.startswith("_") or key in ("trees",):
            continue
        d = ob.copy()
        d.data = ob.data.copy()
        d.name = "%s__%s" % (ob.name, style)
        d.data.name = d.name
        col.objects.link(d)
        made[key] = d
    ground = made["ground"]
    # the mooring basin is cut into EVERY style's own terrain copy — the shared
    # field stays byte-identical to round 1 so style D remains a valid reference row
    fr = O2.pool_frame(F)
    O2.carve_pool(ground, F, fr)
    if style == "g":
        micro_relief(ground, F, fr=fr)

    # ---- vegetation --------------------------------------------------------
    trunks, canopy, sites = build_veg(col, F, style, style, cfg["trees"])
    made["trunks"], made["canopy"] = trunks, canopy
    if style == "h":
        made["meadow"] = build_meadow(col, F, style, style)
        made["hedge"] = build_hedge(col, F, style)

    # ---- the dock + boat_tar ----------------------------------------------
    cls = dict(hull=TAR, wood=WOOD, dark=TAR, canvas=CANVAS, rope=ROPE, lamp=LAMP)
    deck = B.Prop("walk_dock")
    props = B.Prop("dock_props")
    D = O2.build_dock(F, deck, props, cls, fr, boat_rig=cfg["rig"])
    head, borg, bang, root = D["head"], D["boat"], D["ang"], D["root"]
    do = deck.finish(col)
    do.name, do.data.name = "walk_dock__" + style, "walk_dock__" + style
    po = props.finish(col)
    po.name, po.data.name = "boat_tar__" + style, "boat_tar__" + style
    made["dock"], made["boat"] = do, po
    wp = B.Prop("water_pool")
    O2.pool_water(wp, WATER, fr)
    wo = wp.finish(col)
    wo.name, wo.data.name = "water_pool__" + style, "water_pool__" + style
    made["pool"] = wo
    sp = B.Prop("walk_dockpath")
    O2.dock_path(F, sp, DIRT, root, fr)
    spo = sp.finish(col)
    spo.name, spo.data.name = "walk_dockpath__" + style, "walk_dockpath__" + style
    made["dockpath"] = spo
    # a third 1.45u scale capsule on the jetty (render-only, stripped at export)
    rp = B.Prop("ref_char_dock")
    rx_, ry_ = root[0] * 0.72 + head[0] * 0.28, root[1] * 0.72 + head[1] * 0.28
    rp.cone(PEAK, (rx_, ry_, head[2] + 0.72), 0.26, 0.26, 1.05, seg=10)
    rp.ico(PEAK, (rx_, ry_, head[2] + 1.24), (0.26, 0.26, 0.26), subd=1)
    rp.ico(PEAK, (rx_, ry_, head[2] + 0.21), (0.26, 0.26, 0.21), subd=1)
    ro = rp.finish(col)
    ro.name, ro.data.name = "ref_char_dock__" + style, "ref_char_dock__" + style
    made["refdock"] = ro

    # ---- prop colours ------------------------------------------------------
    PROPKEYS = ["skirt", "water", "road", "green", "bridge", "village", "clifftown",
                "dam", "rocks", "ref", "trunks", "canopy", "dock", "boat",
                "dockpath", "refdock", "pool"] + (["meadow", "hedge"] if style == "h" else [])
    for i, key in enumerate(PROPKEYS):
        ob = made[key]
        cls_ = B.write_prop_colors(ob, style, True, 0.055, seed=41 + i)
        made[key + "_cls"] = cls_

    # ---- shading -----------------------------------------------------------
    SOFT = {"ground", "water", "pool", "rocks", "green", "canopy", "trunks"}
    if style == "g":
        SOFT.discard("rocks")
    for key, ob in made.items():
        if key.endswith("_cls") or not hasattr(ob, "data"):
            continue
        v = key in SOFT
        ob.data.polygons.foreach_set("use_smooth", [v] * len(ob.data.polygons))
        ob.data.update()

    # ---- materials --------------------------------------------------------
    # props FIRST: style E bakes the dusk lighting into the terrain map, and a bake
    # run before the props have their materials paints grey bounce onto the ground.
    props_materials(made, mats, group, F, style, atlases)
    for key in PROPKEYS:
        ob = made[key]
        if ob.data.materials:
            continue
        assign_slots2(ob, mats, made[key + "_cls"], group)

    if style == "f":
        terrain_pbr(made, mats, group, F, style)
    else:
        img, layers = bake_terrain(ground, F, sc, style, size=cfg["bake"]["size"],
                                   light=cfg["bake"]["light"], ao=cfg["bake"]["ao"],
                                   made=made)
        finish_baked(made, mats, group, F, style, img, layers, sc)

    # ---- cameras -----------------------------------------------------------
    add_cameras2(sc, F, base_objs, style, D)
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
        sc.eevee.shadow_pool_size = 1024      # 120x90u of terrain overflows the default
    except Exception:
        pass
    BUILD_S[style] = round(time.time() - t_start, 1)
    print("  style %s built in %.1fs" % (style, BUILD_S[style]))
    return sc, made


def finish_baked(made, mats, group, F, style, img, layers, sc):
    """E / G / H: the terrain wears the one baked map; road + green share it."""
    ground = made["ground"]
    tm = bpy.data.materials.new("ow_%s_terrain" % style)
    tm.use_nodes = True
    if style == "e":
        unlit(tm, img)                       # the light is IN the map — ship unlit
    else:
        nt = tm.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        b.inputs["Roughness"].default_value = 0.94
        nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap"
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if style == "g":
            # G's second UV set: a TILED detail normal on UV1 while the baked macro
            # albedo stays on UV0.  glTF gives normalTexture its own TEXCOORD, so
            # this survives export — one map's colour, another map's relief.
            det = tile_uv(ground, "UVdetail", 2.1)
            uv2 = nt.nodes.new("ShaderNodeUVMap")
            uv2.uv_map = "UVdetail"
            nn = tex(nt, os.path.join(TEXO, "aerial_rocks_02_nor_gl_1k.jpg"),
                     uv2.outputs["UV"], (1.0, 1.0), noncolor=True)
            nmn = nt.nodes.new("ShaderNodeNormalMap")
            nmn.uv_map = "UVdetail"
            nmn.inputs["Strength"].default_value = 1.0
            nt.links.new(nn.outputs["Color"], nmn.inputs["Color"])
            nt.links.new(nmn.outputs["Normal"], b.inputs["Normal"])
    ground.data.materials.clear()
    ground.data.materials.append(tm)
    for ca in list(ground.data.color_attributes):
        ground.data.color_attributes.remove(ca)

    # the green disc takes the map straight; the road needs a darkening tint on top
    # or it vanishes into the terrain it was baked from (round-1 finding, still true)
    green = made["green"]
    B.planar_uv_terrain(green)
    green.data.materials.clear()
    green.data.materials.append(tm)
    green.data.polygons.foreach_set("material_index", [0] * len(green.data.polygons))
    for ca in list(green.data.color_attributes):
        green.data.color_attributes.remove(ca)

    rm = bpy.data.materials.new("ow_%s_road" % style)
    rm.use_nodes = True
    nt = rm.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.95
    if style == "e":
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
    mult = mixn(nt, t.outputs["Color"], attr_node(nt, "Col").outputs["Color"],
                fac=1.0, blend="MULTIPLY")
    nt.links.new(mult, b.inputs["Emission Color" if style == "e" else "Base Color"])
    ROADTINT = {"e": ("dcc6a4", "d4bd9a")}.get(style, ("c49b70", "bd9468"))
    for key, tint in (("road", ROADTINT[0]), ("dockpath", ROADTINT[1])):
        ob = made[key]
        B.planar_uv_terrain(ob)
        ca = ob.data.color_attributes["Col"]
        d = np.zeros(len(ca.data) * 4).reshape(-1, 4)
        d[:, :3] = srgb(tint)
        d[:, 3] = 1.0
        ca.data.foreach_set("color", d.ravel())
        ob.data.materials.clear()
        ob.data.materials.append(rm)
        ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))


def tile_uv(ob, name, scale):
    """World-planar tiled UVs (a second set, for detail maps)."""
    me = ob.data
    uv = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    d = np.column_stack([co[lv, 0] / scale, co[lv, 1] / scale])
    uv.data.foreach_set("uv", d.ravel())
    return uv


def triplanar_uv(ob, scale, flat_thresh=0.72, F=None):
    """Per-face projection: flat faces take XY, steep faces take the dominant
    lateral axis.  One pass, no ops — and it is what stops a tiled cliff smearing.

    The axis choice reads the ANALYTIC field gradient when one is supplied, not the
    facet normal.  A herringbone-triangulated terrain flips facet normals between
    neighbours, so a per-facet choice paints a diamond lattice across every hillside
    — the single ugliest thing in the first F render."""
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    if F is not None:
        gx, gy = np.gradient(F.H, L.STEP, L.STEP)
    for poly in me.polygons:
        if F is not None:
            c = poly.center
            i = int(np.clip((c[0] + L.TILE_X / 2) / L.STEP, 0, L.NX - 1))
            j = int(np.clip((c[1] + L.TILE_Y / 2) / L.STEP, 0, L.NY - 1))
            g = (gx[i, j], gy[i, j])
            nz = 1.0 / math.sqrt(1.0 + g[0] ** 2 + g[1] ** 2)
            if nz >= flat_thresh:
                ui, vi = 0, 1
            else:
                ui, vi = (1, 2) if abs(g[0]) >= abs(g[1]) else (0, 2)
        else:
            n = poly.normal
            if abs(n[2]) >= flat_thresh:
                ui, vi = 0, 1
            else:
                ui, vi = (1, 2) if abs(n[0]) >= abs(n[1]) else (0, 2)
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (c[ui] / scale, c[vi] / scale)


def terrain_pbr(made, mats, group, F, style):
    """F: no bake.  Four tiled PBR slots straight on the terrain."""
    ground = made["ground"]
    triplanar_uv(ground, 6.2, F=F)
    layers, W = bands(F, "f")
    write_vcol(ground, art_colors(F, "f"))
    dom = np.argmax(W, axis=1)
    lv = np.zeros(len(ground.data.loops), dtype=np.int32)
    ground.data.loops.foreach_get("vertex_index", lv)
    fv = lv.reshape(-1, 3)
    fdom = np.array([np.bincount(dom[f], minlength=len(layers)).argmax() for f in fv])
    slot_mats = []
    for i, (nm, diff, nor, rgh, tu, tv) in enumerate(layers):
        m = pbr_mat("ow_f_ter_" + nm, diff, nor, rgh, tile=1.0, vcol=True,
                    gain_to=0.46)
        slot_mats.append(m)
    ground.data.materials.clear()
    for m in slot_mats:
        ground.data.materials.append(m)
    ground.data.polygons.foreach_set("material_index", fdom.astype(np.int32))
    # per-slot gain: a multiply only darkens, so each class colour is pre-divided by
    # ITS OWN albedo mean (four different photos, four different gains)
    ca = ground.data.color_attributes["Col"]
    d = np.zeros(len(ca.data) * 4)
    ca.data.foreach_get("color", d)
    d = d.reshape(-1, 4)
    gains = np.array([slot_mats[i]["vcol_gain"] for i in range(len(layers))])
    fg = gains[fdom]
    for pi, poly in enumerate(ground.data.polygons):
        for li in poly.loop_indices:
            d[li, :3] = np.clip(d[li, :3] * fg[pi], 0.0, 1.0)
    ca.data.foreach_set("color", d.ravel())
    print("  F terrain slots: %s  gains %s"
          % ([l[0] for l in layers], [round(float(g), 2) for g in gains]))

    for key, tint in (("road", "8e7a63"), ("dockpath", "8a765f"), ("green", "9aa882")):
        ob = made[key]
        triplanar_uv(ob, 2.2)
        m = pbr_mat("ow_f_" + key, os.path.join(TEXO, "stony_dirt_path_diff_1k.jpg"),
                    os.path.join(TEXO, "stony_dirt_path_nor_gl_1k.jpg"),
                    os.path.join(TEXO, "stony_dirt_path_rough_1k.jpg"),
                    tile=1.0, vcol=True) if key != "green" else \
            pbr_mat("ow_f_" + key, os.path.join(TEXO, "leafy_grass_diff_1k.jpg"),
                    os.path.join(TEXO, "leafy_grass_nor_gl_1k.jpg"),
                    os.path.join(TEXO, "leafy_grass_rough_1k.jpg"), tile=1.0, vcol=True)
        ca = ob.data.color_attributes["Col"]
        d = np.zeros(len(ca.data) * 4).reshape(-1, 4)
        d[:, :3] = np.clip(srgb(tint) * m["vcol_gain"], 0, 1)
        d[:, 3] = 1.0
        ca.data.foreach_set("color", d.ravel())
        ob.data.materials.clear()
        ob.data.materials.append(m)
        ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))


def props_materials(made, mats, group, F, style, atlases):
    """The prop half of each pipeline.  E/G/H keep the cheap vertex-colour matte
    (their money went into the terrain); F gives every prop class a real PBR set."""
    Q = lambda n: os.path.join(TEX, n)
    if style == "f":
        pm = {
            "plaster": pbr_mat("ow_f_plaster", Q("clay_plaster_Diffuse.jpg"),
                               Q("clay_plaster_nor_gl.jpg"), Q("clay_plaster_Rough.jpg"),
                               tile=0.55, vcol=True, gain_to=0.46),
            "tiles": pbr_mat("ow_f_tiles", Q("red_slate_roof_tiles_01_Diffuse.jpg"),
                             Q("red_slate_roof_tiles_01_nor_gl.jpg"),
                             Q("red_slate_roof_tiles_01_Rough.jpg"),
                             tile=0.9, vcol=True, gain_to=0.5),
            "planks": pbr_mat("ow_f_planks", Q("weathered_planks_Diffuse.jpg"),
                              Q("weathered_planks_nor_gl.jpg"), Q("weathered_planks_Rough.jpg"),
                              tile=1.1, vcol=True, gain_to=0.46),
            "stone": pbr_mat("ow_f_stone", Q("rock_face_03_Diffuse.jpg"),
                             Q("rock_face_03_nor_gl.jpg"), Q("rock_face_03_Rough.jpg"),
                             tile=0.45, vcol=True, gain_to=0.46),
            "tar": pbr_mat("ow_f_tar", Q("dark_wooden_planks_Diffuse.jpg"),
                           Q("dark_wooden_planks_nor_gl.jpg"),
                           Q("dark_wooden_planks_Rough.jpg"),
                           tile=1.4, vcol=True, gain_to=0.62),
            # model-railway lichen: a fine grass photo box-projected onto the canopy
            # blobs.  It is exactly how a physical layout makes a tree, and it is the
            # cheapest way to stop F's foliage reading as painted plastic.
            "flock": pbr_mat("ow_f_flock", os.path.join(TEXO, "leafy_grass_diff_1k.jpg"),
                             os.path.join(TEXO, "leafy_grass_nor_gl_1k.jpg"),
                             os.path.join(TEXO, "leafy_grass_rough_1k.jpg"),
                             tile=2.2, vcol=True, gain_to=0.5),
        }
        mats.update(pm)
        # PEAK is deliberately NOT remapped: it is the 1.45u scale capsule's class,
        # and a scale reference wearing a rock photo stops reading as a reference.
        group.update({WALL: "plaster", ROOF: "tiles", WOOD: "planks", TRUNK: "planks",
                      STONE: "stone", ROCK: "stone", BASE: "stone",
                      TAR: "tar", CANVAS: "planks", ROPE: "planks", METAL: "stone",
                      FOL_A: "flock", FOL_B: "flock", FOL_C: "flock"})
        # UVs for every mesh that now wears a tiled material
        for key in ("village", "clifftown", "dam", "bridge", "rocks", "boat",
                    "dock", "trunks", "skirt", "canopy"):
            B.box_uv(made[key], scale=1.0)
        for key in ("village", "clifftown", "dam", "bridge", "rocks", "boat",
                    "dock", "trunks", "skirt", "canopy"):
            ob = made[key]
            cls = made[key + "_cls"]
            gains = {}
            for gname, m in pm.items():
                gains[gname] = m["vcol_gain"]
            ca = ob.data.color_attributes.get("Col")
            if ca is None:
                continue
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            d = d.reshape(-1, 4)
            for pi, poly in enumerate(ob.data.polygons):
                g = gains.get(group.get(int(cls[pi]), "matte"), 1.0)
                for li in poly.loop_indices:
                    d[li, :3] = np.clip(d[li, :3] * g, 0.0, 1.0)
            ca.data.foreach_set("color", d.ravel())

    # style H's foliage: alpha-masked cards.  MASK (not BLEND) is the only alpha
    # mode that is order-independent, and glTF carries it.
    if style == "h":
        # vcol=False on purpose: the atlas already carries per-leaf colour variation,
        # and multiplying it by a class colour (which can only darken) is what turned
        # the first H pass into black splats.
        leaf = pbr_mat("ow_h_leaf", atlases["leaf"], None, None, tile=1.0, vcol=False,
                       alpha_clip=True, twosided=True, rough_default=0.95)
        tuft = pbr_mat("ow_h_tuft", atlases["tuft"], None, None, tile=1.0, vcol=False,
                       alpha_clip=True, twosided=True, rough_default=0.95)
        mats["veg"] = leaf
        for key, m in (("canopy", leaf), ("hedge", leaf), ("meadow", tuft)):
            ob = made[key]
            ob.data.materials.clear()
            ob.data.materials.append(m)
            ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))
    else:
        mats["veg"] = mats["matte"]


# ------------------------------------------------------------------------- main
def main():
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    t0 = time.time()
    F = L.Field()
    print("field %dx%d  village_h=%.2f  clifftown_h=%.2f  (%.1fs)"
          % (L.NX, L.NY, F.village_h, F.clifftown_h, time.time() - t0))

    base_sc = bpy.data.scenes[0]
    base_sc.name = "BASE"
    base_col = bpy.data.collections.new("base_geo")
    base_sc.collection.children.link(base_col)
    objs = B.build_base(F, base_col)

    atlases = {}
    p = os.path.join(TEXO, "veg_leaf_atlas.png")
    O2.leaf_atlas("veg_leaf_atlas", p)
    atlases["leaf"] = p
    p = os.path.join(TEXO, "veg_tuft_atlas.png")
    O2.grass_atlas("veg_tuft_atlas", p)
    atlases["tuft"] = p
    print("foliage atlases written")

    for s in STYLES:
        print("style %s…" % s)
        make_scene2(s, objs, F, atlases)

    # the perf table must quote MEASURED build cost, not a number typed by hand:
    # per-tile authoring time is half of what the user is choosing between
    import json
    qa = os.path.join(ROOT, "docs/qa/overworld")
    os.makedirs(qa, exist_ok=True)
    prev = {}
    fp = os.path.join(qa, "build_times.json")
    if os.path.exists(fp):
        prev = json.load(open(fp))
    prev.update(BUILD_S)
    json.dump(prev, open(fp, "w"), indent=1, sort_keys=True)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s  (%.1fs total)" % (OUT_BLEND, time.time() - t0))


if __name__ == "__main__":
    main()
