"""Interior material library for del-cottage-int (Keepers' Cottage).

Same spine as kit_materials.py (Diffuse x AO -> Base Color, Rough -> Roughness,
nor_gl -> Normal, OBJECT-SPACE BOX projection so nothing needs UVs) but tuned
for an INTERIOR:

  * no moss.  Instead a `grime` layer -- warm soot/smoke that collects where the
    hearth smoke goes (upward faces + a vertical gradient near the ceiling) and
    a `wear` layer that polishes/lightens the horizontal traffic surfaces.
  * a large-scale colour/value breakup ("blotch") node on every textured
    material.  A 1k tile across a 9u floor repeats ~9x; a slow noise multiply
    over the top is what stops the eye locking onto the repeat.
  * painted timber: the town palette calls for oxblood red / moss green trim,
    so paint is a colour laid OVER the wood texture through a wear mask, and
    the bare wood shows through on the edges people touch.

Nothing here scales kit objects -- these materials are for locally built
geometry, and for remapping kit props to their un-mossed interior twins.
"""
import bpy, json, os

TEXDIR = "/Users/junshernchan/projects/multiplayer-rpg/tools/textures"
MAN = {}
for f in ("_manifest.json", "_manifest_int.json"):
    p = os.path.join(TEXDIR, f)
    if os.path.exists(p):
        MAN.update(json.load(open(p)))

OXBLOOD = (0.265, 0.047, 0.038)
MOSSGREEN = (0.082, 0.112, 0.060)


def sock(node, name, stype=None):
    m = [s for s in node.inputs if s.name == name]
    if stype:
        t = [s for s in m if s.type == stype]
        if t:
            return t[0]
    return m[0] if m else None


