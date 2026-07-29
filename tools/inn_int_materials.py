"""Material library for the Dellhollow INN common room (`del-inn-int`).

Deliberately SELF-CONTAINED. It reads the shared texture manifests and calls
`kit_materials.make_tex_mat`, but it does not import any other interior's
material module: the weapon/armor/item interiors are being built concurrently
by other agents, and importing a file somebody else is mid-edit is how a
six-hour headless build dies at 3am.

Palette (public/townmap/dellhollow.map.json -> style.palette):
    weathered PAINTED timber -- oxblood red, moss green, faded blue -- over a
    brown scaffold structure.

Inn-specific additions over the shop palette: hearth stone, slate (for the
lock-schedule board), pewter, wool/blanket, ale, and a soot material for the
chimney breast above the fire.

All names are prefixed `mat_n_` (n = inn) so the library can never collide with
a sibling interior's materials.
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
    "mat_n_floor":     "tex_int_floor",
    "mat_n_floor_b":   "tex_int_floor",
    "mat_n_floor_c":   "mat_int_floor",
    "mat_n_floor_d":   "mat_deck",
    "mat_n_floor_e":   "mat_int_plank",
    "mat_n_wall":      "tex_int_wall",
    "mat_n_wall_b":    "tex_int_wall",
    "mat_n_beam":      "tex_int_beam",
    "mat_n_beam_b":    "tex_int_beam",
    "mat_n_counter":   "mat_int_wood",
    "mat_n_table":     "mat_int_wood",
    "mat_n_table_b":   "mat_int_wood",
    "mat_n_shelf":     "tex_int_shelf",
    "mat_n_shelf_b":   "tex_int_shelf",
    "mat_n_green":     "mat_wallwood",
    "mat_n_green_b":   "mat_wallwood",
    "mat_n_green_c":   "mat_wallwood",
    "mat_n_oxblood":   "mat_wallwood_dark",
    "mat_n_oxblood_b": "mat_wallwood_dark",
    "mat_n_blue":      "mat_wallwood",
    "mat_n_crate":     "mat_timber",
    "mat_n_crate_b":   "tex_int_shelf",
    "mat_n_burlap":    "tex_burlap",
    "mat_n_rust":      "tex_rust",
    "mat_n_plaster":   "mat_int_plaster",
    "mat_n_stone":     "mat_int_hearth",
    "mat_n_stone_b":   "mat_int_stone",
    "mat_n_soot":      "mat_int_hearth",
    "mat_n_rug":       "mat_int_rug",
    "mat_n_linen":     "mat_int_linen",
    "mat_n_wool":      "mat_int_linen",
    "mat_n_wool_b":    "mat_int_linen",
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


def make_glass(name="mat_n_glass", color=(0.72, 0.82, 0.72), rough=0.06):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.48
    mat.use_backface_culling = False
    return mat


def make_ale(name="mat_n_ale", color=(0.52, 0.22, 0.045)):
    """Beer seen from above in a mug: amber, dense, a touch translucent."""
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.14
    b.inputs["Transmission Weight"].default_value = 0.55
    b.inputs["IOR"].default_value = 1.35
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


def make_wax(name="mat_n_wax", color=(0.62, 0.56, 0.40)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.82 for c in color), color, scale=30.0)
    b.inputs["Roughness"].default_value = 0.44
    b.inputs["Subsurface Weight"].default_value = 0.28
    b.inputs["Subsurface Radius"].default_value = (0.012, 0.009, 0.006)
    _noise_bump(nt, b, scale=120.0, strength=0.20)
    return mat


def make_paper(name="mat_n_paper", color=(0.52, 0.45, 0.33), rough=0.80,
               bump=140.0):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.72 for c in color),
            tuple(min(1, c * 1.18) for c in color), scale=26.0)
    b.inputs["Roughness"].default_value = rough
    _noise_bump(nt, b, scale=bump, strength=0.10)
    return mat


def make_canvas(name="mat_n_canvas", color=(0.34, 0.30, 0.22), bump=220.0,
                strength=0.35):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.7 for c in color),
            tuple(min(1, c * 1.25) for c in color), scale=40.0)
    b.inputs["Roughness"].default_value = 0.90
    _noise_bump(nt, b, scale=bump, strength=strength)
    return mat


def make_oilskin(name="mat_n_oilskin", color=(0.085, 0.075, 0.052)):
    """A waxed/oiled traveller's coat: dark, low-key, but with a waxy sheen so
    it catches a rim off the hearth instead of dying as a black blob."""
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.6 for c in color),
            tuple(min(1, c * 2.2) for c in color), scale=18.0)
    b.inputs["Roughness"].default_value = 0.34
    b.inputs["Coat Weight"].default_value = 0.55
    b.inputs["Coat Roughness"].default_value = 0.28
    _noise_bump(nt, b, scale=90.0, strength=0.30)
    return mat


def make_leather(name="mat_n_leather", color=(0.115, 0.065, 0.035)):
    mat, nt, b = _base(name)
    _mottle(nt, b, tuple(c * 0.65 for c in color),
            tuple(min(1, c * 1.5) for c in color), scale=24.0)
    b.inputs["Roughness"].default_value = 0.55
    _noise_bump(nt, b, scale=180.0, strength=0.28)
    return mat


def make_slate(name="mat_n_slate", color=(0.038, 0.040, 0.043)):
    """The chalk board. Very dark but NOT black -- a pure black rectangle in
    the middle of the back wall is exactly the 'black region larger than a
    fist' the brief forbids, so it keeps a dusty sheen and a chalk haze."""
    mat, nt, b = _base(name)
    _mottle(nt, b, color, (0.105, 0.108, 0.112), scale=16.0)
    b.inputs["Roughness"].default_value = 0.62
    _noise_bump(nt, b, scale=110.0, strength=0.16)
    return mat


