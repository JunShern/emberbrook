"""Material library for the Dellhollow COOKHOUSE -- the quay eatery
(`del-cookhouse-int`).

Deliberately SELF-CONTAINED, like its siblings. It reads the shared texture
manifests and calls `kit_materials.make_tex_mat`, but it imports no other
interior's material module: the inn/weapon/armor/item interiors are being
built concurrently by other agents and importing a file somebody else is
mid-edit is how a headless overnight build dies at 3am.

Palette (public/townmap/dellhollow.map.json -> style.palette):
    weathered PAINTED timber -- oxblood red, moss green, faded blue -- over a
    brown scaffold structure.

Cookhouse-specific additions over the shared palette: fired BRICK for the
oven, hearth stone, soot, copper and tinned copper for the pan wall, fish
flesh / fish skin / eel, broth and stew, onion skin, garlic, dried herbs,
root veg, lard, and a slate for the chalk menu board.

All names are prefixed `mat_k_` (k = cookhouse/kitchen) so the library can
never collide with a sibling interior's materials.
"""
import bpy, json, os, importlib.util, math

TOOLS = "/Users/junshernchan/projects/multiplayer-rpg/tools"
TEXDIR = os.path.join(TOOLS, "textures")


def _load_km():
    spec = importlib.util.spec_from_file_location(
        "kit_materials", os.path.join(TOOLS, "kit_materials.py"))
    km = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(km)
    return km


KM = _load_km()


def _merged_manifest():
    m = {}
    for fn in ("_manifest.json", "_manifest_int.json", "_manifest_itemint.json"):
        p = os.path.join(TEXDIR, fn)
        if os.path.exists(p):
            m.update(json.load(open(p)))
    return m


# material name -> manifest key. make_tex_mat names the material after its
# manifest key, so every material that shares a texture aliases the entry.
SRC = {
    "mat_k_floor":     "tex_int_floor",
    "mat_k_floor_b":   "tex_int_floor",
    "mat_k_floor_c":   "mat_int_floor",
    "mat_k_floor_d":   "mat_deck",
    "mat_k_floor_e":   "mat_int_plank",
    "mat_k_flag":      "mat_int_stone",     # flagged kitchen floor by the fire
    "mat_k_flag_b":    "mat_int_stone",
    "mat_k_wall":      "tex_int_wall",
    "mat_k_wall_b":    "tex_int_wall",
    "mat_k_beam":      "tex_int_beam",
    "mat_k_beam_b":    "tex_int_beam",
    "mat_k_counter":   "mat_int_wood",      # serving hatch top
    "mat_k_prep":      "mat_int_wood",      # scrubbed prep bench -- paler
    "mat_k_table":     "mat_int_wood",
    "mat_k_table_b":   "mat_int_wood",
    "mat_k_shelf":     "tex_int_shelf",
    "mat_k_shelf_b":   "tex_int_shelf",
    "mat_k_green":     "mat_wallwood",
    "mat_k_green_b":   "mat_wallwood",
    "mat_k_green_c":   "mat_wallwood",
    "mat_k_oxblood":   "mat_wallwood_dark",
    "mat_k_oxblood_b": "mat_wallwood_dark",
    "mat_k_blue":      "mat_wallwood",
    "mat_k_crate":     "mat_timber",
    "mat_k_crate_b":   "tex_int_shelf",
    "mat_k_burlap":    "tex_burlap",
    "mat_k_rust":      "tex_rust",
    "mat_k_plaster":   "mat_int_plaster",
    "mat_k_stone":     "mat_int_hearth",
    "mat_k_stone_b":   "mat_int_stone",
    "mat_k_brick":     "mat_int_hearth",    # fired brick: red-tinted hearth
    "mat_k_brick_b":   "mat_int_hearth",
    "mat_k_soot":      "mat_int_hearth",
    "mat_k_soot_b":    "mat_int_stone",
    "mat_k_rug":       "mat_int_rug",
    "mat_k_linen":     "mat_int_linen",
    "mat_k_apron":     "mat_int_linen",
    "mat_k_sacking":   "tex_burlap",
}


def _map_node(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "MAPPING")