def _base(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (800, 0)
    mat.use_fake_user = True
    return mat, nt, out


def _img(nt, path, noncolor, loc, mapping, blend=0.35):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        n.image.colorspace_settings.name = "Non-Color"
    n.location = loc
    n.interpolation = "Smart"
    n.projection = "BOX"
    n.projection_blend = blend
    n.extension = "REPEAT"
    nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
    return n


def _mix_rgb(nt, fac, a, b, blend="MIX", loc=(0, 0)):
    """fac/a/b may be sockets or constants."""
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "RGBA"
    m.blend_type = blend; m.location = loc
    fs, as_, bs = sock(m, "Factor", "VALUE"), sock(m, "A", "RGBA"), sock(m, "B", "RGBA")
    if hasattr(fac, "is_output"):
        nt.links.new(fac, fs)
    else:
        fs.default_value = fac
    for s, v in ((as_, a), (bs, b)):
        if hasattr(v, "is_output"):
            nt.links.new(v, s)
        else:
            s.default_value = (*v, 1.0) if len(v) == 3 else v
    return m.outputs["Result"]


def _mix_val(nt, fac, a, b, loc=(0, 0)):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "FLOAT"; m.location = loc
    fs, as_, bs = sock(m, "Factor", "VALUE"), sock(m, "A", "VALUE"), sock(m, "B", "VALUE")
    if hasattr(fac, "is_output"):
        nt.links.new(fac, fs)
    else:
        fs.default_value = fac
    for s, v in ((as_, a), (bs, b)):
        if hasattr(v, "is_output"):
            nt.links.new(v, s)
        else:
            s.default_value = v
    return m.outputs["Result"]


def _noise(nt, tc, scale, detail=6.0, rough=0.5, loc=(0, 0), coord="Object"):
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = loc
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(tc.outputs[coord], n.inputs["Vector"])
    return n


def _ramp(nt, fac, lo, hi, loc=(0, 0)):
    r = nt.nodes.new("ShaderNodeValToRGB"); r.location = loc
    r.color_ramp.elements[0].position = lo
    r.color_ramp.elements[1].position = hi
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _mul(nt, a, b, loc=(0, 0), op="MULTIPLY"):
    m = nt.nodes.new("ShaderNodeMath"); m.operation = op; m.location = loc
    for i, v in enumerate((a, b)):
        if hasattr(v, "is_output"):
            nt.links.new(v, m.inputs[i])
        else:
            m.inputs[i].default_value = v
    return m.outputs["Value"]


# --------------------------------------------------------------- textured mat

def int_mat(name, src=None, scale=1.0, rough_lo=0.35, rough_hi=1.0,
            normal_strength=1.0, darken=1.0, tint=None, tint_fac=0.0,
            blotch=0.30, blotch_scale=0.55, blotch_dark=0.45,
            grime=0.0, grime_color=(0.055, 0.042, 0.034), grime_scale=3.0,
            grime_up=True, wear=0.0, wear_color=(0.42, 0.30, 0.19),
            wear_scale=1.4, paint=None, paint_wear=0.35, paint_scale=2.2,
            spec=0.32, sheen=0.0, proj_blend=0.35, soot=None):
    """Build one interior material.

    paint       : (r,g,b) painted over the wood; paint_wear rubs it back off.
    grime       : 0..1 soot; deposits on upward faces (grime_up) x noise.
    wear        : 0..1 traffic polish; lightens + smooths upward faces.
    blotch      : large-scale value variation that hides texture tiling.
    """
    entry = MAN[src or name]
    maps = entry["maps"]
    mat, nt, out = _base(name)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (520, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1600, 0)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-1400, 0)
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    diff = _img(nt, maps["Diffuse"], False, (-1150, 320), mp, proj_blend)
    color = diff.outputs["Color"]

    if "AO" in maps:
        ao = _img(nt, maps["AO"], True, (-1150, 40), mp, proj_blend)
        color = _mix_rgb(nt, 0.5, color, ao.outputs["Color"], "MULTIPLY", (-880, 320))

    if tint is not None and tint_fac > 0:
        color = _mix_rgb(nt, tint_fac, color, tint, "COLOR", (-700, 380))

    if darken != 1.0:
        color = _mix_rgb(nt, 1.0, color, (darken, darken, darken), "MULTIPLY", (-560, 380))

    # roughness
    if "Rough" in maps:
        rg = _img(nt, maps["Rough"], True, (-1150, -280), mp, proj_blend)
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-880, -280)
        mr.inputs["To Min"].default_value = rough_lo
        mr.inputs["To Max"].default_value = rough_hi
        nt.links.new(rg.outputs["Color"], mr.inputs["Value"])
        rough = mr.outputs["Result"]
    else:
        rough = None

    # normal (bump chain gets appended later if needed)
    nrm = None
    if "nor_gl" in maps:
        nr = _img(nt, maps["nor_gl"], True, (-1150, -600), mp, proj_blend)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-880, -600)
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(nr.outputs["Color"], nm.inputs["Color"])
        nrm = nm.outputs["Normal"]

    geo = nt.nodes.new("ShaderNodeNewGeometry"); geo.location = (-1600, -1000)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-1400, -1000)
    nt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])

    # ---- paint: colour laid over the wood, rubbed back on wear ----
    if paint is not None:
        pn = _noise(nt, tc, paint_scale, detail=8.0, rough=0.7, loc=(-1150, -1250))
        # keep = 1 where the paint survives.  The ramp has to sit BELOW the
        # noise mean or the paint never covers anything.
        lo = 0.10 + paint_wear * 0.30
        pmask = _ramp(nt, pn.outputs["Fac"], lo, lo + 0.26, loc=(-950, -1250))
        # slight per-patch value drift so the paint isn't a flat vinyl sheet
        pv = _noise(nt, tc, 0.9, detail=4.0, loc=(-1150, -1500))
        pcol = _mix_rgb(nt, 0.35,
                        (paint[0], paint[1], paint[2]),
                        (paint[0] * 1.55 + 0.02, paint[1] * 1.55 + 0.02, paint[2] * 1.55 + 0.02),
                        "MIX", (-700, -1400))
        pcol = _mix_rgb(nt, pv.outputs["Fac"], pcol,
                        (paint[0] * 0.55, paint[1] * 0.55, paint[2] * 0.55),
                        "MIX", (-520, -1400))
        keep = _mul(nt, pmask, 1.0, (-360, -1250))       # 1 = paint intact
        color = _mix_rgb(nt, keep, color, pcol, "MIX", (-200, 200))
        if rough is not None:
            rough = _mix_val(nt, keep, rough, 0.52, (-200, -400))

    # ---- traffic wear: upward faces get polished & lightened ----
    if wear > 0:
        up = _ramp(nt, sep.outputs["Z"], 0.30, 0.95, (-1150, -900))
        wn = _noise(nt, tc, wear_scale, detail=8.0, rough=0.62, loc=(-1150, -1050))
        wmask = _ramp(nt, wn.outputs["Fac"], 0.36, 0.70, (-950, -1050))
        f = _mul(nt, _mul(nt, up, wmask, (-760, -960)), wear, (-600, -960))
        color = _mix_rgb(nt, f, color, wear_color, "MIX", (-60, 120))
        if rough is not None:
            rough = _mix_val(nt, f, rough, 0.28, (-60, -460))

    # ---- soot / grime ----
    if grime > 0:
        gd = sep.outputs["Z"] if grime_up else None
        if grime_up:
            gm = _ramp(nt, sep.outputs["Z"], 0.18, 0.92, (-1150, -760))
        else:   # underside / ceiling soot
            inv = _mul(nt, sep.outputs["Z"], -1.0, (-1250, -760))
            gm = _ramp(nt, inv, 0.05, 0.85, (-1050, -760))
        gn = _noise(nt, tc, grime_scale, detail=9.0, rough=0.68, loc=(-1150, -640))
        gmask = _ramp(nt, gn.outputs["Fac"], 0.34, 0.74, (-950, -640))
        f = _mul(nt, _mul(nt, gm, gmask, (-760, -700)), grime, (-600, -700))
        color = _mix_rgb(nt, f, color, grime_color, "MIX", (80, 60))
        if rough is not None:
            rough = _mix_val(nt, f, rough, 0.93, (80, -420))

    # ---- smoke gloom: everything high in the room is soot-stained and dark.
    # Driven by WORLD z, so it crosses object boundaries as one gradient and
    # gives the room its "warm below, gloom in the rafters" falloff.
    if soot:
        amt, sz0, sz1 = soot
        pos = nt.nodes.new("ShaderNodeSeparateXYZ"); pos.location = (-1400, -1400)
        nt.links.new(geo.outputs["Position"], pos.inputs["Vector"])
        mr2 = nt.nodes.new("ShaderNodeMapRange"); mr2.location = (-1150, -1400)
        mr2.inputs["From Min"].default_value = sz0
        mr2.inputs["From Max"].default_value = sz1
        mr2.clamp = True
        nt.links.new(pos.outputs["Z"], mr2.inputs["Value"])
        sn = _noise(nt, tc, 1.3, detail=6.0, loc=(-1150, -1650))
        smix = _mix_val(nt, 0.45, mr2.outputs["Result"], sn.outputs["Fac"], (-930, -1450))
        f = _mul(nt, smix, amt, (-760, -1450))
        color = _mix_rgb(nt, f, color, (0.021, 0.017, 0.015), "MIX", (150, 160))
        if rough is not None:
            rough = _mix_val(nt, f, rough, 0.95, (150, -380))

    # ---- large-scale blotch: kills the tiling read ----
    if blotch > 0:
        bn = _noise(nt, tc, blotch_scale, detail=4.0, rough=0.55, loc=(-1150, -420))
        bfac = _mul(nt, bn.outputs["Fac"], blotch, (-950, -420))
        color = _mix_rgb(nt, bfac, color, (blotch_dark, blotch_dark * 0.94, blotch_dark * 0.88),
                         "MULTIPLY", (240, 40))

    nt.links.new(color, bsdf.inputs["Base Color"])
    if rough is not None:
        nt.links.new(rough, bsdf.inputs["Roughness"])
    if nrm is not None:
        nt.links.new(nrm, bsdf.inputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if sheen > 0:
        bsdf.inputs["Sheen Weight"].default_value = sheen
        bsdf.inputs["Sheen Roughness"].default_value = 0.4
    return mat


# --------------------------------------------------------------- procedural

def simple(name, color, rough=0.55, metal=0.0, spec=0.35, noise=None,
           bump=0.0, bump_scale=40.0, ior=1.45, sheen=0.0):
    mat, nt, out = _base(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (500, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["IOR"].default_value = ior
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-700, -300)
    if noise:
        n = _noise(nt, tc, noise[0], detail=8.0, loc=(-450, 200))
        c2 = noise[1]
        col = _mix_rgb(nt, n.outputs["Fac"], color, c2, "MIX", (-100, 200))
        nt.links.new(col, b.inputs["Base Color"])
        rr = _mix_val(nt, n.outputs["Fac"], rough, min(1.0, rough + 0.25), (-100, -100))
        nt.links.new(rr, b.inputs["Roughness"])
    if bump > 0:
        nb = _noise(nt, tc, bump_scale, detail=8.0, loc=(-450, -400))
        bm = nt.nodes.new("ShaderNodeBump"); bm.location = (100, -400)
        bm.inputs["Strength"].default_value = bump
        nt.links.new(nb.outputs["Fac"], bm.inputs["Height"])
        nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return mat


def emissive(name, color, strength):
    mat, nt, out = _base(name)
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (500, 0)
    e.inputs["Color"].default_value = (*color, 1.0)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_fire():
    """Hearth flame: emission ramped hot-white core -> orange -> smoke tips,
    driven by a stretched noise so each flame body differs.  Alpha-less: the
    flame meshes are thin tapered cones, the ramp kills the outer shell."""
    mat, nt, out = _base("mat_fire")
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (600, 0)
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (380, 140)
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission"); em.location = (380, -140)
    em.inputs["Strength"].default_value = 3.6
    nt.links.new(em.outputs["Emission"], mix.inputs[2])

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-720, 0)
    mp.inputs["Scale"].default_value = (7.0, 7.0, 1.7)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-520, 0)
    n.inputs["Scale"].default_value = 3.4
    n.inputs["Detail"].default_value = 9.0
    n.inputs["Roughness"].default_value = 0.72
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])

    # height along the flame (object Z) modulates both colour and opacity
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-720, -320)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    h = nt.nodes.new("ShaderNodeMapRange"); h.location = (-520, -320)
    h.inputs["From Min"].default_value = 0.0
    h.inputs["From Max"].default_value = 0.34
    nt.links.new(sep.outputs["Z"], h.inputs["Value"])

    comb = _mul(nt, n.outputs["Fac"], 0.75, (-300, -140))
    comb = _mul(nt, comb, h.outputs["Result"], (-160, -140), op="ADD")

    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (40, 120)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.05; cr.elements[0].color = (1.0, 0.62, 0.16, 1)
    cr.elements[1].position = 0.62; cr.elements[1].color = (0.65, 0.10, 0.012, 1)
    e2 = cr.elements.new(0.26); e2.color = (1.0, 0.90, 0.55, 1)
    nt.links.new(comb, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])

    op = nt.nodes.new("ShaderNodeValToRGB"); op.location = (40, -300)
    op.color_ramp.elements[0].position = 0.20
    op.color_ramp.elements[1].position = 0.78
    nt.links.new(comb, op.inputs["Fac"])
    inv = _mul(nt, 1.0, op.outputs["Color"], (340, -320), op="SUBTRACT")
    nt.links.new(inv, mix.inputs["Fac"])
    mat.surface_render_method = 'BLENDED'
    return mat