def make_chalk(name="mat_n_chalk", color=(0.70, 0.70, 0.66)):
    mat, nt, b = _base(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.95
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


def make_dusk_pane(name="mat_n_dusk", strength=0.95):
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
    cr.elements[0].color = (1.0, 0.52, 0.24, 1)      # low warm horizon glow
    e2 = cr.elements.new(0.42); e2.color = (0.80, 0.47, 0.34, 1)
    cr.elements[2].position = 1.0
    cr.elements[2].color = (0.22, 0.31, 0.56, 1)     # cool upper gorge sky
    nt.links.new(mr.outputs["Result"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], e.inputs["Color"])
    return mat


def make_fire(name="mat_n_fire"):
    """Flame body: emission graded root(dark orange) -> tip(pale yellow) in
    object Z, so the fire is not one flat orange blob."""
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
    # Range must match where the flames ACTUALLY are. It was 0.12..0.62 while
    # the flame bodies sat at z 0.10..0.83, so almost every visible surface
    # landed on the pale end of the ramp and the whole fire came back cream.
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-140, 0)
    mr.inputs["From Min"].default_value = 0.05
    mr.inputs["From Max"].default_value = 0.34
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
    # Emission strength. v1 ran 26 at the root and AgX clipped the whole fire
    # to a white blob -- the flames stopped being orange and became a hole in
    # the picture. The fire's JOB is to be coloured; the lighting is done by
    # FIRE_mouth / FIRE_core, not by this surface.
    st = nt.nodes.new("ShaderNodeMapRange"); st.location = (240, -220)
    st.inputs["From Min"].default_value = 0.0
    st.inputs["From Max"].default_value = 1.0
    # AgX desaturates the highlight shoulder hard: ANY emission driven bright
    # enough to clip comes back cream, however saturated its colour. A fire
    # reads orange only if it sits in the MIDTONES -- so the flames are kept
    # modest and it is the darkness of the sooted firebox behind them, not
    # their absolute brightness, that makes them the brightest thing in frame.
    st.inputs["To Min"].default_value = 1.30
    st.inputs["To Max"].default_value = 0.50
    nt.links.new(mr.outputs["Result"], st.inputs["Value"])
    nt.links.new(st.outputs["Result"], e.inputs["Strength"])
    return mat