def tex(name, offset=(0, 0, 0), rot=(0, 0, 0), **kw):
    """make_tex_mat against the merged manifest, then de-correlate the tile.

    The kit projects textures in OBJECT space, so a large single-object surface
    (floor, wall cladding) repeats one 1k tile visibly. Variants of the same
    source with different offset/rotation/darken, dealt out board by board, are
    what kill that.
    """
    KM.MANIFEST = _merged_manifest()
    KM.MANIFEST[name] = KM.MANIFEST[SRC[name]]
    kw.setdefault("moss", 0.0)          # moss is world-up driven: wrong indoors
    mat = KM.make_tex_mat(name, **kw)
    mp = _map_node(mat)
    mp.inputs["Location"].default_value = offset
    mp.inputs["Rotation"].default_value = rot
    return mat


# ------------------------------------------------------------- procedurals

def _base(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (420, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return mat, nt, b


def _noise_bump(nt, b, scale=40.0, strength=0.15, detail=6.0, space="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-620, -420)
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-420, -420)
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs[space], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (180, -420)
    bump.inputs["Strength"].default_value = strength
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return n


def _mottle(nt, b, c1, c2, scale=18.0, detail=6.0):
    """Two-tone noise into base colour -- stops flat plastic reads."""
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-820, 300)
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-620, 300)
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = (-400, 300)
    r.color_ramp.elements[0].position = 0.35
    r.color_ramp.elements[0].color = (*c1, 1)
    r.color_ramp.elements[1].position = 0.68
    r.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return r


def make_glass(name="mat_k_glass", color=(0.72, 0.82, 0.72), rough=0.06):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.48
    mat.use_backface_culling = False
    return mat


def make_broth(name="mat_k_broth", color=(0.30, 0.135, 0.038)):
    """Stew seen from above in a bowl or a pot: dark, glossy, barely
    translucent -- it is the SPECULAR that says liquid, not the colour."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.62 for c in color),
            tuple(min(1, c * 1.5) for c in color), scale=48.0)
    b.inputs["Roughness"].default_value = 0.11
    b.inputs["Transmission Weight"].default_value = 0.25
    b.inputs["IOR"].default_value = 1.34
    _noise_bump(nt, b, scale=90.0, strength=0.10)
    return mat


def make_ceramic(name, color, rough=0.22, mottle=0.9):
    mat, nt, b = _base(name)
    c2 = tuple(min(1.0, c * (1.0 + 0.35 * mottle)) for c in color)
    c1 = tuple(c * (1.0 - 0.30 * mottle) for c in color)
    _mottle(nt, b, c1, c2, scale=14.0)
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=55.0, strength=0.10)
    return mat


def make_metal(name, color, rough=0.30, metallic=1.0):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.55 for c in color), color, scale=22.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=90.0, strength=0.12)
    return mat


def make_copper(name="mat_k_copper", color=(0.62, 0.29, 0.135), rough=0.22,
                verdigris=0.0):
    """The pan wall is the cookhouse's jewellery. Hammered copper: a rougher
    dark base mottled to a bright polished crown, so each pan catches ONE
    bright arc off the fire instead of going uniformly dull.

    `verdigris` mixes a green-grey tarnish into the shadows for the older pans
    -- a wall of identically shiny copper reads as plastic.
    """
    mat, nt, b = _base(name)
    dark = tuple(c * 0.42 for c in color)
    if verdigris:
        dark = tuple(d * (1 - verdigris) + g * verdigris
                     for d, g in zip(dark, (0.115, 0.185, 0.150)))
    _mottle(nt, b, dark, tuple(min(1, c * 1.28) for c in color), scale=26.0)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=150.0, strength=0.32)   # hammer planishing
    return mat


def make_wax(name="mat_k_wax", color=(0.62, 0.56, 0.40)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.82 for c in color), color, scale=30.0)
    b.inputs["Roughness"].default_value = 0.44
    b.inputs["Subsurface Weight"].default_value = 0.28
    b.inputs["Subsurface Radius"].default_value = (0.012, 0.009, 0.006)
    _noise_bump(nt, b, scale=120.0, strength=0.20)
    return mat


def make_paper(name="mat_k_paper", color=(0.52, 0.45, 0.33), rough=0.80,
               bump=140.0):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.72 for c in color),
            tuple(min(1, c * 1.18) for c in color), scale=26.0)
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=bump, strength=0.10)
    return mat


def make_canvas(name="mat_k_canvas", color=(0.34, 0.30, 0.22), bump=220.0,
                strength=0.35):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.7 for c in color),
            tuple(min(1, c * 1.25) for c in color), scale=40.0)
    b.inputs["Roughness"].default_value = 0.90
    _noise_bump(nt, b, scale=bump, strength=strength)
    return mat


def make_leather(name="mat_k_leather", color=(0.115, 0.065, 0.035)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.65 for c in color),
            tuple(min(1, c * 1.5) for c in color), scale=24.0)
    b.inputs["Roughness"].default_value = 0.55
    _noise_bump(nt, b, scale=180.0, strength=0.28)
    return mat


# ------------------------------------------------------------------- food

def make_fishflesh(name="mat_k_fishflesh", color=(0.62, 0.36, 0.30)):
    """A filleted fish on the block. Wet, subsurface-pink, faintly banded --
    it is the one CLEAN bright note in a room of browns and it has to read as
    food at 30px, so it keeps a hard specular and a pale mottle."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.68 for c in color),
            tuple(min(1, c * 1.35) for c in color), scale=55.0)
    b.inputs["Roughness"].default_value = 0.16
    b.inputs["Subsurface Weight"].default_value = 0.42
    b.inputs["Subsurface Radius"].default_value = (0.030, 0.014, 0.011)
    _noise_bump(nt, b, scale=170.0, strength=0.22)
    return mat


