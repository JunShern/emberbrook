"""Build the Dellhollow kit material library from downloaded PolyHaven textures.

Every material is a real textured Principled setup: Diffuse(xAO) -> Base Color,
Rough -> Roughness, nor_gl -> Normal Map. Outdoor materials get a procedural
moss/grime layer driven by world-up normal + noise, which is what sells the
weathered FF9 look (moss collects on upward faces).
"""
import bpy, os, json

TEXDIR = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else "", "")
TEXDIR = "/Users/junshernchan/projects/multiplayer-rpg/tools/textures"
MANIFEST = json.load(open(os.path.join(TEXDIR, "_manifest.json")))


def sock(node, name, stype=None):
    """ShaderNodeMix exposes several same-named sockets (one per data type),
    so match on socket type as well as name."""
    m = [s for s in node.inputs if s.name == name]
    if stype:
        t = [s for s in m if s.type == stype]
        if t:
            return t[0]
    return m[0] if m else None


def _img(nt, path, noncolor, loc, mapping):
    n = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(path, check_existing=True)
    n.image = img
    if noncolor:
        img.colorspace_settings.name = "Non-Color"
    n.location = loc
    n.interpolation = "Smart"
    # Box (triplanar) projection in object space: every kit piece gets correct
    # real-world texel density with no UV unwrapping, and planks/beams keep
    # their grain when rotated because the coords rotate with the object.
    n.projection = "BOX"
    n.projection_blend = 0.35
    n.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
    return n