def make_embers():
    """Glowing log bed: charcoal that goes incandescent in the cracks."""
    mat, nt, out = _base("mat_embers")
    add = nt.nodes.new("ShaderNodeAddShader"); add.location = (600, 0)
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (380, 200)
    b.inputs["Base Color"].default_value = (0.020, 0.014, 0.011, 1)
    b.inputs["Roughness"].default_value = 0.86
    nt.links.new(b.outputs["BSDF"], add.inputs[0])
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (380, -160)
    nt.links.new(e.outputs["Emission"], add.inputs[1])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-700, 0)
    n = _noise(nt, tc, 26.0, detail=10.0, rough=0.75, loc=(-480, 0))
    m = _ramp(nt, n.outputs["Fac"], 0.52, 0.78, (-260, 0))
    col = _mix_rgb(nt, m, (0.35, 0.045, 0.004), (1.0, 0.52, 0.10), "MIX", (60, -60))
    nt.links.new(col, e.inputs["Color"])
    st = _mul(nt, m, 2.6, (60, -300))
    nt.links.new(st, e.inputs["Strength"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.location = (140, 240)
    bm.inputs["Strength"].default_value = 0.5
    nt.links.new(n.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return mat


def make_dusk_glass():
    """The river-side glazing.  Old wavy glass: transmissive, faintly green,
    with a rough bump so the dusk beyond reads as a soft blue smear, not a
    sharp photograph."""
    mat, nt, out = _base("mat_glass_dusk")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (500, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.82, 0.90, 0.90, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.09
    b.inputs["IOR"].default_value = 1.48
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-700, -300)
    w = nt.nodes.new("ShaderNodeTexWave"); w.location = (-450, -300)
    w.wave_type = "BANDS"; w.bands_direction = "Z"
    w.inputs["Scale"].default_value = 26.0
    w.inputs["Distortion"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.location = (140, -300)
    bm.inputs["Strength"].default_value = 0.16
    bm.inputs["Distance"].default_value = 0.004
    nt.links.new(w.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return mat


def make_dusk_backdrop():
    """Emissive matte seen through the glass: dusk gorge light -- deep blue at
    the top, a warm band where the sun has just gone, dark cliff below."""
    mat, nt, out = _base("mat_dusk_matte")
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (520, 0)
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-900, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-700, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-500, 0)
    mr.inputs["From Min"].default_value = -3.0
    mr.inputs["From Max"].default_value = 5.0
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-260, 0)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.02; cr.elements[0].color = (0.020, 0.036, 0.055, 1)
    cr.elements[1].position = 1.00; cr.elements[1].color = (0.030, 0.052, 0.105, 1)
    a = cr.elements.new(0.46); a.color = (0.30, 0.26, 0.32, 1)
    b2 = cr.elements.new(0.58); b2.color = (0.70, 0.44, 0.28, 1)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    # cloud/haze breakup so it is not a clean gradient
    n = _noise(nt, tc, 1.6, detail=8.0, rough=0.6, loc=(-500, -320))
    col = _mix_rgb(nt, 0.22, ramp.outputs["Color"], n.outputs["Color"], "OVERLAY", (60, 0))
    nt.links.new(col, e.inputs["Color"])
    e.inputs["Strength"].default_value = 1.1
    return mat


def make_all():
    m = {}
    # --- structure -------------------------------------------------------
    m["floor"] = int_mat("mat_int_floor", scale=0.42, rough_lo=0.46, rough_hi=0.92,
                         darken=0.72, tint=(0.31, 0.19, 0.11), tint_fac=0.30,
                         normal_strength=1.15, blotch=0.42, blotch_scale=0.38,
                         blotch_dark=0.42, wear=0.55, wear_color=(0.30, 0.20, 0.125),
                         wear_scale=0.75, grime=0.22, grime_scale=1.1, spec=0.22)
    m["plaster"] = int_mat("mat_int_plaster", scale=1.55, rough_lo=0.66, rough_hi=1.0,
                           darken=0.82, tint=(0.46, 0.345, 0.235), tint_fac=0.56,
                           normal_strength=1.70, blotch=0.24, blotch_scale=0.9,
                           blotch_dark=0.52, grime=0.34, grime_scale=1.7,
                           grime_color=(0.070, 0.052, 0.040), spec=0.20,
                           soot=(0.46, 1.7, 3.6))
    m["stone"] = int_mat("mat_int_stone", scale=0.30, rough_lo=0.55, rough_hi=1.0,
                         darken=0.52, tint=(0.22, 0.19, 0.17), tint_fac=0.35,
                         normal_strength=1.4, blotch=0.40, blotch_scale=0.5,
                         blotch_dark=0.44, grime=0.55, grime_scale=2.2,
                         grime_color=(0.030, 0.024, 0.020), spec=0.22,
                         soot=(0.45, 1.5, 3.6))
    m["hearth"] = int_mat("mat_int_hearth", scale=0.34, rough_lo=0.55, rough_hi=1.0,
                          darken=0.44, tint=(0.20, 0.17, 0.15), tint_fac=0.40,
                          normal_strength=1.45, blotch=0.45, blotch_scale=0.7,
                          blotch_dark=0.40, grime=0.75, grime_scale=3.0,
                          grime_color=(0.018, 0.014, 0.012), spec=0.18,
                          soot=(0.55, 1.5, 3.4))
    # beams: dark oiled timber, soot on the UNDERSIDE (smoke rolls along them)
    m["beam"] = int_mat("mat_int_beam", src="mat_int_wood", scale=0.5,
                        rough_lo=0.45, rough_hi=0.95, darken=0.40,
                        tint=(0.26, 0.16, 0.09), tint_fac=0.45, normal_strength=1.3,
                        blotch=0.34, blotch_scale=0.6, blotch_dark=0.46,
                        grime=0.42, grime_up=False, grime_scale=2.4, spec=0.26,
                        soot=(0.55, 2.0, 3.6))
    m["wood"] = int_mat("mat_int_wood", scale=0.75, rough_lo=0.33, rough_hi=0.80,
                        darken=0.62, tint=(0.36, 0.22, 0.12), tint_fac=0.32,
                        normal_strength=1.0, blotch=0.30, blotch_scale=1.1,
                        blotch_dark=0.50, wear=0.45, wear_color=(0.46, 0.31, 0.185),
                        wear_scale=2.6, spec=0.38)
    m["plank"] = int_mat("mat_int_plank", scale=0.7, rough_lo=0.42, rough_hi=0.92,
                         darken=0.58, tint=(0.32, 0.22, 0.14), tint_fac=0.35,
                         normal_strength=1.1, blotch=0.32, blotch_scale=0.9,
                         blotch_dark=0.48, grime=0.20, spec=0.30,
                         soot=(0.35, 2.0, 3.6))
    # --- painted trim (town palette) --------------------------------------
    m["paint_red"] = int_mat("mat_int_paint_red", src="mat_int_plank", scale=0.7,
                             rough_lo=0.40, rough_hi=0.85, darken=0.52,
                             normal_strength=1.0, paint=OXBLOOD, paint_wear=0.30,
                             paint_scale=2.8, blotch=0.28, blotch_scale=0.8,
                             blotch_dark=0.52, grime=0.18, spec=0.42,
                             soot=(0.30, 1.9, 3.6))
    m["paint_green"] = int_mat("mat_int_paint_green", src="mat_int_plank", scale=0.7,
                               rough_lo=0.40, rough_hi=0.85, darken=0.52,
                               normal_strength=1.0, paint=MOSSGREEN, paint_wear=0.34,
                               paint_scale=3.2, blotch=0.28, blotch_scale=0.8,
                               blotch_dark=0.52, grime=0.20, spec=0.42,
                               soot=(0.30, 1.9, 3.6))
    # --- soft goods --------------------------------------------------------
    m["rug"] = int_mat("mat_int_rug", scale=1.05, rough_lo=0.70, rough_hi=1.0,
                       darken=1.30, tint=(0.62, 0.135, 0.070), tint_fac=0.90,
                       normal_strength=1.6, blotch=0.36, blotch_scale=1.5,
                       blotch_dark=0.46, sheen=0.45, spec=0.14)
    m["linen"] = int_mat("mat_int_linen", scale=1.6, rough_lo=0.72, rough_hi=1.0,
                         darken=0.92, tint=(0.72, 0.66, 0.52), tint_fac=0.35,
                         normal_strength=1.5, blotch=0.26, blotch_scale=2.2,
                         blotch_dark=0.60, sheen=0.55, spec=0.16)
    # --- procedural --------------------------------------------------------
    simple("mat_int_iron", (0.030, 0.026, 0.023), rough=0.52, metal=0.88,
           bump=0.22, bump_scale=90.0)
    simple("mat_int_brass", (0.62, 0.42, 0.16), rough=0.34, metal=1.0,
           bump=0.12, bump_scale=120.0)
    simple("mat_int_copper", (0.55, 0.26, 0.13), rough=0.40, metal=1.0,
           bump=0.16, bump_scale=110.0,
           noise=(30.0, (0.24, 0.30, 0.22)))
    simple("mat_int_crock", (0.60, 0.55, 0.45), rough=0.22, spec=0.6,
           noise=(18.0, (0.42, 0.36, 0.28)), bump=0.05, bump_scale=200.0)
    simple("mat_int_crock_blue", (0.36, 0.44, 0.52), rough=0.20, spec=0.6,
           noise=(16.0, (0.20, 0.26, 0.34)), bump=0.05, bump_scale=200.0)
    simple("mat_int_bowlwood", (0.20, 0.125, 0.062), rough=0.42,
           noise=(24.0, (0.30, 0.20, 0.10)), bump=0.10, bump_scale=60.0)
    simple("mat_int_bread", (0.42, 0.235, 0.088), rough=0.78,
           noise=(22.0, (0.22, 0.105, 0.032)), bump=0.55, bump_scale=52.0)
    simple("mat_int_stew", (0.155, 0.075, 0.030), rough=0.24, spec=0.7,
           noise=(40.0, (0.22, 0.14, 0.05)), bump=0.08, bump_scale=70.0)
    simple("mat_int_wax", (0.86, 0.80, 0.62), rough=0.36, spec=0.4,
           bump=0.10, bump_scale=90.0)
    simple("mat_int_oilskin", (0.055, 0.062, 0.042), rough=0.30, spec=0.55,
           noise=(9.0, (0.115, 0.095, 0.052)), bump=0.28, bump_scale=34.0, sheen=0.2)
    simple("mat_int_paper", (0.56, 0.49, 0.35), rough=0.82,
           noise=(11.0, (0.40, 0.33, 0.22)), bump=0.14, bump_scale=45.0)
    simple("mat_int_ink", (0.055, 0.045, 0.048), rough=0.72)
    simple("mat_int_ash", (0.115, 0.105, 0.098), rough=0.94,
           noise=(30.0, (0.055, 0.048, 0.045)), bump=0.40, bump_scale=48.0)
    simple("mat_int_glassjug", (0.28, 0.34, 0.30), rough=0.12, spec=0.8, ior=1.5)
    m["rug_border"] = int_mat("mat_int_rug_border", src="mat_int_rug", scale=1.05,
                              rough_lo=0.70, rough_hi=1.0, darken=1.05,
                              tint=(0.115, 0.135, 0.070), tint_fac=0.88,
                              normal_strength=1.6, blotch=0.30, blotch_scale=1.5,
                              blotch_dark=0.50, sheen=0.45, spec=0.14)
    simple("mat_int_soot", (0.0135, 0.0115, 0.0105), rough=0.93,
           noise=(14.0, (0.045, 0.036, 0.030)), bump=0.55, bump_scale=26.0)
    simple("mat_int_charlog", (0.026, 0.020, 0.017), rough=0.88,
           noise=(20.0, (0.075, 0.055, 0.042)), bump=0.45, bump_scale=40.0)
    make_fire(); make_embers(); make_dusk_glass(); make_dusk_backdrop()
    emissive("mat_int_flame_small", (1.0, 0.68, 0.28), 90.0)
    emissive("mat_int_lampglass", (1.0, 0.66, 0.30), 22.0)
    return m


def verify():
    bad = []
    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        nt = mat.node_tree
        b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        imgs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
        broken = [n for n in imgs if not n.image or n.image.size[0] == 0]
        if broken:
            bad.append((mat.name, "unloaded images: %d" % len(broken)))
        elif b is not None and imgs and not b.inputs["Base Color"].is_linked:
            bad.append((mat.name, "textures present but base colour unlinked"))
    return bad