def make_fishskin(name="mat_k_fishskin", color=(0.135, 0.165, 0.185)):
    """Whole fish in the crate: dark blue-grey backs with a cold specular
    sheen, so the crate reads as a heap of wet silver rather than as mud."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.55 for c in color),
            tuple(min(1, c * 3.4) for c in color), scale=34.0)
    b.inputs["Roughness"].default_value = 0.10
    b.inputs["Metallic"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 0.65
    b.inputs["Coat Roughness"].default_value = 0.09
    _noise_bump(nt, b, scale=260.0, strength=0.30)
    return mat


def make_eel(name="mat_k_eel", color=(0.055, 0.062, 0.038)):
    """The barrel of eels. Very dark olive, VERY wet -- the whole prop works
    on the coat highlight running along each back. Without the coat the barrel
    is a black hole, which the brief forbids outright."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.6 for c in color),
            tuple(min(1, c * 4.2) for c in color), scale=20.0)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.05
    _noise_bump(nt, b, scale=120.0, strength=0.28)
    return mat


def make_onion(name="mat_k_onion", color=(0.52, 0.34, 0.115)):
    """Papery onion skin: warm gold, translucent at the edges, satin."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.62 for c in color),
            tuple(min(1, c * 1.30) for c in color), scale=30.0)
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (0.022, 0.015, 0.006)
    _noise_bump(nt, b, scale=200.0, strength=0.28)
    return mat


def make_herb(name="mat_k_herb", color=(0.118, 0.135, 0.072)):
    """Bundles drying overhead. DRIED, so grey-green and matte -- fresh green
    would read as a houseplant and break the smoke-cured story."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.55 for c in color),
            tuple(min(1, c * 1.9) for c in color), scale=42.0)
    b.inputs["Roughness"].default_value = 0.88
    _noise_bump(nt, b, scale=260.0, strength=0.40)
    return mat


def make_slate(name="mat_k_slate", color=(0.038, 0.040, 0.043)):
    """The chalk MENU board. Very dark but NOT black -- a pure black rectangle
    on the back wall is exactly the 'black region larger than a fist' the brief
    forbids, so it keeps a dusty sheen and a chalk haze."""
    mat, nt, b = _base(name)
    _mottle(nt, b, color, (0.105, 0.108, 0.112), scale=16.0)
    b.inputs["Roughness"].default_value = 0.62
    _noise_bump(nt, b, scale=110.0, strength=0.16)
    return mat