def make_tex_mat(name, scale=1.0, moss=0.0, moss_color=(0.09, 0.16, 0.05),
                 rough_lo=0.35, rough_hi=1.0, normal_strength=1.0,
                 tint=None, tint_fac=0.0, darken=1.0):
    """moss: 0 = none, 1 = heavy. Adds upward-facing green/grime breakup."""
    entry = MANIFEST[name]
    maps = entry["maps"]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1400, 0)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-1200, 0)
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    diff = _img(nt, maps["Diffuse"], False, (-900, 300), mp)
    color_out = diff.outputs["Color"]

    if "AO" in maps:
        ao = _img(nt, maps["AO"], True, (-900, 20), mp)
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"; mix.location = (-560, 300)
        sock(mix, "Factor", "VALUE").default_value = 0.55
        nt.links.new(color_out, sock(mix, "A", "RGBA"))
        nt.links.new(ao.outputs["Color"], sock(mix, "B", "RGBA"))
        color_out = mix.outputs["Result"]

    if tint is not None and tint_fac > 0:
        tn = nt.nodes.new("ShaderNodeMix"); tn.data_type = "RGBA"
        tn.blend_type = "COLOR"; tn.location = (-380, 380)
        sock(tn, "Factor", "VALUE").default_value = tint_fac
        nt.links.new(color_out, sock(tn, "A", "RGBA"))
        sock(tn, "B", "RGBA").default_value = (*tint, 1.0)
        color_out = tn.outputs["Result"]

    # roughness
    if "Rough" in maps:
        rg = _img(nt, maps["Rough"], True, (-900, -260), mp)
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-560, -260)
        mr.inputs["To Min"].default_value = rough_lo
        mr.inputs["To Max"].default_value = rough_hi
        nt.links.new(rg.outputs["Color"], mr.inputs["Value"])
        rough_out = mr.outputs["Result"]
    else:
        rough_out = None

    # normal
    if "nor_gl" in maps:
        nr = _img(nt, maps["nor_gl"], True, (-900, -560), mp)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-560, -560)
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(nr.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    if darken != 1.0:
        dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = "RGBA"
        dk.blend_type = "MULTIPLY"; dk.location = (-260, 380)
        sock(dk, "Factor", "VALUE").default_value = 1.0
        nt.links.new(color_out, sock(dk, "A", "RGBA"))
        sock(dk, "B", "RGBA").default_value = (darken, darken, darken, 1.0)
        color_out = dk.outputs["Result"]

    # ---- moss / grime layer on upward faces ----
    if moss > 0:
        geo = nt.nodes.new("ShaderNodeNewGeometry"); geo.location = (-1400, -900)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-1200, -900)
        nt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-1000, -900)
        ramp.color_ramp.elements[0].position = 0.25
        ramp.color_ramp.elements[1].position = 0.85
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])

        noi = nt.nodes.new("ShaderNodeTexNoise"); noi.location = (-1000, -1200)
        noi.inputs["Scale"].default_value = 7.0
        noi.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
        nramp = nt.nodes.new("ShaderNodeValToRGB"); nramp.location = (-800, -1200)
        nramp.color_ramp.elements[0].position = 0.42
        nramp.color_ramp.elements[1].position = 0.62
        nt.links.new(noi.outputs["Fac"], nramp.inputs["Fac"])

        m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
        m1.location = (-560, -1000)
        nt.links.new(ramp.outputs["Color"], m1.inputs[0])
        nt.links.new(nramp.outputs["Color"], m1.inputs[1])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
        m2.location = (-380, -1000); m2.inputs[1].default_value = moss
        nt.links.new(m1.outputs["Value"], m2.inputs[0])
        mossfac = m2.outputs["Value"]

        mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"
        mm.blend_type = "MIX"; mm.location = (-150, 200)
        nt.links.new(mossfac, sock(mm, "Factor", "VALUE"))
        nt.links.new(color_out, sock(mm, "A", "RGBA"))
        sock(mm, "B", "RGBA").default_value = (*moss_color, 1.0)
        color_out = mm.outputs["Result"]

        # moss is rougher than the substrate
        if rough_out is not None:
            rm = nt.nodes.new("ShaderNodeMix"); rm.data_type = "FLOAT"
            rm.location = (-150, -300)
            nt.links.new(mossfac, sock(rm, "Factor", "VALUE"))
            nt.links.new(rough_out, sock(rm, "A", "VALUE"))
            sock(rm, "B", "VALUE").default_value = 0.95
            rough_out = rm.outputs["Result"]

    nt.links.new(color_out, bsdf.inputs["Base Color"])
    if rough_out is not None:
        nt.links.new(rough_out, bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    return mat


def verify(mat):
    """Return (ok, msg). A gray Principled with no image feeding base color is a failure."""
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return False, "no principled"
    imgs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
    loaded = [n for n in imgs if n.image and n.image.size[0] > 0]
    bc = bsdf.inputs["Base Color"].is_linked
    nl = bsdf.inputs["Normal"].is_linked
    rl = bsdf.inputs["Roughness"].is_linked
    ok = bc and len(loaded) >= 2
    return ok, f"imgs={len(imgs)} loaded={len(loaded)} basecolor={bc} rough={rl} normal={nl}"


# ---------------------------------------------------------------- procedural

def _base(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    return mat, nt, out


def make_rope():
    """Twisted-fibre rope: wave texture along the strand + noise fuzz."""
    mat, nt, out = _base("mat_rope")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (420, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-800, 0)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-620, 0)
    mp.inputs["Scale"].default_value = (1, 1, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexWave"); w.location = (-420, 100)
    w.wave_type = "BANDS"; w.bands_direction = "DIAGONAL"
    w.inputs["Scale"].default_value = 14.0
    w.inputs["Distortion"].default_value = 1.5
    nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-420, -220)
    n.inputs["Scale"].default_value = 90.0
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-180, 100)
    ramp.color_ramp.elements[0].color = (0.22, 0.15, 0.075, 1)
    ramp.color_ramp.elements[1].color = (0.44, 0.33, 0.185, 1)
    nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (180, -300)
    bump.inputs["Strength"].default_value = 0.55
    nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.92
    return mat