# ------------------------------------------------------------------ build

def make_all():
    made = []

    # --- floor: five de-correlated variants dealt out plank by plank --------
    made.append(tex("mat_n_floor", scale=0.42, rough_lo=0.40, rough_hi=0.90,
                    darken=0.95, normal_strength=1.25,
                    tint=(0.40, 0.255, 0.135), tint_fac=0.24))
    made.append(tex("mat_n_floor_b", scale=0.40, rough_lo=0.40, rough_hi=0.95,
                    darken=0.80, normal_strength=1.25,
                    tint=(0.30, 0.215, 0.145), tint_fac=0.26,
                    offset=(3.7, 1.9, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_n_floor_c", scale=0.46, rough_lo=0.42, rough_hi=0.94,
                    darken=0.98, normal_strength=1.15,
                    tint=(0.38, 0.25, 0.145), tint_fac=0.20,
                    offset=(-2.3, 5.1, 0.0)))
    made.append(tex("mat_n_floor_d", scale=0.50, rough_lo=0.46, rough_hi=0.95,
                    darken=0.70, normal_strength=1.30,
                    tint=(0.27, 0.135, 0.080), tint_fac=0.38,
                    offset=(6.1, 0.4, 0.0), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_n_floor_e", scale=0.44, rough_lo=0.48, rough_hi=0.95,
                    darken=0.88, normal_strength=1.20,
                    tint=(0.36, 0.245, 0.150), tint_fac=0.30,
                    offset=(1.1, 2.6, 0.0)))

    # --- wall cladding ------------------------------------------------------
    made.append(tex("mat_n_wall", scale=0.55, rough_lo=0.50, darken=0.86,
                    tint=(0.42, 0.285, 0.165), tint_fac=0.36,
                    normal_strength=1.3))
    made.append(tex("mat_n_wall_b", scale=0.52, rough_lo=0.52, darken=0.72,
                    tint=(0.38, 0.245, 0.145), tint_fac=0.46,
                    normal_strength=1.3,
                    offset=(1.7, 4.3, 2.1), rot=(0, 0, math.radians(90))))

    # --- structure ----------------------------------------------------------
    made.append(tex("mat_n_beam", scale=0.6, rough_lo=0.55, darken=0.66,
                    tint=(0.33, 0.21, 0.12), tint_fac=0.48, normal_strength=1.2))
    made.append(tex("mat_n_beam_b", scale=0.55, rough_lo=0.58, darken=0.56,
                    tint=(0.28, 0.175, 0.098), tint_fac=0.55,
                    normal_strength=1.2, offset=(2.4, 1.1, 3.3)))

    # --- horizontal work surfaces -------------------------------------------
    # The counter and the long table are the two things the eye lands on, so
    # they get the dedicated worn-table texture, lighter and glossier than the
    # structure so they carry the highlight.
    made.append(tex("mat_n_counter", scale=0.80, rough_lo=0.20, rough_hi=0.55,
                    darken=0.90, tint=(0.40, 0.26, 0.14), tint_fac=0.26,
                    normal_strength=0.70))
    made.append(tex("mat_n_table", scale=0.72, rough_lo=0.18, rough_hi=0.52,
                    darken=0.98, tint=(0.44, 0.30, 0.165), tint_fac=0.22,
                    normal_strength=0.65, offset=(2.9, 0.6, 0.0)))
    made.append(tex("mat_n_table_b", scale=0.86, rough_lo=0.24, rough_hi=0.60,
                    darken=0.82, tint=(0.38, 0.25, 0.14), tint_fac=0.30,
                    normal_strength=0.70,
                    offset=(0.5, 3.4, 1.2), rot=(0, 0, math.radians(90))))
    made.append(tex("mat_n_shelf", scale=0.8, rough_lo=0.55, darken=0.88,
                    tint=(0.42, 0.28, 0.15), tint_fac=0.22))
    made.append(tex("mat_n_shelf_b", scale=0.75, rough_lo=0.58, darken=0.74,
                    offset=(4.1, 2.2, 1.3), rot=(0, 0, math.radians(90))))

    # --- painted palette accents -------------------------------------------
    # moss green: the wainscot and joinery that ties the whole room together
    made.append(tex("mat_n_green", scale=0.9, rough_lo=0.40, darken=1.00,
                    tint=(0.105, 0.255, 0.145), tint_fac=0.74))
    made.append(tex("mat_n_green_b", scale=0.85, rough_lo=0.44, darken=0.86,
                    tint=(0.082, 0.198, 0.115), tint_fac=0.82,
                    offset=(2.2, 1.4, 0.7)))
    made.append(tex("mat_n_green_c", scale=1.05, rough_lo=0.38, darken=1.08,
                    tint=(0.135, 0.300, 0.175), tint_fac=0.68,
                    offset=(5.3, 2.9, 1.8), rot=(0, 0, math.radians(90))))
    # oxblood: the map's shop-front / trim accent
    made.append(tex("mat_n_oxblood", scale=0.75, rough_lo=0.38, darken=1.00,
                    tint=(0.345, 0.050, 0.042), tint_fac=0.85))
    made.append(tex("mat_n_oxblood_b", scale=0.68, rough_lo=0.42, darken=0.84,
                    tint=(0.255, 0.042, 0.036), tint_fac=0.88,
                    offset=(1.9, 0.7, 2.4)))
    # faded blue: the third painted accent in the town palette, used sparingly
    # on furniture so the room is not a two-colour poster
    made.append(tex("mat_n_blue", scale=0.82, rough_lo=0.42, darken=0.92,
                    tint=(0.095, 0.150, 0.235), tint_fac=0.80,
                    offset=(3.1, 1.8, 0.4)))

    # --- surfaces -----------------------------------------------------------
    made.append(tex("mat_n_crate", scale=1.35, rough_lo=0.58, darken=0.80,
                    tint=(0.32, 0.25, 0.17), tint_fac=0.35))
    made.append(tex("mat_n_crate_b", scale=1.5, rough_lo=0.60, darken=0.68,
                    offset=(0.9, 3.3, 1.1)))
    made.append(tex("mat_n_burlap", scale=2.2, rough_lo=0.75, darken=0.95,
                    tint=(0.42, 0.34, 0.21), tint_fac=0.35, normal_strength=1.4))
    made.append(tex("mat_n_rust", scale=1.6, rough_lo=0.50, darken=0.78))
    made.append(tex("mat_n_plaster", scale=1.1, rough_lo=0.62, darken=0.92,
                    tint=(0.46, 0.40, 0.30), tint_fac=0.25))
    # hearth stone: warm-tinted so firelight has something to glow on
    made.append(tex("mat_n_stone", scale=0.62, rough_lo=0.55, rough_hi=0.98,
                    darken=1.02, tint=(0.46, 0.305, 0.185), tint_fac=0.46,
                    normal_strength=1.5))
    made.append(tex("mat_n_stone_b", scale=0.48, rough_lo=0.58, rough_hi=0.98,
                    darken=0.88, tint=(0.40, 0.265, 0.170), tint_fac=0.50,
                    normal_strength=1.5, offset=(2.7, 1.3, 0.9)))
    # sooted stone for the chimney throat and the wall above the fire
    made.append(tex("mat_n_soot", scale=0.58, rough_lo=0.72, rough_hi=1.0,
                    darken=0.34, tint=(0.10, 0.085, 0.078), tint_fac=0.62,
                    normal_strength=1.4, offset=(4.2, 2.6, 1.1)))
    made.append(tex("mat_n_rug", scale=1.25, rough_lo=0.82, darken=0.98,
                    tint=(0.38, 0.155, 0.095), tint_fac=0.52,
                    normal_strength=1.6))
    made.append(tex("mat_n_linen", scale=1.9, rough_lo=0.80, darken=0.60,
                    tint=(0.40, 0.355, 0.270), tint_fac=0.40, normal_strength=1.3))
    made.append(tex("mat_n_wool", scale=1.5, rough_lo=0.86, darken=0.50,
                    tint=(0.255, 0.095, 0.070), tint_fac=0.74, normal_strength=1.6))
    made.append(tex("mat_n_wool_b", scale=1.7, rough_lo=0.88, darken=0.30,
                    tint=(0.062, 0.092, 0.130), tint_fac=0.80, normal_strength=1.6,
                    offset=(1.4, 2.8, 0.6)))

    made += [
        make_glass(),
        make_glass("mat_n_glass_brown", color=(0.42, 0.24, 0.09), rough=0.10),
        make_glass("mat_n_glass_green", color=(0.16, 0.36, 0.19), rough=0.08),
        make_ale(),
        make_ale("mat_n_ale_dark", color=(0.22, 0.085, 0.030)),
        make_ceramic("mat_n_ceramic", (0.40, 0.33, 0.22)),
        make_ceramic("mat_n_ceramic_b", (0.30, 0.20, 0.12), rough=0.30),
        make_ceramic("mat_n_ceramic_ox", (0.26, 0.075, 0.055), rough=0.26),
        make_ceramic("mat_n_ceramic_gn", (0.115, 0.215, 0.135), rough=0.30),
        make_ceramic("mat_n_ceramic_bl", (0.085, 0.135, 0.205), rough=0.24),
        make_ceramic("mat_n_ceramic_cr", (0.48, 0.44, 0.34), rough=0.20),
        make_metal("mat_n_brass", (0.55, 0.38, 0.14), rough=0.28),
        make_metal("mat_n_copper", (0.52, 0.26, 0.14), rough=0.36),
        make_metal("mat_n_pewter", (0.155, 0.160, 0.168), rough=0.42),
        make_metal("mat_n_iron", (0.048, 0.042, 0.038), rough=0.55, metallic=0.9),
        make_wax(),
        make_paper(),
        make_paper("mat_n_label", color=(0.60, 0.53, 0.38)),
        make_paper("mat_n_notice", color=(0.58, 0.52, 0.40), rough=0.86),
        make_paper("mat_n_card", color=(0.66, 0.60, 0.47), rough=0.55, bump=260.0),
        make_paper("mat_n_straw", color=(0.235, 0.185, 0.095)),
        make_canvas(color=(0.205, 0.180, 0.128)),
        make_canvas("mat_n_canvas_b", color=(0.150, 0.135, 0.098)),
        make_canvas("mat_n_sack", color=(0.215, 0.185, 0.118), bump=160.0),
        make_oilskin(),
        make_oilskin("mat_n_oilskin_b", color=(0.062, 0.070, 0.062)),
        make_leather(),
        make_leather("mat_n_leather_b", color=(0.075, 0.048, 0.030)),
        make_slate(),
        make_chalk(),
        make_emissive_cam("mat_n_lampglass", (1.0, 0.60, 0.25), 9.5),
        make_emissive_cam("mat_n_candleflame", (1.0, 0.70, 0.30), 17.0),
        make_emissive("mat_n_ember", (1.0, 0.20, 0.030), 4.2),
        make_fire(),
        make_dusk_pane(),
    ]
    for m in made:
        m.use_fake_user = True      # zero-user datablocks are dropped on save
    return {m.name: KM.verify(m) for m in made}