def make_chalk(name="mat_k_chalk", color=(0.72, 0.71, 0.66)):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.95
    return mat


# ------------------------------------------------------------- emissive

def make_emissive(name, color=(1.0, 0.58, 0.24), strength=14.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (180, 0)
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_emissive_cam(name, color=(1.0, 0.58, 0.24), strength=14.0):
    """Emissive to the CAMERA, transparent to everything else.

    The kit lesson: a plain emission surface is opaque to all rays, so an
    emissive lamp pane sitting in front of its own practical light blocks that
    light from reaching the room. Mixing to Transparent on non-camera rays lets
    the practical do the lighting while the pane does the look.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (500, 0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (300, -140)
    lp = nt.nodes.new("ShaderNodeLightPath"); lp.location = (300, 240)
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (300, 60)
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(e.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_dusk_pane(name="mat_k_dusk", strength=0.62):
    """Window glass reading as the dusk sky in the gorge: warm low band, cool
    blue above. CAMERA RAYS ONLY -- see make_emissive_cam; with a plain
    emission here the sun outside cannot get through the opening at all."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (700, 0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (500, -140)
    lp = nt.nodes.new("ShaderNodeLightPath"); lp.location = (500, 260)
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (380, 0)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], mix.inputs[2])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-500, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-320, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-140, 0)
    mr.inputs["From Min"].default_value = 0.9
    mr.inputs["From Max"].default_value = 2.3
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = (60, 0)
    cr = r.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (1.0, 0.44, 0.14, 1)      # low warm horizon glow
    e2 = cr.elements.new(0.42); e2.color = (0.68, 0.40, 0.24, 1)
    cr.elements[2].position = 1.0
    cr.elements[2].color = (0.17, 0.26, 0.50, 1)     # cool upper gorge sky
    nt.links.new(mr.outputs["Result"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], e.inputs["Color"])
    return mat


