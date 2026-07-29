"""Interior material library for the Dellhollow shop/room interiors.

Two differences from the outdoor kit library (tools/kit_materials.py):

  1. **No moss.** The kit's moss layer is driven by the world-up normal, so it
     only stains upward faces -- which is right outdoors and wrong inside a
     shop. Interior materials pass moss=0 and get their wear from the source
     texture plus per-variant darkening.
  2. **De-correlated variants.** The kit projects textures in OBJECT space, so
     a floor built as one object shows the same 1k tile repeating. Interior
     surfaces that are large (floor, wall cladding) get 3 material variants of
     the same source texture with different mapping offset/rotation/darken,
     dealt out plank by plank. That, plus real plank geometry, is what kills
     the tiling artifact.

The texture maps come from two manifests: the shared kit one and the
interior-only one written by tools/int_textures.py.
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
    m = dict(json.load(open(os.path.join(TEXDIR, "_manifest.json"))))
    p = os.path.join(TEXDIR, "_manifest_itemint.json")
    if os.path.exists(p):
        m.update(json.load(open(p)))
    return m


# material name -> source manifest key. Several materials share one texture;
# make_tex_mat names the material after its manifest key, so alias the entry
# under every material name that wants it.
SRC = {
    "mat_i_floor":    "tex_int_floor",
    "mat_i_floor_b":  "tex_int_floor",
    "mat_i_floor_c":  "tex_int_floor",
    "mat_i_floor_d":  "tex_int_floor",
    "mat_i_floor_e":  "mat_deck",
    "mat_i_wall":     "tex_int_wall",
    "mat_i_wall_b":   "tex_int_wall",
    "mat_i_beam":     "tex_int_beam",
    "mat_i_counter":  "tex_int_beam",
    "mat_i_shelf":    "tex_int_shelf",
    "mat_i_shelf_b":  "tex_int_shelf",
    "mat_i_green":    "mat_wallwood",
    "mat_i_green_b":  "mat_wallwood",
    "mat_i_oxblood":  "mat_wallwood_dark",
    "mat_i_crate":    "mat_timber",
    "mat_i_crate_b":  "tex_int_shelf",
    "mat_i_burlap":   "tex_burlap",
    "mat_i_rust":     "tex_rust",
    "mat_i_plaster":  "mat_plaster",
    # per-shop trim variants: the shell is identical between shops, the
    # painted joinery is not. weapon = deeper oxblood, armour = steel-blue.
    "mat_i_oxblood_d": "mat_wallwood_dark",
    "mat_i_steelblue": "mat_wallwood",
    "mat_i_steelblue_b": "mat_wallwood",
    "mat_i_green_c":  "mat_wallwood",
}


def _map_node(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "MAPPING")


def tex(name, offset=(0, 0, 0), rot=(0, 0, 0), **kw):
    """make_tex_mat against the merged manifest, then de-correlate the tile."""
    KM.MANIFEST = _merged_manifest()
    KM.MANIFEST[name] = KM.MANIFEST[SRC[name]]
    kw.setdefault("moss", 0.0)
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


def make_glass(name="mat_i_glass", color=(0.72, 0.82, 0.72), rough=0.06):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.48
    mat.use_backface_culling = False
    return mat


def make_oil(name="mat_i_oil", color=(0.68, 0.30, 0.055)):
    """Lamp oil seen through a jar: amber, dense, slightly translucent."""
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.12
    b.inputs["Transmission Weight"].default_value = 0.72
    b.inputs["IOR"].default_value = 1.45
    return mat


def make_ceramic(name, color, rough=0.22, mottle=0.9):
    mat, nt, b = _base(name)
    c2 = tuple(min(1.0, c * (1.0 + 0.35 * mottle)) for c in color)
    c1 = tuple(c * (1.0 - 0.30 * mottle) for c in color)
    _mottle(nt, b, c1, c2, scale=14.0)
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=55.0, strength=0.10)
    return mat


def make_brass(name="mat_i_brass", color=(0.55, 0.38, 0.14), rough=0.30):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.55 for c in color), color, scale=22.0)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=90.0, strength=0.12)
    return mat


def make_iron(name="mat_i_iron", color=(0.055, 0.048, 0.042), rough=0.55):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.6 for c in color), tuple(c * 1.9 for c in color),
            scale=26.0)
    b.inputs["Metallic"].default_value = 0.9
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=70.0, strength=0.18)
    return mat


def make_wax(name="mat_i_wax", color=(0.62, 0.56, 0.40)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.82 for c in color), color, scale=30.0)
    b.inputs["Roughness"].default_value = 0.44
    b.inputs["Subsurface Weight"].default_value = 0.28
    b.inputs["Subsurface Radius"].default_value = (0.012, 0.009, 0.006)
    _noise_bump(nt, b, scale=120.0, strength=0.20)
    return mat


def make_paper(name="mat_i_paper", color=(0.52, 0.45, 0.33)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.72 for c in color),
            tuple(min(1, c * 1.18) for c in color), scale=26.0)
    b.inputs["Roughness"].default_value = 0.80
    _noise_bump(nt, b, scale=140.0, strength=0.10)
    return mat


def make_canvas(name="mat_i_canvas", color=(0.34, 0.30, 0.22)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.7 for c in color),
            tuple(min(1, c * 1.25) for c in color), scale=40.0)
    b.inputs["Roughness"].default_value = 0.90
    _noise_bump(nt, b, scale=220.0, strength=0.35)
    return mat


def make_fish(name="mat_i_fish", color=(0.20, 0.145, 0.085)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.6 for c in color),
            tuple(min(1, c * 1.7) for c in color), scale=45.0)
    b.inputs["Roughness"].default_value = 0.52
    _noise_bump(nt, b, scale=150.0, strength=0.30)
    return mat


def make_apple(name="mat_i_apple", color=(0.36, 0.075, 0.035)):
    mat, nt, b = _base(name)
    _mottle(nt, b, color, (0.42, 0.30, 0.05), scale=34.0)
    b.inputs["Roughness"].default_value = 0.28
    b.inputs["Coat Weight"].default_value = 0.4
    return mat


def make_leather(name="mat_i_leather", color=(0.115, 0.065, 0.035)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.65 for c in color),
            tuple(min(1, c * 1.5) for c in color), scale=24.0)
    b.inputs["Roughness"].default_value = 0.55
    _noise_bump(nt, b, scale=180.0, strength=0.28)
    return mat


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


def make_dusk_pane(name="mat_i_dusk", strength=1.7):
    """Window glass that reads as the dusk sky outside: warm at the bottom of
    the pane, cool blue at the top.

    CAMERA RAYS ONLY. A plain emission surface is opaque to everything else,
    so with the dusk lamp sitting outside the wall the pane was blocking the
    entire window light -- the room got its "dusk" from the pane's own weak
    emission and nothing came through the opening. Mixing to a Transparent
    BSDF for non-camera rays lets the lamp light the room and lets the sash
    and mullions cast their shadow across the floor, which is the whole point
    of putting a window in the wall.
    """
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
    cr.elements[0].color = (1.0, 0.55, 0.26, 1)      # low warm horizon glow
    e2 = cr.elements.new(0.45); e2.color = (0.82, 0.50, 0.36, 1)
    cr.elements[2].position = 1.0
    cr.elements[2].color = (0.26, 0.34, 0.58, 1)     # cool upper sky
    nt.links.new(mr.outputs["Result"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], e.inputs["Color"])
    return mat


def _set(b, name, v):
    """Principled socket names drifted across Blender versions -- never let a
    missing socket take the whole material build down."""
    if name in b.inputs:
        b.inputs[name].default_value = v
        return True
    return False


def _rim(nt, b, src, color=(1.0, 0.78, 0.52), fac=0.55, blend=0.30):
    """Brighten the base colour at grazing angles.

    This is the single most important node in the armour shop. Dark metal in a
    dark room is invisible: a matte-ish steel facing the camera reflects the
    ceiling, which is black, so an unlit breastplate renders as a hole. The
    physical fix is a light behind every piece; the cheap fix that works from
    one fixed camera is to make the SILHOUETTE brighter than the interior of
    the form, so every metal object is outlined by its own edges wherever a
    practical can reach it. LayerWeight's Facing output is 1 exactly on those
    edges.
    """
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.location = (-360, 520)
    lw.inputs["Blend"].default_value = blend
    mul = nt.nodes.new("ShaderNodeMath"); mul.location = (-190, 520)
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = fac
    nt.links.new(lw.outputs["Facing"], mul.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.location = (-20, 420)
    mix.data_type = "RGBA"
    mix.blend_type = "MIX"
    nt.links.new(mul.outputs[0], mix.inputs["Factor"])
    nt.links.new(src, mix.inputs[6])                 # A
    mix.inputs[7].default_value = (*color, 1)        # B
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return mix


def make_metal(name="mat_i_steel", color=(0.62, 0.615, 0.605), rough=0.33,
               aniso=0.70, rim=(1.0, 0.80, 0.56), rim_fac=0.55, rim_blend=0.30,
               mottle=0.35, bump=0.06, bump_scale=140.0):
    """Ground steel: ANISOTROPIC, because a blade or a helm is polished along
    one direction and its highlight is a streak rather than a dot. A streak
    survives a small light source; a dot is a single pixel the denoiser eats.

    Combined with the _rim edge term above, this is what makes dark metal read
    in a dark room without lighting the room flat.
    """
    mat, nt, b = _base(name)
    c1 = tuple(c * (1.0 - 0.55 * mottle) for c in color)
    c2 = tuple(min(1.0, c * (1.0 + 0.30 * mottle)) for c in color)
    ramp = _mottle(nt, b, c1, c2, scale=22.0, detail=4.0)
    _rim(nt, b, ramp.outputs["Color"], color=rim, fac=rim_fac, blend=rim_blend)
    _set(b, "Metallic", 1.0)
    _set(b, "Roughness", rough)
    if _set(b, "Anisotropic", aniso):
        _set(b, "Anisotropic Rotation", 0.0)
        tan = nt.nodes.new("ShaderNodeTangent"); tan.location = (-360, -640)
        tan.direction_type = "RADIAL"
        tan.axis = "Z"
        if "Tangent" in b.inputs:
            nt.links.new(tan.outputs["Tangent"], b.inputs["Tangent"])
    if bump:
        _noise_bump(nt, b, scale=bump_scale, strength=bump)
    return mat


def make_mail(name="mat_i_mail", color=(0.150, 0.158, 0.172)):
    """Riveted mail: darker and rougher than plate, but with a dense high
    frequency bump so the surface breaks the light into hundreds of small
    specks. Without the bump a mail shirt is a grey bag."""
    mat, nt, b = _base(name)
    ramp = _mottle(nt, b, tuple(c * 0.5 for c in color),
                   tuple(min(1, c * 1.45) for c in color), scale=30.0)
    _rim(nt, b, ramp.outputs["Color"], color=(0.90, 0.74, 0.55), fac=0.38,
         blend=0.26)
    _set(b, "Metallic", 0.95)
    _set(b, "Roughness", 0.52)
    _set(b, "Anisotropic", 0.25)
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-820, -520)
    v = nt.nodes.new("ShaderNodeTexVoronoi"); v.location = (-600, -520)
    v.inputs["Scale"].default_value = 420.0
    v.feature = "DISTANCE_TO_EDGE"
    nt.links.new(tc.outputs["Object"], v.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-380, -520)
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.006
    nt.links.new(v.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def make_stone(name="mat_i_stone", color=(0.175, 0.170, 0.160), rough=0.78):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.62 for c in color),
            tuple(min(1, c * 1.55) for c in color), scale=11.0, detail=8.0)
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=34.0, strength=0.45, detail=8.0)
    return mat


def make_water_dark(name="mat_i_water_d", color=(0.035, 0.050, 0.052)):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.06
    _set(b, "Specular IOR Level", 0.9)
    return mat


# ------------------------------------------------------------------ build

def make_all():
    made = []
    # --- floor: three de-correlated variants of one worn plank texture -----
    made.append(tex("mat_i_floor", scale=0.42, rough_lo=0.42, rough_hi=0.92,
                    darken=0.95, normal_strength=1.25,
                    tint=(0.40, 0.255, 0.135), tint_fac=0.24))
    made.append(tex("mat_i_floor_b", scale=0.40, rough_lo=0.40, rough_hi=0.95,
                    darken=0.82, normal_strength=1.25,
                    tint=(0.30, 0.22, 0.15), tint_fac=0.25,
                    offset=(3.7, 1.9, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_i_floor_c", scale=0.45, rough_lo=0.45, rough_hi=0.95,
                    darken=1.00, normal_strength=1.15,
                    offset=(-2.3, 5.1, 0.0)))
    made.append(tex("mat_i_floor_d", scale=0.38, rough_lo=0.45, rough_hi=0.95,
                    darken=0.66, normal_strength=1.30,
                    tint=(0.26, 0.12, 0.075), tint_fac=0.40,
                    offset=(6.1, 0.4, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_i_floor_e", scale=0.50, rough_lo=0.50, rough_hi=0.95,
                    darken=0.92, normal_strength=1.20,
                    tint=(0.35, 0.32, 0.26), tint_fac=0.35, offset=(1.1, 2.6, 0.0)))
    # --- wall cladding ----------------------------------------------------
    made.append(tex("mat_i_wall", scale=0.55, rough_lo=0.50, darken=0.84,
                    tint=(0.42, 0.285, 0.165), tint_fac=0.36, normal_strength=1.3))
    made.append(tex("mat_i_wall_b", scale=0.52, rough_lo=0.52, darken=0.70,
                    tint=(0.38, 0.245, 0.145), tint_fac=0.46, normal_strength=1.3,
                    offset=(1.7, 4.3, 2.1), rot=(0, 0, math.radians(90))))
    # --- structure --------------------------------------------------------
    made.append(tex("mat_i_beam", scale=0.6, rough_lo=0.55, darken=0.62,
                    tint=(0.32, 0.205, 0.115), tint_fac=0.50, normal_strength=1.2))
    made.append(tex("mat_i_counter", scale=0.85, rough_lo=0.22, rough_hi=0.60,
                    darken=0.82, tint=(0.36, 0.24, 0.13), tint_fac=0.30,
                    normal_strength=0.75, offset=(2.9, 0.6, 0.0)))
    made.append(tex("mat_i_shelf", scale=0.8, rough_lo=0.55, darken=0.88,
                    tint=(0.42, 0.28, 0.15), tint_fac=0.22))
    made.append(tex("mat_i_shelf_b", scale=0.75, rough_lo=0.58, darken=0.74,
                    offset=(4.1, 2.2, 1.3), rot=(0, 0, math.radians(90))))
    # --- palette accents --------------------------------------------------
    # moss-green painted trim: the town's shed green, pushed greener/darker
    made.append(tex("mat_i_green", scale=0.9, rough_lo=0.42, darken=1.00,
                    tint=(0.115, 0.275, 0.155), tint_fac=0.72))
    made.append(tex("mat_i_green_b", scale=0.85, rough_lo=0.45, darken=0.88,
                    tint=(0.090, 0.215, 0.125), tint_fac=0.80,
                    offset=(2.2, 1.4, 0.7)))
    # oxblood: the map's accent colour
    made.append(tex("mat_i_oxblood", scale=0.75, rough_lo=0.40, darken=1.00,
                    tint=(0.345, 0.050, 0.042), tint_fac=0.85))
    # --- per-shop trim hues, all inside the town palette ------------------
    # weapon shop: the same oxblood pushed darker and browner, so a room full
    # of grey steel does not sit on a bright red ground
    made.append(tex("mat_i_oxblood_d", scale=0.72, rough_lo=0.42, darken=0.74,
                    tint=(0.215, 0.030, 0.028), tint_fac=0.90,
                    offset=(1.3, 2.7, 0.4)))
    # armour shop: the map's "faded blue" read as a cold steel-grey trim, so
    # the polished pieces have a cool ground to be warm highlights against
    made.append(tex("mat_i_steelblue", scale=0.9, rough_lo=0.45, darken=0.92,
                    tint=(0.125, 0.170, 0.215), tint_fac=0.82))
    made.append(tex("mat_i_steelblue_b", scale=0.85, rough_lo=0.48, darken=0.78,
                    tint=(0.090, 0.128, 0.170), tint_fac=0.86,
                    offset=(3.1, 0.8, 1.9)))
    made.append(tex("mat_i_green_c", scale=0.88, rough_lo=0.44, darken=0.94,
                    tint=(0.098, 0.215, 0.190), tint_fac=0.74,
                    offset=(0.7, 2.9, 1.5)))
    # --- goods ------------------------------------------------------------
    made.append(tex("mat_i_crate", scale=1.35, rough_lo=0.58, darken=0.80,
                    tint=(0.32, 0.25, 0.17), tint_fac=0.35))
    made.append(tex("mat_i_crate_b", scale=1.5, rough_lo=0.60, darken=0.68,
                    offset=(0.9, 3.3, 1.1)))
    made.append(tex("mat_i_burlap", scale=2.2, rough_lo=0.75, darken=0.95,
                    tint=(0.42, 0.34, 0.21), tint_fac=0.35, normal_strength=1.4))
    made.append(tex("mat_i_rust", scale=1.6, rough_lo=0.50, darken=0.78))
    made.append(tex("mat_i_plaster", scale=1.1, rough_lo=0.62, darken=0.92))

    made += [
        make_glass(),
        make_glass("mat_i_glass_brown", color=(0.42, 0.24, 0.09), rough=0.10),
        make_glass("mat_i_glass_green", color=(0.16, 0.36, 0.19), rough=0.08),
        make_oil(),
        make_ceramic("mat_i_ceramic", (0.40, 0.33, 0.22)),
        make_ceramic("mat_i_ceramic_b", (0.30, 0.20, 0.12), rough=0.30),
        make_ceramic("mat_i_ceramic_ox", (0.26, 0.075, 0.055), rough=0.26),
        make_ceramic("mat_i_ceramic_gn", (0.115, 0.215, 0.135), rough=0.30),
        make_ceramic("mat_i_ceramic_bl", (0.085, 0.135, 0.205), rough=0.24),
        make_brass(),
        make_brass("mat_i_copper", color=(0.52, 0.26, 0.14), rough=0.38),
        make_brass("mat_i_bronze", color=(0.44, 0.30, 0.135), rough=0.34),
        make_iron(),
        # --- the armoury metals ------------------------------------------
        make_metal(),
        make_metal("mat_i_steel_b", color=(0.255, 0.258, 0.262), rough=0.44,
                   aniso=0.55, rim=(0.94, 0.76, 0.54), rim_fac=0.66,
                   rim_blend=0.28),
        # A polished blade seen from a high camera mirrors the COOL overhead
        # wash and comes out blue-grey. Keeping the roughness up broadens the
        # highlight enough that the warm lanterns underneath get into it too,
        # which is what makes steel read as steel rather than as tin.
        make_metal("mat_i_steel_bright", color=(0.755, 0.750, 0.735), rough=0.25,
                   aniso=0.80, rim=(1.0, 0.86, 0.62), rim_fac=0.52),
        make_mail(),
        make_stone(),
        make_stone("mat_i_coal", color=(0.030, 0.026, 0.024), rough=0.62),
        # Sooted firebrick for the forge's hearthstone and fire bowl. Kit
        # finding 28, again: shipped in ordinary hearth stone the slab was
        # BRIGHTER than the coals it holds -- measured 93% of it clipped to
        # white -- because a mid-grey albedo half a metre from a practical has
        # nowhere to go but the AgX shoulder. The masonry that touches a fire
        # has to be dark enough that the fire can out-value it.
        make_stone("mat_i_forgestone", color=(0.078, 0.064, 0.056), rough=0.74),
        make_water_dark(),
        make_wax(),
        make_paper(),
        make_paper("mat_i_label", color=(0.60, 0.53, 0.38)),
        make_paper("mat_i_straw", color=(0.235, 0.185, 0.095)),
        make_canvas(),
        make_canvas("mat_i_net", color=(0.20, 0.175, 0.115)),
        make_canvas("mat_i_net_d", color=(0.105, 0.092, 0.062)),
        make_fish(),
        make_apple(),
        make_apple("mat_i_apple_g", color=(0.26, 0.24, 0.055)),
        make_leather(),
        make_leather("mat_i_leather_b", color=(0.058, 0.036, 0.024)),
        make_leather("mat_i_leather_r", color=(0.155, 0.058, 0.038)),
        make_paper("mat_i_feather", color=(0.44, 0.40, 0.31)),
        # Forge coals (weapon skin only). v3 ran 9.0 and the bed came back as a
        # pale band: the camera clears the counter's back edge by a few
        # centimetres, so the coals are seen nearly edge-on and every one of
        # them was deep in the AgX shoulder, where saturated orange returns
        # cream. Driven DOWN into the midtones and saturated, the same coals
        # read as coals -- and there are more of them, which is where the extra
        # glow comes from.
        make_emissive("mat_i_ember", (1.0, 0.24, 0.045), 4.2),
        make_emissive("mat_i_lampglass", (1.0, 0.60, 0.25), 16.0),
        make_emissive("mat_i_flame", (1.0, 0.72, 0.34), 55.0),
        make_dusk_pane(),
    ]
    for m in made:
        m.use_fake_user = True          # zero-user datablocks are dropped on save
    return {m.name: KM.verify(m) for m in made}