def make_water():
    """Deep gorge water.

    A physically-plain Principled surface reads muddy brown here: the camera is
    low, so almost every sight line hits the water at a grazing angle where
    Fresnel makes it a near-pure mirror of the warm sky. The reference art has
    water that stays TEAL. So mix a fixed teal body under the specular instead
    of letting Fresnel win -- glossy for the highlights, teal diffuse for colour.
    """
    mat, nt, out = _base("mat_water")
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (420, 0)
    mix.inputs["Fac"].default_value = 0.68          # 0 = all gloss, 1 = all body
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.location = (200, 120)
    gl.inputs["Roughness"].default_value = 0.15
    gl.inputs["Color"].default_value = (0.40, 0.47, 0.50, 1)
    nt.links.new(gl.outputs["BSDF"], mix.inputs[1])
    df = nt.nodes.new("ShaderNodeBsdfDiffuse"); df.location = (200, -140)
    df.inputs["Color"].default_value = (0.045, 0.175, 0.170, 1)   # teal body
    nt.links.new(df.outputs["BSDF"], mix.inputs[2])

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-800, -300)
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.location = (-560, -220)
    n1.inputs["Scale"].default_value = 4.0
    n1.inputs["Detail"].default_value = 8.0
    n1.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.location = (-560, -480)
    n2.inputs["Scale"].default_value = 22.0
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
    add.location = (-320, -320); add.inputs[1].default_value = 0.3
    nt.links.new(n2.outputs["Fac"], add.inputs[0])
    nt.links.new(n1.outputs["Fac"], add.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-80, -320)
    bump.inputs["Strength"].default_value = 0.32
    bump.inputs["Distance"].default_value = 0.04
    nt.links.new(add.outputs["Value"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], gl.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], df.inputs["Normal"])
    return mat


def make_tar():
    mat, nt, out = _base("mat_tar")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (420, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.012, 0.010, 0.009, 1)
    b.inputs["Roughness"].default_value = 0.14
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-500, -300)
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-300, -300)
    n.inputs["Scale"].default_value = 12.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (120, -300)
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return mat


def make_lantern_glass(strength=28.0, color=(1.0, 0.62, 0.26)):
    """Warm emissive lantern glass -- the single biggest mood cue in the ref."""
    mat, nt, out = _base("mat_lantern_glass")
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (420, 0)
    e.inputs["Color"].default_value = (*color, 1.0)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_iron():
    mat, nt, out = _base("mat_iron")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (420, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.045, 0.038, 0.032, 1)
    b.inputs["Metallic"].default_value = 0.85
    b.inputs["Roughness"].default_value = 0.62
    return mat


def make_glass_dark():
    """Window glass: dark, glossy, slightly warm interior tint (reads lit at night)."""
    mat, nt, out = _base("mat_glass_dark")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (420, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.030, 0.028, 0.026, 1)
    b.inputs["Roughness"].default_value = 0.10
    b.inputs["Metallic"].default_value = 0.30
    return mat


def make_all():
    """Build every kit material. Returns {name: (ok, msg)}."""
    made = []
    made.append(make_tex_mat("mat_deck", scale=1.0, moss=0.55, rough_lo=0.55,
                             darken=0.62, normal_strength=1.2))
    made.append(make_tex_mat("mat_timber", scale=0.7, moss=0.42, rough_lo=0.60,
                             darken=0.38, tint=(0.27, 0.23, 0.19), tint_fac=0.60,
                             normal_strength=1.2))
    made.append(make_tex_mat("mat_wallwood", scale=0.8, moss=0.35, rough_lo=0.45))
    made.append(make_tex_mat("mat_wallwood_dark", scale=0.8, moss=0.28, rough_lo=0.45,
                             tint=(0.30, 0.10, 0.07), tint_fac=0.35))
    made.append(make_tex_mat("mat_plaster", scale=1.0, moss=0.30, rough_lo=0.60))
    made.append(make_tex_mat("mat_rock", scale=0.17, moss=0.45, rough_lo=0.55,
                             darken=0.72, normal_strength=1.3))
    made.append(make_tex_mat("mat_shingle", scale=1.4, moss=0.75, rough_lo=0.50,
                             normal_strength=1.2))
    made.append(make_tex_mat("mat_mosswood", scale=1.0, moss=0.25, rough_lo=0.60))
    made.append(make_tex_mat("mat_metal", scale=1.0, moss=0.20, rough_lo=0.40))
    made.append(make_tex_mat("mat_ground", scale=0.6, moss=0.30, rough_lo=0.65))
    made += [make_rope(), make_water(), make_tar(), make_lantern_glass(),
             make_iron(), make_glass_dark()]
    return {m.name: verify(m) for m in made}