def make_fire(name="mat_k_fire", lo=0.05, hi=0.34, s_lo=0.82, s_hi=0.30):
    """Flame body: emission graded root(dark orange) -> tip(pale yellow) in
    object Z, so the fire is not one flat orange blob.

    Kit lesson 21/22: stacked emissive cones ADD, and AgX desaturates its
    highlight shoulder hard -- ANY emission bright enough to clip comes back
    cream. A fire reads ORANGE only if it sits in the MIDTONES, so the flame
    surfaces stay modest and it is the darkness of the sooted firebox behind
    them that makes them the brightest thing in frame. The lighting is done by
    FIRE_mouth / FIRE_core, not by this surface.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (480, 0)
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-500, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-320, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-140, 0)
    mr.inputs["From Min"].default_value = lo
    mr.inputs["From Max"].default_value = hi
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = (60, 0)
    cr = r.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (1.0, 0.150, 0.018, 1)
    e2 = cr.elements.new(0.5); e2.color = (1.0, 0.330, 0.048, 1)
    cr.elements[2].position = 1.0
    cr.elements[2].color = (1.0, 0.560, 0.140, 1)
    nt.links.new(mr.outputs["Result"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], e.inputs["Color"])
    st = nt.nodes.new("ShaderNodeMapRange"); st.location = (240, -220)
    st.inputs["From Min"].default_value = 0.0
    st.inputs["From Max"].default_value = 1.0
    st.inputs["To Min"].default_value = s_lo
    st.inputs["To Max"].default_value = s_hi
    nt.links.new(mr.outputs["Result"], st.inputs["Value"])
    nt.links.new(st.outputs["Result"], e.inputs["Strength"])
    return mat


def make_steam(name="mat_k_steam", color=(0.88, 0.82, 0.74), alpha=0.058):
    """Steam WISP geometry -- the soft-edged shells that sit inside the little
    bounded steam volume over the pots.

    It is a Translucent+Transparent mix, never an emission: steam that emits
    reads as a ghost. The alpha is driven by a noise ramp so each shell is a
    ragged patch rather than a uniform grey balloon, and the ramp straddles the
    noise MEAN (kit rule) or the mask is all-on / all-off.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (700, 0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (480, -150)
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.location = (480, 60)
    tl.inputs["Color"].default_value = (*color, 1)
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tl.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-700, 0)
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-500, 0)
    n.inputs["Scale"].default_value = 5.5
    n.inputs["Detail"].default_value = 7.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = (-280, 0)
    # straddle the noise mean (~0.5) or the mask is all-on / all-off
    r.color_ramp.elements[0].position = 0.36
    r.color_ramp.elements[0].color = (0, 0, 0, 1)
    r.color_ramp.elements[1].position = 0.70
    r.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    # fade out towards the top of each wisp so it dissolves instead of ending
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-500, -260)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    fade = nt.nodes.new("ShaderNodeMapRange"); fade.location = (-280, -260)
    fade.inputs["From Min"].default_value = 0.55
    fade.inputs["From Max"].default_value = 0.02
    nt.links.new(sep.outputs["Z"], fade.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.location = (-60, -120)
    m1.operation = "MULTIPLY"
    nt.links.new(r.outputs["Color"], m1.inputs[0])
    nt.links.new(fade.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.location = (160, -120)
    m2.operation = "MULTIPLY"
    m2.inputs[1].default_value = alpha
    nt.links.new(m1.outputs["Value"], m2.inputs[0])
    nt.links.new(m2.outputs["Value"], mix.inputs["Fac"])
    return mat


# ------------------------------------------------------------------ build

def make_all():
    made = []

    # --- floor: five de-correlated variants dealt out plank by plank --------
    made.append(tex("mat_k_floor", scale=0.42, rough_lo=0.40, rough_hi=0.90,
                    darken=0.95, normal_strength=1.25,
                    tint=(0.40, 0.255, 0.135), tint_fac=0.24))
    made.append(tex("mat_k_floor_b", scale=0.40, rough_lo=0.40, rough_hi=0.95,
                    darken=0.80, normal_strength=1.25,
                    tint=(0.30, 0.215, 0.145), tint_fac=0.26,
                    offset=(3.7, 1.9, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_k_floor_c", scale=0.46, rough_lo=0.42, rough_hi=0.94,
                    darken=0.98, normal_strength=1.15,
                    tint=(0.38, 0.25, 0.145), tint_fac=0.20,
                    offset=(-2.3, 5.1, 0.0)))
    # a grease-darkened board: the lane between hearth and hatch that the cook
    # has walked ten thousand times
    made.append(tex("mat_k_floor_d", scale=0.50, rough_lo=0.30, rough_hi=0.80,
                    darken=0.64, normal_strength=1.30,
                    tint=(0.25, 0.130, 0.072), tint_fac=0.42,
                    offset=(6.1, 0.4, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_k_floor_e", scale=0.44, rough_lo=0.48, rough_hi=0.95,
                    darken=0.88, normal_strength=1.20,
                    tint=(0.36, 0.245, 0.150), tint_fac=0.30,
                    offset=(1.1, 2.6, 0.0)))
    # flagstones in front of the fire -- a plank floor at a cooking hearth is
    # a building that has already burned down
    made.append(tex("mat_k_flag", scale=0.52, rough_lo=0.48, rough_hi=0.94,
                    darken=0.50, tint=(0.185, 0.155, 0.130), tint_fac=0.56,
                    normal_strength=1.55))
    made.append(tex("mat_k_flag_b", scale=0.46, rough_lo=0.50, rough_hi=0.96,
                    darken=0.40, tint=(0.145, 0.122, 0.105), tint_fac=0.62,
                    normal_strength=1.55, offset=(3.3, 1.7, 0.5)))

    # --- wall cladding ------------------------------------------------------
    made.append(tex("mat_k_wall", scale=0.55, rough_lo=0.50, darken=0.86,
                    tint=(0.42, 0.285, 0.165), tint_fac=0.36,
                    normal_strength=1.3))
    made.append(tex("mat_k_wall_b", scale=0.52, rough_lo=0.52, darken=0.72,
                    tint=(0.38, 0.245, 0.145), tint_fac=0.46,
                    normal_strength=1.3,
                    offset=(1.7, 4.3, 2.1), rot=(0, 0, math.radians(90))))

    # --- structure ----------------------------------------------------------
    made.append(tex("mat_k_beam", scale=0.6, rough_lo=0.55, darken=0.66,
                    tint=(0.33, 0.21, 0.12), tint_fac=0.48, normal_strength=1.2))
    made.append(tex("mat_k_beam_b", scale=0.55, rough_lo=0.58, darken=0.56,
                    tint=(0.28, 0.175, 0.098), tint_fac=0.55,
                    normal_strength=1.2, offset=(2.4, 1.1, 3.3)))

    # --- horizontal work surfaces -------------------------------------------
    # Hatch top and prep bench are the two things the eye lands on after the
    # fire, so they get the worn-table texture, lighter and glossier than the
    # structure so they carry the highlight. The prep bench is SCRUBBED --
    # paler and cooler than anything else in the room, which is exactly what
    # makes the fish on it read.
    made.append(tex("mat_k_counter", scale=0.80, rough_lo=0.18, rough_hi=0.52,
                    darken=0.94, tint=(0.42, 0.275, 0.145), tint_fac=0.24,
                    normal_strength=0.70))
    made.append(tex("mat_k_prep", scale=0.76, rough_lo=0.30, rough_hi=0.72,
                    darken=1.18, tint=(0.52, 0.44, 0.335), tint_fac=0.40,
                    normal_strength=0.85, offset=(1.6, 2.2, 0.0)))
    made.append(tex("mat_k_table", scale=0.72, rough_lo=0.18, rough_hi=0.52,
                    darken=0.98, tint=(0.44, 0.30, 0.165), tint_fac=0.22,
                    normal_strength=0.65, offset=(2.9, 0.6, 0.0)))
    made.append(tex("mat_k_table_b", scale=0.86, rough_lo=0.24, rough_hi=0.60,
                    darken=0.82, tint=(0.38, 0.25, 0.14), tint_fac=0.30,
                    normal_strength=0.70,
                    offset=(0.5, 3.4, 1.2), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_k_shelf", scale=0.8, rough_lo=0.55, darken=0.88,
                    tint=(0.42, 0.28, 0.15), tint_fac=0.22))
    made.append(tex("mat_k_shelf_b", scale=0.75, rough_lo=0.58, darken=0.74,
                    offset=(4.1, 2.2, 1.3), rot=(0, 0, math.radians(90))))

    # --- painted palette accents -------------------------------------------
    made.append(tex("mat_k_green", scale=0.9, rough_lo=0.40, darken=1.00,
                    tint=(0.105, 0.255, 0.145), tint_fac=0.74))
    made.append(tex("mat_k_green_b", scale=0.85, rough_lo=0.44, darken=0.86,
                    tint=(0.082, 0.198, 0.115), tint_fac=0.82,
                    offset=(2.2, 1.4, 0.7)))
    made.append(tex("mat_k_green_c", scale=1.05, rough_lo=0.38, darken=1.08,
                    tint=(0.135, 0.300, 0.175), tint_fac=0.68,
                    offset=(5.3, 2.9, 1.8), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_k_oxblood", scale=0.75, rough_lo=0.38, darken=1.00,
                    tint=(0.345, 0.050, 0.042), tint_fac=0.85))
    made.append(tex("mat_k_oxblood_b", scale=0.68, rough_lo=0.42, darken=0.84,
                    tint=(0.255, 0.042, 0.036), tint_fac=0.88,
                    offset=(1.9, 0.7, 2.4)))
    made.append(tex("mat_k_blue", scale=0.82, rough_lo=0.42, darken=0.92,
                    tint=(0.095, 0.150, 0.235), tint_fac=0.80,
                    offset=(3.1, 1.8, 0.4)))

    # --- surfaces -----------------------------------------------------------
    made.append(tex("mat_k_crate", scale=1.35, rough_lo=0.58, darken=0.80,
                    tint=(0.32, 0.25, 0.17), tint_fac=0.35))
    made.append(tex("mat_k_crate_b", scale=1.5, rough_lo=0.60, darken=0.68,
                    offset=(0.9, 3.3, 1.1)))
    made.append(tex("mat_k_burlap", scale=2.2, rough_lo=0.75, darken=0.95,
                    tint=(0.42, 0.34, 0.21), tint_fac=0.35, normal_strength=1.4))
    made.append(tex("mat_k_sacking", scale=1.8, rough_lo=0.80, darken=0.70,
                    tint=(0.33, 0.28, 0.18), tint_fac=0.45, normal_strength=1.5,
                    offset=(2.6, 0.9, 1.4)))
    made.append(tex("mat_k_rust", scale=1.6, rough_lo=0.50, darken=0.78))
    made.append(tex("mat_k_plaster", scale=1.1, rough_lo=0.62, darken=0.92,
                    tint=(0.46, 0.40, 0.30), tint_fac=0.25))
    # hearth stone: warm-tinted so firelight has something to glow on
    made.append(tex("mat_k_stone", scale=0.62, rough_lo=0.58, rough_hi=0.98,
                    darken=0.80, tint=(0.36, 0.245, 0.155), tint_fac=0.50,
                    normal_strength=1.6))
    made.append(tex("mat_k_stone_b", scale=0.48, rough_lo=0.62, rough_hi=0.98,
                    darken=0.66, tint=(0.30, 0.200, 0.135), tint_fac=0.56,
                    normal_strength=1.6, offset=(2.7, 1.3, 0.9)))
    # FIRED BRICK for the oven -- redder and more saturated than the river
    # stone of the hearth, so the two masonry masses do not merge into one
    # undifferentiated lump in the back-left corner
    # v1 shipped this at darken 1.00 / tint_fac 0.66 and the range wall came
    # back salmon pink and BRIGHTER than the fire -- the value leader was the
    # masonry rather than the flame it contains. Brick lit by firelight is a
    # dull warm brown, not a terracotta swatch: two stops down and desaturated.
    made.append(tex("mat_k_brick", scale=0.90, rough_lo=0.62, rough_hi=0.97,
                    darken=0.62, tint=(0.300, 0.148, 0.092), tint_fac=0.56,
                    normal_strength=1.7))
    made.append(tex("mat_k_brick_b", scale=0.82, rough_lo=0.66, rough_hi=0.99,
                    darken=0.48, tint=(0.245, 0.115, 0.072), tint_fac=0.62,
                    normal_strength=1.7, offset=(1.5, 3.1, 0.7)))
    # sooted stone/brick for the chimney throat and the wall above the fire
    made.append(tex("mat_k_soot", scale=0.58, rough_lo=0.78, rough_hi=1.0,
                    darken=0.20, tint=(0.058, 0.050, 0.046), tint_fac=0.74,
                    normal_strength=1.4, offset=(4.2, 2.6, 1.1)))
    made.append(tex("mat_k_soot_b", scale=0.50, rough_lo=0.82, rough_hi=1.0,
                    darken=0.15, tint=(0.042, 0.036, 0.034), tint_fac=0.80,
                    normal_strength=1.4, offset=(0.7, 4.4, 2.2)))
    made.append(tex("mat_k_rug", scale=1.25, rough_lo=0.82, darken=0.98,
                    tint=(0.38, 0.155, 0.095), tint_fac=0.52,
                    normal_strength=1.6))
    made.append(tex("mat_k_linen", scale=1.9, rough_lo=0.80, darken=0.60,
                    tint=(0.40, 0.355, 0.270), tint_fac=0.40, normal_strength=1.3))
    # the cook's apron: the palest cloth in the room, deliberately
    made.append(tex("mat_k_apron", scale=1.7, rough_lo=0.82, darken=1.05,
                    tint=(0.55, 0.50, 0.42), tint_fac=0.35, normal_strength=1.3,
                    offset=(0.8, 1.9, 0.4)))

    made += [
        make_glass(),
        make_glass("mat_k_glass_brown", color=(0.42, 0.24, 0.09), rough=0.10),
        make_glass("mat_k_glass_green", color=(0.16, 0.36, 0.19), rough=0.08),
        make_broth(),
        make_broth("mat_k_broth_b", color=(0.235, 0.100, 0.028)),
        make_broth("mat_k_water", color=(0.055, 0.075, 0.070)),
        make_ceramic("mat_k_ceramic", (0.40, 0.33, 0.22)),
        make_ceramic("mat_k_ceramic_b", (0.30, 0.20, 0.12), rough=0.30),
        make_ceramic("mat_k_ceramic_ox", (0.26, 0.075, 0.055), rough=0.26),
        make_ceramic("mat_k_ceramic_gn", (0.115, 0.215, 0.135), rough=0.30),
        make_ceramic("mat_k_ceramic_bl", (0.085, 0.135, 0.205), rough=0.24),
        make_ceramic("mat_k_ceramic_cr", (0.50, 0.46, 0.36), rough=0.20),
        make_ceramic("mat_k_crock", (0.235, 0.185, 0.120), rough=0.28),
        make_copper(),
        make_copper("mat_k_copper_b", color=(0.55, 0.245, 0.105), rough=0.30,
                    verdigris=0.30),
        make_copper("mat_k_copper_c", color=(0.68, 0.36, 0.155), rough=0.16),
        make_copper("mat_k_tin", color=(0.46, 0.44, 0.42), rough=0.28),
        make_metal("mat_k_brass", (0.55, 0.38, 0.14), rough=0.28),
        make_metal("mat_k_pewter", (0.155, 0.160, 0.168), rough=0.42),
        make_metal("mat_k_steel", (0.42, 0.43, 0.45), rough=0.14),   # knives
        make_metal("mat_k_iron", (0.048, 0.042, 0.038), rough=0.55, metallic=0.9),
        make_metal("mat_k_iron_b", (0.075, 0.062, 0.052), rough=0.42, metallic=0.9),
        make_wax(),
        make_paper(),
        make_paper("mat_k_label", color=(0.60, 0.53, 0.38)),
        make_paper("mat_k_garlic", color=(0.66, 0.62, 0.52), rough=0.62,
                   bump=220.0),
        make_paper("mat_k_straw", color=(0.235, 0.185, 0.095)),
        make_paper("mat_k_bread", color=(0.44, 0.275, 0.115), rough=0.72,
                   bump=90.0),
        make_paper("mat_k_dough", color=(0.60, 0.53, 0.40), rough=0.68,
                   bump=70.0),
        make_canvas(color=(0.205, 0.180, 0.128)),
        make_canvas("mat_k_canvas_b", color=(0.150, 0.135, 0.098)),
        make_canvas("mat_k_sack", color=(0.105, 0.090, 0.058), bump=160.0),
        make_leather(),
        make_leather("mat_k_leather_b", color=(0.075, 0.048, 0.030)),
        make_fishflesh(),
        make_fishflesh("mat_k_fishflesh_b", color=(0.55, 0.40, 0.34)),
        make_fishskin(),
        make_fishskin("mat_k_fishskin_b", color=(0.155, 0.150, 0.135)),
        make_eel(),
        make_onion(),
        make_onion("mat_k_onion_b", color=(0.42, 0.235, 0.075)),
        make_onion("mat_k_carrot", color=(0.52, 0.185, 0.045)),
        make_herb(),
        make_herb("mat_k_herb_b", color=(0.150, 0.150, 0.088)),
        make_herb("mat_k_cabbage", color=(0.155, 0.205, 0.098)),
        make_slate(),
        make_chalk(),
        make_emissive_cam("mat_k_lampglass", (1.0, 0.60, 0.25), 9.5),
        make_emissive_cam("mat_k_candleflame", (1.0, 0.70, 0.30), 17.0),
        make_emissive("mat_k_ember", (1.0, 0.185, 0.026), 2.3),
        make_emissive("mat_k_ember_b", (1.0, 0.26, 0.048), 1.3),
        make_fire(),
        # oven mouth: shallower gradient, the loaves inside are lit not aflame
        make_fire("mat_k_fire_oven", lo=0.02, hi=0.22, s_lo=0.60, s_hi=0.26),
        make_steam(),
        make_steam("mat_k_steam_b", color=(0.82, 0.78, 0.73), alpha=0.042),
        make_dusk_pane(),
    ]
    for m in made:
        m.use_fake_user = True      # zero-user datablocks are dropped on save
    return {m.name: KM.verify(m) for m in made}
