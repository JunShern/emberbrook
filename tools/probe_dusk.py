"""Dellhollow Boatyard probe -- dusk / vegetation / colour art-direction pass.

Applied ON TOP of the scene `probe_build.py` produces (i.e. on `probe.blend`),
not instead of it. Re-runnable: everything this pass creates is named with the
`v10_` prefix and is purged before rebuilding, so the script can be run against
an already-patched probe.blend as many times as you like.

Answers the coordinator's critique of probe_v9:
  1. DUSK, not afternoon      -> `dusk_light()`
  2. VEGETATION               -> `vegetation()`
  3. COLOUR SEPARATION        -> `colour_structures()`
  4. FOREGROUND LIFE          -> `foreground()`
  5. FAR DEPTH                -> `far_depth()`

Run headless:
    blender -b tools/blends/probe.blend -P tools/probe_dusk.py -- \
        --out docs/qa/dellhollow-rebuild/probe_v10.png --samples 224 --save
"""
import bpy, bmesh, math, random, sys, os, importlib.util
from mathutils import Matrix, Vector, Euler, noise

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TAG = "v10_"
R = random.Random(90210)


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pb = _mod("pb", ROOT + "/tools/probe_build.py")
km = _mod("km", ROOT + "/tools/kit_materials.py")
ru = _mod("ru", ROOT + "/tools/render_util.py")


# --------------------------------------------------------------- housekeeping

def coll(name, exclude=False):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    if exclude:
        lc = bpy.context.view_layer.layer_collection.children.get(name)
        if lc:
            lc.exclude = True
    return c


def purge():
    """Drop everything a previous run of this pass created."""
    dead = [o for o in bpy.data.objects if o.name.startswith(TAG)]
    for o in dead:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0 and me.name.startswith(TAG):
            bpy.data.meshes.remove(me)


def M(name):
    return bpy.data.materials.get(name)


def derive(manifest_key, newname, **kw):
    """Build a NEW material from a PolyHaven manifest entry without stealing the
    existing datablock of that name (make_tex_mat writes into `manifest_key`)."""
    keep = bpy.data.materials.get(manifest_key)
    if keep:
        keep.name = manifest_key + "__hold"
    m = km.make_tex_mat(manifest_key, **kw)
    m.name = newname
    if keep:
        keep.name = manifest_key
    return m


def _base(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (800, 0)
    return mat, nt, out


# ------------------------------------------------------------------- geometry

class Mesh(pb.Mesh):
    """probe_build.Mesh plus a UV layer and leaf-card support.

    Leaf cards need real UVs: the foliage shader cuts the rectangle down to a
    leafy blob using a radial mask measured from the card centre, and object /
    generated coordinates cannot give per-card local space inside one mesh.
    """

    def __init__(self, name):
        super().__init__(name)
        self.uv = self.bm.loops.layers.uv.new("UVMap")

    def card(self, center, sx, sy, rot, mat):
        idx = self.mi(mat)
        mtx = (Matrix.Translation(center)
               @ Euler(rot, "XYZ").to_matrix().to_4x4())
        pts = [(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)]
        vs = [self.bm.verts.new(mtx @ Vector(p)) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = idx
        for l, uv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            l[self.uv].uv = uv

    def finish(self, c, bevel=0.0, seg=2, shade_smooth=False, weld=True):
        me = bpy.data.meshes.new(self.name)
        if weld:
            bmesh.ops.remove_doubles(self.bm, verts=list(self.bm.verts), dist=1e-5)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        c.objects.link(ob)
        if bevel:
            md = ob.modifiers.new("bev", "BEVEL")
            md.width = bevel; md.segments = seg
            md.limit_method = "ANGLE"; md.angle_limit = math.radians(40)
        for p in me.polygons:
            p.use_smooth = shade_smooth
        return ob


def place(src, loc, rot=(0, 0, 0), c=None, jitter=0.0, scale=1.0):
    o = src.copy()
    if jitter:
        rot = tuple(r + R.uniform(-jitter, jitter) for r in rot)
    o.location = loc
    o.rotation_euler = rot
    if scale != 1.0:
        o.scale = (scale, scale, scale)
    c.objects.link(o)
    return o


# ------------------------------------------------------------------ materials

def leaf_mat(name, cols, alpha_scale=9.0, cut=0.30, trans=0.32, rough=0.68,
             col_scale=2.5):
    """Leaf-card material.

    The card is a rectangle; the shader turns it into a ragged leafy blob:
    radial falloff from the UV centre x a noise field, hard-thresholded into
    alpha. Colour comes from a second, much larger noise so neighbouring clumps
    differ in hue instead of the whole canopy being one flat orange.
    """
    mat, nt, out = _base(name)
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1200, 0)

    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"
    sub.location = (-1000, -200)
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    nt.links.new(tc.outputs["UV"], sub.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    ln.location = (-840, -200)
    nt.links.new(sub.outputs["Vector"], ln.inputs[0])
    rad = nt.nodes.new("ShaderNodeMapRange"); rad.location = (-680, -200)
    rad.inputs["From Min"].default_value = 0.16
    rad.inputs["From Max"].default_value = 0.50
    rad.inputs["To Min"].default_value = 1.0
    rad.inputs["To Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], rad.inputs["Value"])

    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.location = (-840, -460)
    nz.inputs["Scale"].default_value = alpha_scale
    nz.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["UV"], nz.inputs["Vector"])
    nzr = nt.nodes.new("ShaderNodeMapRange"); nzr.location = (-680, -460)
    nzr.inputs["From Min"].default_value = 0.30
    nzr.inputs["From Max"].default_value = 0.62
    nt.links.new(nz.outputs["Fac"], nzr.inputs["Value"])

    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.location = (-480, -320)
    nt.links.new(rad.outputs["Result"], mul.inputs[0])
    nt.links.new(nzr.outputs["Result"], mul.inputs[1])
    thr = nt.nodes.new("ShaderNodeValToRGB"); thr.location = (-300, -320)
    thr.color_ramp.interpolation = "LINEAR"
    thr.color_ramp.elements[0].position = cut
    thr.color_ramp.elements[1].position = cut + 0.07
    nt.links.new(mul.outputs["Value"], thr.inputs["Fac"])

    # colour variation across the canopy
    cn = nt.nodes.new("ShaderNodeTexNoise"); cn.location = (-840, 320)
    cn.inputs["Scale"].default_value = col_scale
    cn.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], cn.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.location = (-600, 320)
    ramp = cr.color_ramp
    ramp.elements[0].position = 0.30
    ramp.elements[0].color = (*cols[0], 1)
    e = ramp.elements.new(0.50); e.color = (*cols[1], 1)
    ramp.elements[2].position = 0.70
    ramp.elements[2].color = (*cols[2], 1)
    nt.links.new(cn.outputs["Fac"], cr.inputs["Fac"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (-120, 300)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.location = (-120, 60)
    nt.links.new(cr.outputs["Color"], tl.inputs["Color"])
    leafmix = nt.nodes.new("ShaderNodeMixShader"); leafmix.location = (200, 160)
    leafmix.inputs["Fac"].default_value = trans
    nt.links.new(bsdf.outputs["BSDF"], leafmix.inputs[1])
    nt.links.new(tl.outputs["BSDF"], leafmix.inputs[2])

    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (200, -160)
    alpha = nt.nodes.new("ShaderNodeMixShader"); alpha.location = (500, 0)
    nt.links.new(thr.outputs["Color"], alpha.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], alpha.inputs[1])
    nt.links.new(leafmix.outputs["Shader"], alpha.inputs[2])
    nt.links.new(alpha.outputs["Shader"], out.inputs["Surface"])
    return mat


def grass_mat(name, base=(0.055, 0.075, 0.030), tip=(0.30, 0.30, 0.11), h=0.45):
    mat, nt, out = _base(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (500, 0)
    b.inputs["Roughness"].default_value = 0.75
    b.inputs["Specular IOR Level"].default_value = 0.2
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-600, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-420, 0)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-260, 0)
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = h
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.location = (-80, 0)
    cr.color_ramp.elements[0].color = (*base, 1)
    cr.color_ramp.elements[1].color = (*tip, 1)
    nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent"); tl.location = (500, -220)
    nt.links.new(cr.outputs["Color"], tl.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.location = (660, 0)
    mx.inputs["Fac"].default_value = 0.30
    nt.links.new(b.outputs["BSDF"], mx.inputs[1])
    nt.links.new(tl.outputs["BSDF"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return mat


def scatter_mat(name, density, color, aniso=0.3):
    mat, nt, out = _base(name)
    v = nt.nodes.new("ShaderNodeVolumeScatter"); v.location = (400, 0)
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = aniso
    nt.links.new(v.outputs["Volume"], out.inputs["Volume"])
    return mat


def materials():
    """Everything this pass adds or retunes."""
    made = {}
    # -- painted timber: the palette the style block asks for -----------------
    made["mat_paint_red"] = derive(
        "mat_wallwood", "mat_paint_red", scale=0.8, moss=0.30, rough_lo=0.45,
        tint=(0.40, 0.058, 0.042), tint_fac=1.0, darken=0.82)
    made["mat_paint_blue"] = derive(
        "mat_wallwood", "mat_paint_blue", scale=0.8, moss=0.26, rough_lo=0.45,
        tint=(0.070, 0.195, 0.330), tint_fac=0.96, darken=0.86)
    made["mat_shingle_mossy"] = derive(
        "mat_shingle", "mat_shingle_mossy", scale=1.35, moss=0.95,
        moss_color=(0.115, 0.200, 0.072), rough_lo=0.55, normal_strength=1.35,
        darken=0.80)
    # pale fresh-sawn timber: tonal separation against the weathered grey deck
    made["mat_freshwood"] = derive(
        "mat_deck", "mat_freshwood", scale=2.0, moss=0.0, rough_lo=0.68,
        darken=1.0, normal_strength=0.9)

    # -- vegetation -----------------------------------------------------------
    made["mat_leaf_autumn"] = leaf_mat(
        "mat_leaf_autumn",
        [(0.235, 0.062, 0.028), (0.330, 0.115, 0.032), (0.285, 0.180, 0.058)],
        alpha_scale=10.0, cut=0.25, trans=0.22)
    made["mat_leaf_autumn_far"] = leaf_mat(
        "mat_leaf_autumn_far",
        [(0.150, 0.058, 0.042), (0.190, 0.080, 0.044), (0.165, 0.100, 0.055)],
        alpha_scale=6.0, cut=0.16, col_scale=0.8, trans=0.10)
    made["mat_leaf_creeper"] = leaf_mat(
        "mat_leaf_creeper",
        [(0.042, 0.082, 0.026), (0.072, 0.115, 0.032), (0.190, 0.120, 0.032)],
        alpha_scale=12.0, cut=0.26, trans=0.26)
    vm, nt, out = _base("mat_vine")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (400, 0)
    b.inputs["Base Color"].default_value = (0.055, 0.048, 0.028, 1)
    b.inputs["Roughness"].default_value = 0.85
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    made["mat_vine"] = vm
    made["mat_grass"] = grass_mat("mat_grass")
    made["mat_fern"] = grass_mat("mat_fern", base=(0.035, 0.070, 0.028),
                                 tip=(0.12, 0.20, 0.055), h=0.55)

    # -- atmosphere -----------------------------------------------------------
    # Restraint: v10a stacked three dense layers over the whole gorge and the
    # frame went to orange soup -- exactly the v1 failure the manifest records.
    # These sit BEYOND the lock gates only, and only just thicken with distance.
    made["mat_haze_mid"] = scatter_mat("mat_haze_mid", 0.0034, (0.48, 0.50, 0.60))
    made["mat_haze_far"] = scatter_mat("mat_haze_far", 0.0080, (0.52, 0.54, 0.66))
    made["mat_haze_rim"] = scatter_mat("mat_haze_rim", 0.0135, (0.56, 0.57, 0.68))
    made["mat_glow"] = scatter_mat("mat_glow", 0.035, (1.0, 0.78, 0.50), aniso=0.6)
    # far-rim buildings must read as SHAPES, not as lit models
    sil, nt, out = _base("mat_silhouette")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (400, 0)
    b.inputs["Base Color"].default_value = (0.022, 0.019, 0.021, 1)
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.1
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    made["mat_silhouette"] = sil
    em, nt, out = _base("mat_embers")
    e = nt.nodes.new("ShaderNodeEmission"); e.location = (400, 0)
    e.inputs["Color"].default_value = (1.0, 0.30, 0.055, 1)
    e.inputs["Strength"].default_value = 14.0
    nt.links.new(e.outputs["Emission"], out.inputs["Surface"])
    made["mat_embers"] = em
    pk, nt, out = _base("mat_pumpkin")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (400, 0)
    b.inputs["Base Color"].default_value = (0.46, 0.135, 0.020, 1)
    b.inputs["Roughness"].default_value = 0.48
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    made["mat_pumpkin"] = pk
    for nm, col in (("mat_flag_red", (0.235, 0.032, 0.030)),
                    ("mat_flag_blue", (0.045, 0.115, 0.215)),
                    ("mat_flag_green", (0.055, 0.135, 0.062)),
                    ("mat_flag_ochre", (0.310, 0.185, 0.048))):
        fm, fnt, fout = _base(nm)
        d = fnt.nodes.new("ShaderNodeBsdfDiffuse"); d.location = (300, 90)
        d.inputs["Color"].default_value = (*col, 1)
        t = fnt.nodes.new("ShaderNodeBsdfTranslucent"); t.location = (300, -110)
        t.inputs["Color"].default_value = (*[min(1, v * 1.7) for v in col], 1)
        mx = fnt.nodes.new("ShaderNodeMixShader"); mx.location = (560, 0)
        mx.inputs["Fac"].default_value = 0.45
        fnt.links.new(d.outputs["BSDF"], mx.inputs[1])
        fnt.links.new(t.outputs["BSDF"], mx.inputs[2])
        fnt.links.new(mx.outputs["Shader"], fout.inputs["Surface"])
        made[nm] = fm
    w = M("mat_water")
    if w:
        for n in w.node_tree.nodes:
            if n.type == "MIX_SHADER":
                n.inputs["Fac"].default_value = 0.88
            if n.type == "BSDF_DIFFUSE":
                n.inputs["Color"].default_value = (0.024, 0.118, 0.122, 1)

    # -- retunes --------------------------------------------------------------
    # far ridge read as pale cardboard: darken hard and push it blue-grey
    frm = M("mat_rock_far")
    if frm:
        for n in frm.node_tree.nodes:
            if n.type == "MIX" and n.blend_type == "MULTIPLY" and \
                    not n.inputs[0].is_linked:
                for s in n.inputs:
                    if s.type == "RGBA" and not s.is_linked:
                        s.default_value = (0.12, 0.12, 0.12, 1)
            if n.type == "MIX" and n.blend_type == "COLOR":
                km.sock(n, "Factor", "VALUE").default_value = 0.85
                km.sock(n, "B", "RGBA").default_value = (0.33, 0.35, 0.45, 1)
            if n.type == "NORMAL_MAP":
                n.inputs["Strength"].default_value = 0.9
    # lantern glass: the lamps have just come on -- let them blow out
    lg = M("mat_lantern_glass")
    if lg:
        for n in lg.node_tree.nodes:
            if n.type == "EMISSION":
                n.inputs["Strength"].default_value = 90.0
                n.inputs["Color"].default_value = (1.0, 0.58, 0.22, 1)
    # kettle smoke: it is now a hero prop in frame, so make the wisp read
    sm = M("mat_smoke")
    if sm:
        for n in sm.node_tree.nodes:
            if n.type == "MATH" and n.operation == "MULTIPLY" and \
                    not n.inputs[1].is_linked and \
                    abs(n.inputs[1].default_value - 0.55) < 1e-3:
                n.inputs[1].default_value = 1.30
    return made


# --------------------------------------------------------------- cliff surface

CLIFFS = {
    # name: (origin, size, height, seed, facing, ragged)
    "cliff_port":  ((-13.0, -2.0, -2.0), 62, 30, 1.7, 1, 0.0),
    "cliff_stbd":  ((17.5, -2.0, -2.0), 62, 30, 8.3, -1, 0.0),
    "cliff_back":  ((0.0, 0.0, -6.0), 170, 36, 3.1, 1, 0.45),
    "cliff_back2": ((0.0, 0.0, -6.0), 140, 28, 6.7, 1, 0.55),
}


def cliff_local(key, u, v):
    origin, size, height, seed, facing, ragged = CLIFFS[key]
    y = origin[1] + (v - 0.5) * size
    hs = 1.0
    if ragged:
        hs = 1.0 - ragged * (0.5 + 0.5 * noise.noise(
            Vector((y * 0.055, seed * 3.7, 0.0))))
    z = origin[2] + u * height * hs
    n1 = noise.noise(Vector((y * 0.11, z * 0.11, seed)))
    n2 = noise.noise(Vector((y * 0.38, z * 0.38, seed + 5))) * 0.35
    n3 = noise.noise(Vector((y * 1.1, z * 1.1, seed + 9))) * 0.12
    d = (n1 + n2 + n3) * 3.4 + (1.0 - u) * -1.6
    return Vector((origin[0] + facing * d, y, z))


def cliff_world(key, u, v):
    ob = bpy.data.objects.get(key)
    p = cliff_local(key, u, v)
    return (ob.matrix_world @ p) if ob else p


def cliff_out(key, p):
    """Horizontal outward direction of a gorge wall at world point p."""
    return Vector((1.0 if p.x < 2.0 else -1.0, 0.0, 0.0))


def crest_at_x(key, world_x, band=2.0):
    """Top of the ridge near a world x, measured on the EVALUATED mesh.

    far_depth() puts a Z-displace modifier on the back ridges to ragged up the
    skyline, so the analytic surface function is no longer where the geometry
    is. Read the real thing instead, or the far-rim buildings float.
    """
    ob = bpy.data.objects[key]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    best = None
    for vt in me.vertices:
        w = mw @ vt.co
        if abs(w.x - world_x) <= band:
            if best is None or w.z > best.z:
                best = w.copy()
    ev.to_mesh_clear()
    return best


# --------------------------------------------------------------- 1. dusk light

def dusk_light():
    """Sun down on the gorge rim, cooled shadows, lamps just lit."""
    sun = bpy.data.objects["SUN_key"]
    # 21 deg -> 10 deg elevation. Horizontal planes (decks, ramp, water) now
    # receive sin(10)/sin(21) = 48% of the light they did while vertical planes
    # facing the sun get MORE: the frame separates into blazing walls and decks
    # sunk in cool shade, which is what late dusk actually looks like.
    sun.rotation_euler = (math.radians(80.0), 0, math.radians(-26.8))
    sun.data.energy = 9.0
    sun.data.color = (1.0, 0.50, 0.22)
    sun.data.angle = math.radians(3.2)

    fill = bpy.data.objects["FILL_bounce"]
    fill.data.energy = 185
    fill.data.color = (0.13, 0.27, 0.62)      # blue-grey shadow bounce
    fill.data.size = 22.0

    rim = bpy.data.objects["RIM_gorge"]
    rim.data.energy = 780
    rim.data.color = (1.0, 0.52, 0.26)
    rim.location = (-1, 16, 6.5)

    # The dusk sky is mostly a LIGHTING problem, not a backdrop problem.
    # `Generated` Z for a world clamps at 0, so a ramp whose first stop sits at
    # position 0 paints the ENTIRE lower hemisphere with that colour -- v10b had
    # a bright ember there, which is a vast warm ambient dome and is why the
    # frame stayed a bright afternoon no matter how low the sun went. Push the
    # ember into a thin band just above the horizon (which is the only sky the
    # camera actually sees, Z ~ 0.05-0.15), make everything below it dark, and
    # let a deep blue zenith supply the ambient. That is what cools the shadows.
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB").color_ramp
    while len(ramp.elements) > 2:
        ramp.elements.remove(ramp.elements[-1])
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0.115, 0.050, 0.032, 1)     # below the horizon
    ramp.elements[1].position = 1.0
    ramp.elements[1].color = (0.030, 0.045, 0.120, 1)     # zenith
    for pos, col in ((0.115, (0.66, 0.235, 0.075, 1)),    # ember band
                     (0.28, (0.30, 0.145, 0.145, 1)),     # dusty mauve
                     (0.55, (0.085, 0.085, 0.175, 1))):
        e = ramp.elements.new(pos); e.color = col
    next(n for n in nt.nodes if n.type == "BACKGROUND") \
        .inputs["Strength"].default_value = 1.05

    # crank every practical
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.data.type == "POINT":
            if o.name.startswith("kettle_fire"):
                o.data.energy = 95.0
                o.data.color = (1.0, 0.38, 0.10)
            elif "lantern" in o.name:
                o.data.energy = 300.0
                o.data.color = (1.0, 0.58, 0.24)
                o.data.shadow_soft_size = 0.12
    return sun


def lantern_halos(c):
    """Bounded scatter shells so the lamps visibly bloom.

    (World volume would do this too and would also extinguish the sun -- see
    KITLIB_MANIFEST. Small local shells cost nothing and are safe.)"""
    cam = bpy.context.scene.camera
    made = []
    for o in list(bpy.data.objects):
        if o.type != "LIGHT" or o.data.type != "POINT" or "lantern" not in o.name:
            continue
        p = o.matrix_world.translation
        if (p - cam.matrix_world.translation).length > 45:
            continue
        m = Mesh(TAG + "halo_" + o.name)
        try:
            res = bmesh.ops.create_icosphere(m.bm, subdivisions=2, radius=1.0)
        except TypeError:
            res = bmesh.ops.create_icosphere(m.bm, subdivisions=2, diameter=1.0)
        m.stamp(res["verts"], M("mat_glow"),
                Matrix.Translation(p) @ Matrix.Diagonal((0.95, 0.95, 1.05, 1.0)))
        ob = m.finish(c, bevel=0, shade_smooth=True)
        ob.visible_shadow = False
        made.append(ob)
    return made


# ---------------------------------------------------------------- 2. vegetation

def src_clump(name, mat, radius=1.0, n=24, leaf=(0.40, 0.32), squash=0.72):
    m = Mesh(TAG + name)
    for _ in range(n):
        v = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1)))
        if v.length < 1e-4:
            continue
        v.normalize()
        r = radius * R.uniform(0.15, 1.0) ** 0.5
        p = Vector((v.x * r, v.y * r, v.z * r * squash))
        s = R.uniform(0.65, 1.4)
        m.card(p, leaf[0] * s, leaf[1] * s,
               (R.uniform(0, math.pi), R.uniform(0, math.pi),
                R.uniform(0, math.tau)), mat)
    return m.finish(SRC, bevel=0, weld=False)


def src_tree(name, leafmat, h=3.4, canopy=1.5, n=30):
    m = Mesh(TAG + name)
    tb = M("mat_timber")
    m.cyl((0, 0, h * 0.42), 0.075, h * 0.85, tb, seg=6, r2=0.038)
    for _ in range(3):
        a = R.uniform(0, math.tau)
        m.cyl((math.cos(a) * 0.28, math.sin(a) * 0.28, h * 0.80), 0.032,
              0.75, tb, seg=5, rot=(R.uniform(0.5, 0.9) * math.sin(a),
                                   R.uniform(0.5, 0.9) * math.cos(a), 0))
    for _ in range(n):
        v = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 0.7)))
        if v.length < 1e-4:
            continue
        v.normalize()
        r = canopy * R.uniform(0.15, 1.0) ** 0.5
        p = Vector((v.x * r, v.y * r, h + v.z * r * 0.75))
        s = R.uniform(0.7, 1.5)
        m.card(p, 0.36 * s, 0.29 * s,
               (R.uniform(0, math.pi), R.uniform(0, math.pi),
                R.uniform(0, math.tau)), leafmat)
    return m.finish(SRC, bevel=0, weld=False)


def src_creeper(name, leafmat, length=4.2, strands=6):
    m = Mesh(TAG + name)
    vine = M("mat_vine")
    for s in range(strands):
        x0, y0 = R.uniform(-0.55, 0.55), R.uniform(-0.30, 0.30)
        L = length * R.uniform(0.45, 1.0)
        segs = max(3, int(L / 0.42))
        prev = Vector((x0, y0, 0.0))
        for i in range(1, segs + 1):
            t = i / segs
            p = Vector((x0 + math.sin(t * 3.4 + s) * 0.30 * t,
                        y0 + math.cos(t * 2.6 + s) * 0.22 * t,
                        -L * t))
            d = p - prev
            if d.length > 1e-4:
                q = d.to_track_quat("Z", "Y").to_euler()
                m.cyl((prev + p) / 2, 0.026, d.length * 1.15, vine, seg=5,
                      rot=(q.x, q.y, q.z))
            for _ in range(2):
                m.card(p + Vector((R.uniform(-.20, .20), R.uniform(-.20, .20),
                                   R.uniform(-.14, .10))),
                       R.uniform(.11, .21), R.uniform(.09, .18),
                       (R.uniform(0, math.pi), R.uniform(0, math.pi),
                        R.uniform(0, math.tau)), leafmat)
            prev = p
    return m.finish(SRC, bevel=0, weld=False)


def src_tuft(name, mat, blades=16, h=0.34, lean=(0.25, 0.8)):
    """Real tapered blade geometry -- at foreground scale alpha cards read flat."""
    m = Mesh(TAG + name)
    for _ in range(blades):
        a = R.uniform(0, math.tau)
        ln = R.uniform(*lean)
        H = h * R.uniform(0.55, 1.5)
        nx, ny = -math.sin(a), math.cos(a)
        rows = []
        for k in range(5):
            t = k / 4
            bend = ln * t * t
            px, py = math.cos(a) * bend * H, math.sin(a) * bend * H
            pz = H * t * (1 - 0.22 * t)
            w = 0.019 * (1 - t * 0.93)
            rows.append([(px - nx * w, py - ny * w, pz),
                         (px + nx * w, py + ny * w, pz)])
        m.quad_strip(rows, mat)
    return m.finish(SRC, bevel=0, shade_smooth=True, weld=False)


def vegetation(c):
    """Autumn crowns on the rims, creepers off the cliff faces, tufts wherever
    decking meets rock or water. The pilot slice is alive with this; v9 had
    literally none."""
    leaf = M("mat_leaf_autumn")
    leaf_far = M("mat_leaf_autumn_far")
    creep = M("mat_leaf_creeper")

    tree_a = src_tree("src_tree_a", leaf, h=2.8, canopy=1.30, n=90)
    tree_b = src_tree("src_tree_b", leaf, h=3.3, canopy=1.50, n=110)
    # distant crowns: a trunk with sparse cards reads as a DEAD tree at 100u.
    # Far vegetation has to be mass, so the rim gets clumps only.
    clump_a = src_clump("src_clump_a", leaf, radius=0.85, n=46,
                        leaf=(0.34, 0.27))
    clump_b = src_clump("src_clump_b", leaf, radius=0.58, n=28, leaf=(0.26, 0.20))
    clump_far = src_clump("src_clump_far", leaf_far, radius=1.15, n=56,
                          leaf=(0.42, 0.34), squash=0.55)
    creep_a = src_creeper("src_creeper_a", creep, length=4.6, strands=7)
    creep_b = src_creeper("src_creeper_b", creep, length=2.8, strands=5)
    tuft_g = src_tuft("src_tuft_grass", M("mat_grass"), blades=16, h=0.32)
    tuft_f = src_tuft("src_tuft_fern", M("mat_fern"), blades=11, h=0.52,
                      lean=(0.6, 1.15))

    made = []

    # -- creepers + ledge growth on the near cliff faces ----------------------
    # cliff_stbd fills the right of frame at y 12..22, z 1..11 (ray-mapped).
    for (y, z, src) in [(13.2, 9.4, creep_a), (15.0, 10.6, creep_a),
                        (16.4, 7.6, creep_b), (18.0, 10.2, creep_a),
                        (19.6, 8.4, creep_b), (21.0, 10.8, creep_a),
                        (14.2, 5.2, creep_b), (17.2, 4.4, creep_b),
                        (20.2, 5.6, creep_b)]:
        v = (y + 2.0) / 62 + 0.5
        u = (z + 2.0) / 30
        p = cliff_world("cliff_stbd", u, v)
        made.append(place(src, p + cliff_out("cliff_stbd", p) * 0.30,
                          rot=(0, 0, R.uniform(0, 6.2)),
                          c=c, scale=R.uniform(0.85, 1.35)))
    for (y, z) in [(12.6, 11.4), (16.0, 12.0), (19.4, 11.6), (21.6, 12.4),
                   (14.8, 6.6), (18.6, 6.0)]:
        v = (y + 2.0) / 62 + 0.5
        u = (z + 2.0) / 30
        p = cliff_world("cliff_stbd", u, v)
        made.append(place(R.choice([clump_a, clump_b]),
                          p + cliff_out("cliff_stbd", p) * 0.55,
                          rot=(0, 0, R.uniform(0, 6.2)), c=c,
                          scale=R.uniform(0.8, 1.4)))
    # cliff_port shows as a sliver at the left edge, y 23..27, z 0..11
    for (y, z, src) in [(23.6, 8.0, creep_a), (25.2, 9.6, creep_a),
                        (26.4, 6.4, creep_b)]:
        v = (y + 2.0) / 62 + 0.5
        u = (z + 2.0) / 30
        p = cliff_world("cliff_port", u, v)
        made.append(place(src, p + cliff_out("cliff_port", p) * 0.30,
                          rot=(0, 0, R.uniform(0, 6.2)),
                          c=c, scale=R.uniform(0.9, 1.3)))
    for (y, z) in [(24.4, 10.6), (26.0, 11.4), (23.0, 5.4)]:
        v = (y + 2.0) / 62 + 0.5
        u = (z + 2.0) / 30
        p = cliff_world("cliff_port", u, v)
        made.append(place(R.choice([clump_a, clump_b]),
                          p + cliff_out("cliff_port", p) * 0.55,
                          rot=(0, 0, R.uniform(0, 6.2)), c=c,
                          scale=R.uniform(0.9, 1.4)))

    # -- autumn crown on the mid ridge behind the lock ------------------------
    for x in (-16, -9.5, -3.0, 4.0, 11.5, 19.0, 27.0, 34.0):
        p = crest_at_x("cliff_back2", x)
        if p is None:
            continue
        made.append(place(clump_far,
                          (p.x, p.y - R.uniform(0.4, 2.4), p.z - 0.7),
                          rot=(0, 0, R.uniform(0, 6.2)), c=c,
                          scale=R.uniform(0.75, 1.25)))
    for x in (22.0, 30.0, 38.0):
        p = crest_at_x("cliff_back", x)
        if p is None:
            continue
        made.append(place(clump_far, (p.x, p.y - 1.5, p.z - 0.9),
                          rot=(0, 0, R.uniform(0, 6.2)), c=c,
                          scale=R.uniform(1.0, 1.7)))

    # -- trees on the lock abutments / upper deck -----------------------------
    for (x, y, z) in [(-8.6, 25.6, 6.2), (9.0, 25.4, 6.2)]:
        made.append(place(tree_b, (x, y, z), rot=(0, 0, R.uniform(0, 6.2)),
                          c=c, scale=R.uniform(0.9, 1.2)))
        for _ in range(9):
            made.append(place(tuft_g, (x + R.uniform(-2.2, 2.2),
                                       y + R.uniform(-1.0, 1.0), z),
                              rot=(0, 0, R.uniform(0, 6.2)), c=c,
                              scale=R.uniform(0.8, 1.6)))

    # -- tufts where decking meets rock / water -------------------------------
    edge = []
    for i in range(14):                      # both lips of the slipway
        y = -15.2 + i * 0.62
        z = 3.13 + (-3.6) * ((y + 15.0) / 18.0)
        for sx in (-1, 1):
            if R.random() < 0.62:
                edge.append((sx * (4.24 + R.uniform(-0.10, 0.10)),
                             y + R.uniform(-0.2, 0.2), z + 0.02))
    for i in range(16):                      # front lip of the yard deck
        edge.append((R.uniform(-11.0, -4.3), -19.0 + R.uniform(-0.35, 0.35), 3.14))
        edge.append((R.uniform(4.3, 11.5), -19.0 + R.uniform(-0.35, 0.35), 3.14))
    for i in range(14):                      # against the shed wall
        edge.append((R.uniform(5.6, 6.4), R.uniform(-14.5, -7.6), 3.14))
    for (x, y, z) in edge:
        made.append(place(R.choice([tuft_g, tuft_g, tuft_f]), (x, y, z),
                          rot=(0, 0, R.uniform(0, 6.2)), c=c,
                          scale=R.uniform(0.7, 1.5)))
    # weed at the waterline of the pilings
    for (x, y) in [(-6.6, 1.5), (-6.2, 6.0), (-5.6, 11.0), (7.4, 0.5),
                   (7.9, 5.5), (8.3, 11.5)]:
        for _ in range(3):
            a = R.uniform(0, math.tau)
            made.append(place(tuft_f, (x + math.cos(a) * 0.22,
                                       y + math.sin(a) * 0.22, 0.55),
                              rot=(0, 0, R.uniform(0, 6.2)), c=c,
                              scale=R.uniform(0.8, 1.3)))
    return made


# --------------------------------------------------- 3. colour / structures

def cabin(m, ox, oy, oz, W, D, H, wall, roof, trim, pitch=1.15,
          door=None, door_at=None, shutter=None):
    """Small plank cabin: cladding, corner posts, gable roof in shingle courses."""
    nb = max(2, int(D / 0.30))
    for sgn in (-1, 1):
        for i in range(nb):
            y = oy - D / 2 + D * (i + 0.5) / nb
            m.box((ox + sgn * W / 2, y, oz + H / 2),
                  (0.055, D / nb / 2 - 0.008, H / 2), wall, jitter=0.01)
    nbx = max(2, int(W / 0.30))
    for i in range(nbx):
        x = ox - W / 2 + W * (i + 0.5) / nbx
        for sgn in (-1, 1):
            m.box((x, oy + sgn * D / 2, oz + H / 2),
                  (W / nbx / 2 - 0.008, 0.055, H / 2), wall, jitter=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((ox + sx * W / 2, oy + sy * D / 2, oz + H / 2),
                  (0.10, 0.10, H / 2), trim)
    for sy in (-1, 1):
        m.box((ox, oy + sy * D / 2, oz + H + 0.03), (W / 2 + 0.1, 0.09, 0.10), trim)
    # gable roof
    for side in (1, -1):
        L = math.hypot(W / 2 + 0.40, pitch)
        ang = math.atan2(pitch, W / 2 + 0.40)
        cx = ox + side * (W / 4 + 0.20)
        cz = oz + H + pitch / 2
        m.box((cx, oy, cz), (L / 2, D / 2 + 0.42, 0.075), roof,
              rot=(0, -side * ang, 0))
        rows = 7
        for r in range(rows):
            f = (r + 0.5) / rows
            px = ox + side * (W / 2 + 0.40) * (1 - f)
            pz = oz + H + pitch * f
            # half-width 0.85 of the course STEP -> 70% overlap, i.e. a
            # continuous weathered surface rather than a rack of slats.
            m.box((px, oy, pz + 0.045), ((L / rows) * 1.25, D / 2 + 0.46, 0.022),
                  roof, rot=(0, -side * ang, 0), jitter=0.003)
    m.box((ox, oy, oz + H + pitch + 0.03), (0.12, D / 2 + 0.46, 0.085), trim)
    # door + shutters on the requested face
    if door and door_at:
        dx, dy, ang = door_at
        m.box((dx, dy, oz + 1.05), (0.50, 0.055, 1.05), door, rot=(0, 0, ang))
        for zz in (0.35, 1.75):
            m.box((dx, dy - 0.03, oz + zz), (0.52, 0.035, 0.055), trim,
                  rot=(0, 0, ang))
    if shutter:
        for sy in (-1, 1):
            m.box((ox - W / 2 - 0.03, oy + sy * D * 0.24, oz + H * 0.62),
                  (0.03, 0.42, 0.40), shutter)
            m.box((ox - W / 2 - 0.07, oy + sy * D * 0.24, oz + H * 0.62),
                  (0.02, 0.44, 0.05), trim)


def stilt_bay(m, x0, x1, y0, y1, deck_z, mat_deck_, tb, water_z=0.2):
    """Planked platform on braced piles -- how everything in Dellhollow stands."""
    n = max(1, int((x1 - x0) / 0.28))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        m.box((x, (y0 + y1) / 2, deck_z), ((x1 - x0) / n / 2 - 0.008,
                                           (y1 - y0) / 2, 0.06), mat_deck_,
              jitter=0.006)
    for yy in (y0 + 0.5, y1 - 0.5):
        m.box(((x0 + x1) / 2, yy, deck_z - 0.20), ((x1 - x0) / 2, 0.11, 0.14), tb)
    for sx in (x0 + 0.35, x1 - 0.35):
        for sy in (y0 + 0.45, y1 - 0.45):
            h = deck_z - water_z + 1.6
            m.box((sx, sy, deck_z - 0.32 - h / 2), (0.11, 0.11, h / 2), tb,
                  jitter=0.015)
        m.box((sx, (y0 + y1) / 2, deck_z - 1.3),
              (0.07, (y1 - y0) / 2, 0.07), tb, rot=(0.30, 0, 0))
        m.box((sx, (y0 + y1) / 2, deck_z - 1.3),
              (0.07, (y1 - y0) / 2, 0.07), tb, rot=(-0.30, 0, 0))


def colour_structures(c, kit):
    """Break the brown monopoly.

    v9 is a brown scene with one green shed. The style block asks for oxblood
    red, moss green and faded blue over brown scaffold. This puts an oxblood
    chandlery across the water on the LEFT (directly opposing the green shed on
    the right) and a low mossy-roofed net loft under the starboard cliff, whose
    roof plane sits below camera height so the moss actually reads.
    """
    red, blue, green = M("mat_paint_red"), M("mat_paint_blue"), M("mat_wallwood")
    moss_roof, tb = M("mat_shingle_mossy"), M("mat_timber")
    dk = M("mat_deck")
    made = []

    # -- oxblood chandlery, port side, mid-distance ---------------------------
    m = Mesh(TAG + "chandlery")
    ox, oy, dz = -6.4, 11.4, 2.35
    stilt_bay(m, ox - 3.1, ox + 2.6, oy - 3.4, oy + 3.4, dz, dk, tb)
    cabin(m, ox, oy, dz + 0.06, 4.0, 4.6, 2.45, red, moss_roof, tb, pitch=1.25,
          door=blue, door_at=(ox - 2.05, oy - 0.6, math.pi / 2), shutter=blue)
    # jetty stub + rail towards the camera
    stilt_bay(m, ox - 0.6, ox + 2.6, oy - 6.2, oy - 3.4, dz - 0.55, dk, tb)
    for i in range(6):
        m.box((ox - 0.6 + i * 0.64, oy - 6.2, dz - 0.05), (0.055, 0.055, 0.5), tb,
              jitter=0.03)
    m.box((ox + 1.0, oy - 6.2, dz + 0.42), (1.7, 0.05, 0.05), tb)
    # lantern bracket
    m.box((ox - 2.2, oy - 1.8, dz + 2.95), (0.34, 0.05, 0.05), tb)
    made.append(m.finish(c, bevel=0.01))

    # -- mossy-roofed net loft, starboard, low enough to show its roof --------
    m = Mesh(TAG + "netloft")
    ox2, oy2, dz2 = 12.6, 16.4, 1.95
    stilt_bay(m, ox2 - 2.9, ox2 + 3.0, oy2 - 3.0, oy2 + 3.0, dz2, dk, tb)
    cabin(m, ox2, oy2, dz2 + 0.06, 3.6, 4.2, 1.95, green, moss_roof, tb,
          pitch=1.15, door=red, door_at=(ox2 - 1.85, oy2 - 0.5, math.pi / 2))
    # drying racks: horizontal poles with hanging nets suggested by battens
    for i in range(4):
        m.box((ox2 - 2.6, oy2 - 2.2 + i * 1.4, dz2 + 1.35), (0.05, 0.05, 1.3), tb,
              jitter=0.02)
    m.box((ox2 - 2.6, oy2, dz2 + 2.6), (0.05, 2.6, 0.05), tb)
    made.append(m.finish(c, bevel=0.01))

    # -- mossy lean-to over the shed bench (right of frame, roof plane visible)
    m = Mesh(TAG + "shed_leanto")
    hi_x, lo_x, hi_z, lo_z = 5.94, 4.35, 5.32, 4.58
    ang = math.atan2(hi_z - lo_z, hi_x - lo_x)
    L = math.hypot(hi_x - lo_x, hi_z - lo_z)
    y0, y1 = -15.8, -6.8
    m.box(((hi_x + lo_x) / 2, (y0 + y1) / 2, (hi_z + lo_z) / 2),
          (L / 2 + 0.15, (y1 - y0) / 2, 0.075), moss_roof, rot=(0, ang, 0))
    for r in range(6):
        f = (r + 0.5) / 6
        px = lo_x + (hi_x - lo_x) * f
        pz = lo_z + (hi_z - lo_z) * f
        m.box((px, (y0 + y1) / 2, pz + 0.048), ((L / 6) * 1.30,
                                                (y1 - y0) / 2 + 0.10, 0.022),
              moss_roof, rot=(0, ang, 0), jitter=0.004)
    for yy in (y0 + 0.4, (y0 + y1) / 2, y1 - 0.4):
        m.box((lo_x + 0.12, yy, (lo_z + 3.13) / 2), (0.07, 0.07,
                                                     (lo_z - 3.13) / 2), tb,
              jitter=0.02)
    # a strip of oxblood barge-board so red reads on the right too
    m.box((lo_x + 0.02, (y0 + y1) / 2, lo_z - 0.13), (0.06, (y1 - y0) / 2 + 0.10,
                                                      0.13), red)
    made.append(m.finish(c, bevel=0.008))

    # -- painted timber variety on the near deck ------------------------------
    m = Mesh(TAG + "paintwork")
    # blue-painted shutter panel and red door frame on the near shed corner
    m.box((5.86, -6.6, 4.30), (0.05, 0.62, 0.60), blue)
    m.box((5.86, -6.6, 4.98), (0.055, 0.66, 0.06), red)
    # bunting-post pair with a red-painted cap (motif from the master ref)
    for (x, y) in [(-4.30, -10.2), (4.30, -9.0)]:
        m.box((x, y, 4.05), (0.075, 0.075, 0.92), tb, jitter=0.02)
        m.box((x, y, 4.99), (0.11, 0.11, 0.055), red)
    made.append(m.finish(c, bevel=0.008))

    # -- moored cargo barges: the two big empty water plates in v10 --------
    # (ray map: open water at x -6..1 y 1..10, and x 9..10 y -1, both dead.)
    # Flat barges with crates and pumpkins are a master-ref motif and they are
    # what a lock pool full of trade traffic actually looks like.
    for tag, (bx, by, rz, ncrate) in {
            "barge_port": (-3.6, 5.2, 0.22, 3),
            "barge_stbd": (8.6, -1.4, -0.34, 2),
            "barge_mid": (4.3, 13.2, 0.14, 3)}.items():
        m = Mesh(TAG + tag)
        L, W = 5.0, 1.9
        for i in range(int(W * 2 / 0.28)):
            x = -W + (i + 0.5) * 0.28
            m.box((x, 0, 0.30), (0.135, L / 2, 0.055), dk, jitter=0.01)
        for sy in (-1, 1):
            m.box((0, sy * L / 2, 0.42), (W, 0.09, 0.20), tb)
        for sx in (-1, 1):
            m.box((sx * W, 0, 0.44), (0.09, L / 2, 0.22), tb)
            m.box((sx * W * 0.92, 0, 0.16), (0.07, L / 2 - 0.3, 0.16),
                  M("mat_mosswood") or tb)
        for k in range(ncrate):
            m.box((R.uniform(-0.8, 0.8), -1.2 + k * 1.1, 0.68),
                  (0.34, 0.34, 0.32), R.choice([dk, red, blue]),
                  rot=(0, 0, R.uniform(-0.4, 0.4)))
        for k in range(7):     # pumpkins, straight off the master ref
            m.cyl((R.uniform(-1.1, 1.1), R.uniform(0.8, 2.0), 0.57), 0.21, 0.30,
                  M("mat_pumpkin"), seg=10, rot=(math.pi / 2, 0, 0))
        m.box((-W * 0.5, L * 0.36, 0.95), (0.055, 0.055, 0.55), tb)
        ob = m.finish(c, bevel=0.01)
        ob.location = (bx, by, 0.0)
        ob.rotation_euler = (0, 0, rz)
        made.append(ob)
        if tag == "barge_port":
            made.append(place_lantern(
                kit, (bx - W * 0.5 - 0.1, by + L * 0.36, 1.42), c, energy=210))

    # -- festival bunting: the identity motif of the master ref, and the only
    #    place in frame where saturated colour appears at full strength ------
    m = Mesh(TAG + "bunting")
    a0, a1 = Vector((-4.85, -8.6, 6.05)), Vector((5.60, -6.9, 6.35))
    flags = [M("mat_flag_red"), M("mat_flag_ochre"), M("mat_flag_green"),
             M("mat_flag_blue")]
    N = 26
    def sag(t):
        p = a0.lerp(a1, t)
        p.z -= 1.05 * math.sin(math.pi * t)
        return p
    prev = sag(0.0)
    for i in range(1, N + 1):
        q = sag(i / N)
        d = q - prev
        rot = d.to_track_quat("Z", "Y").to_euler()
        m.cyl((prev + q) / 2, 0.018, d.length * 1.1, tb, seg=5,
              rot=(rot.x, rot.y, rot.z))
        if i < N:
            fm = flags[i % 4]
            m.box((q.x, q.y, q.z - 0.20), (0.005, 0.115, 0.20), fm,
                  rot=(R.uniform(-0.25, 0.25), 0, R.uniform(-0.3, 0.3)))
        prev = q
    made.append(m.finish(c, bevel=0))

    # -- oxblood where the sun still lands: the foreground is the only sunlit
    #    plane left at a 10deg key, so the saturated red has to appear there --
    m = Mesh(TAG + "redcrates")
    for (x, y, rz, h) in [(1.95, -16.35, 0.30, 0.36), (2.25, -15.45, -0.5, 0.30),
                          (-1.30, -17.10, 0.9, 0.34)]:
        z = 3.16
        m.box((x, y, z + h), (0.42, 0.42, h), red, rot=(0, 0, rz))
        for sx in (-1, 1):
            m.box((x + sx * 0.42 * math.cos(rz), y + sx * 0.42 * math.sin(rz),
                   z + h), (0.05, 0.44, h), tb, rot=(0, 0, rz))
        m.box((x, y, z + h * 2), (0.44, 0.44, 0.04), tb, rot=(0, 0, rz))
    made.append(m.finish(c, bevel=0.01))

    # practicals on the new structures + on the lock walkway, which was the
    # one big dead slab left in the centre of frame
    for (x, y, z, w) in [(-6.4, 8.75, 4.55, 380), (-8.6, 9.6, 5.30, 300),
                         (10.6, 14.9, 3.60, 150),
                         (-6.2, 26.4, 5.55, 260), (6.2, 26.4, 5.55, 260)]:
        made.append(place_lantern(kit, (x, y, z), c, energy=w))
    return made


def place_lantern(kit, loc, c, energy=340.0):
    src = kit["kit_lantern_hanging"]
    o = src.copy()
    o.name = TAG + "lantern"
    o.location = loc
    c.objects.link(o)
    for ch in src.children:
        lc = ch.copy()
        lc.name = TAG + "lantern_light"
        lc.data = ch.data.copy()
        lc.data.energy = energy
        lc.data.color = (1.0, 0.58, 0.24)
        c.objects.link(lc)
        lc.parent = o
        lc.matrix_parent_inverse = o.matrix_world.inverted()
    return o


# ------------------------------------------------------------ 4. foreground

def ramp_z(y):
    """Height of the slipway deck at a given y (ramp runs y -15 -> +3)."""
    return 3.1 + (-3.6) * ((y + 15.0) / 18.0)


def foreground(c, kit):
    """The slipway ramp centre-front was a barren plank field. Fill it with the
    work that would actually be happening, and bring the pitch kettle -- which
    the town map puts in exactly this shot -- into frame."""
    dk, tb, fresh = M("mat_deck"), M("mat_timber"), M("mat_freshwood")
    tar, ir = M("mat_tar"), M("mat_iron")
    made = []

    # -- close the hole between the yard deck and the ramp head ---------------
    # rays through the bottom-right of frame were passing UNDER the slipway and
    # out onto open water. Deck it, which also gives the props somewhere to sit.
    m = Mesh(TAG + "apron")
    n = int(8.44 / 0.27)
    for i in range(n):
        x = -4.22 + 8.44 * (i + 0.5) / n
        m.box((x, -17.05, 3.06), (8.44 / n / 2 - 0.008, 2.05, 0.07), dk,
              jitter=0.006)
    for yy in (-18.8, -17.0, -15.3):
        m.box((0, yy, 2.90), (4.3, 0.13, 0.15), tb)
    m.box((0, -15.05, 2.82), (4.3, 0.09, 0.28), tb)      # skirt at the ramp head
    made.append(m.finish(c, bevel=0.01))

    # -- pitch kettle moves into frame, lower left ---------------------------
    kx, ky = -2.42, -11.85
    kz = ramp_z(ky)
    o = bpy.data.objects.get("pitch_kettle")
    if o:
        o.location = (kx + 6.4, ky + 12.6, kz - 3.13)
    f = bpy.data.objects.get("kettle_fire")
    if f:
        # v10 put this at +0.30, which is inside the kettle casting -- the fire
        # lit the underside of its own pot. Drop it into the hearth mouth.
        # The hearth ring is nearly solid and the kettle caps it, so a light
        # inside lights nothing. Put it at the stoking mouth on the camera side.
        f.location = (kx, ky - 0.60, kz + 0.34)
        f.data.energy = 260.0
        f.data.shadow_soft_size = 0.3
    m = Mesh(TAG + "embers")
    for _ in range(14):
        a = R.uniform(-2.5, -0.65); rr = R.uniform(0.30, 0.60)
        m.box((kx + math.cos(a) * rr, ky + math.sin(a) * rr, kz + 0.17),
              (R.uniform(0.05, 0.11), R.uniform(0.04, 0.09), 0.045),
              M("mat_embers"), rot=(0, 0, R.uniform(0, 3.1)))
    for _ in range(6):                      # flame tongues licking the pot
        a = R.uniform(-2.3, -0.85)
        m.box((kx + math.cos(a) * 0.52, ky + math.sin(a) * 0.52,
               kz + 0.30 + R.uniform(0, 0.12)),
              (0.035, 0.035, R.uniform(0.10, 0.20)), M("mat_embers"),
              rot=(R.uniform(-0.3, 0.3), R.uniform(-0.3, 0.3), 0))
    # split logs stacked ready by the hearth
    for k in range(5):
        m.cyl((kx + 1.35 + R.uniform(-0.06, 0.06), ky - 1.05,
               ramp_z(ky - 1.05) + 0.09 + k * 0.15), 0.075, 0.85, tb, seg=8,
              rot=(0, math.pi / 2, R.uniform(-0.2, 0.2)))
    # v11a: the pot was a smooth dark drum sitting dead centre. Bands, a bail
    # and a stirring paddle are what make it read as a pitch kettle.
    ir = M("mat_iron")
    for zz in (0.44, 0.70):
        m.cyl((kx, ky, kz + zz), 0.635 - (zz - 0.44) * 0.18, 0.055, ir, seg=20)
    for sx in (-1, 1):
        m.box((kx + sx * 0.60, ky, kz + 0.86), (0.05, 0.05, 0.12), ir)
    for k in range(11):                     # bail hoop over the pot
        a0 = math.pi * k / 11
        a1 = math.pi * (k + 1) / 11
        p0 = Vector((kx + math.cos(a0) * 0.60, ky, kz + 0.94 + math.sin(a0) * 0.44))
        p1 = Vector((kx + math.cos(a1) * 0.60, ky, kz + 0.94 + math.sin(a1) * 0.44))
        d = p1 - p0
        q = d.to_track_quat("Z", "Y").to_euler()
        m.cyl((p0 + p1) / 2, 0.028, d.length * 1.2, ir, seg=6,
              rot=(q.x, q.y, q.z))
    m.cyl((kx + 0.34, ky - 0.30, kz + 1.34), 0.045, 1.7, tb, seg=8,
          rot=(0.52, 0.30, 0))            # stirring paddle standing in the tar
    m.box((kx + 0.72, ky - 0.72, kz + 2.02), (0.085, 0.02, 0.24), tb,
          rot=(0.52, 0.30, 0))
    made.append(m.finish(c, bevel=0.006))
    # The original smoke was a 3x3x4.8 box, invisible off-frame at v9. In frame
    # it renders as a literal slab. Replace it with a narrow leaning plume.
    old = bpy.data.objects.get("kettle_smoke")
    if old:
        old.hide_render = True
        old.hide_viewport = True
    # A ray-map of v10 showed this plume covering columns 4-9 of rows 0-6 --
    # it was quietly hazing the entire centre of frame, which is why the lock
    # and the mid water went flat. A pitch kettle makes a WISP.
    m = Mesh(TAG + "kettle_smoke")
    for i in range(5):
        t = i / 4
        w = 0.14 + t * 0.30
        m.box((kx + t * t * 0.75, ky + t * 0.30, kz + 0.95 + t * 1.55),
              (w, w, 0.24), M("mat_smoke"), rot=(0, 0, t * 0.6))
    sm = m.finish(c, bevel=0)
    sm.visible_shadow = False
    made.append(sm)

    # -- sawhorse pair with a fresh plank across it --------------------------
    m = Mesh(TAG + "foreclutter")
    for yy in (-14.7, -12.9):
        zz = ramp_z(yy)
        m.box((0.95, yy, zz + 0.62), (0.60, 0.07, 0.07), tb)
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.box((0.95 + sx * 0.48, yy + sy * 0.16, zz + 0.31),
                      (0.05, 0.05, 0.31), tb, rot=(sy * 0.16, sx * 0.22, 0))
    m.box((0.95, -13.8, ramp_z(-13.8) + 0.73), (0.42, 1.30, 0.045), fresh,
          rot=(0.02, 0.0, 0.03))
    m.box((1.42, -13.5, ramp_z(-13.5) + 0.73), (0.30, 1.05, 0.038), fresh,
          rot=(0.01, 0.0, -0.02))
    # a two-man saw leaning on the horse
    m.box((0.36, -14.3, ramp_z(-14.3) + 0.55), (0.02, 0.55, 0.16), ir,
          rot=(0.55, 0, 0.2))
    # wood shavings and offcuts around the sawing
    for _ in range(34):
        x = R.uniform(-0.6, 2.4); y = R.uniform(-15.4, -12.2)
        m.box((x, y, ramp_z(y) + 0.02),
              (R.uniform(0.03, 0.09), R.uniform(0.02, 0.06), 0.008), fresh,
              rot=(R.uniform(-0.4, 0.4), R.uniform(-0.4, 0.4),
                   R.uniform(0, 3.1)))
    for _ in range(9):
        x = R.uniform(-3.2, 2.6); y = R.uniform(-16.6, -12.0)
        m.box((x, y, ramp_z(y) + 0.03),
              (R.uniform(0.05, 0.13), R.uniform(0.20, 0.46), 0.024), fresh,
              rot=(0, 0, R.uniform(0, 3.1)))
    # tar bucket, brush and a black splash beside the kettle
    m.cyl((kx + 1.05, ky - 0.55, ramp_z(ky - 0.55) + 0.16), 0.20, 0.32, ir,
          seg=12, r2=0.17)
    m.cyl((kx + 1.05, ky - 0.55, ramp_z(ky - 0.55) + 0.31), 0.165, 0.02, tar,
          seg=12)
    m.box((kx + 0.72, ky - 0.95, ramp_z(ky - 0.95) + 0.26), (0.03, 0.03, 0.26),
          tb, rot=(0.3, 0.5, 0))
    for _ in range(7):
        x = kx + R.uniform(-0.9, 1.5); y = ky + R.uniform(-1.2, 0.9)
        m.cyl((x, y, ramp_z(y) + 0.012), R.uniform(0.07, 0.19), 0.012, tar,
              seg=9)
    # a hauling hawser running up the ramp to the hull
    prev = Vector((-2.55, -16.4, ramp_z(-16.4) + 0.05))
    for i in range(1, 16):
        t = i / 15
        y = -16.4 + t * 6.0
        p = Vector((-2.55 + math.sin(t * 3.0) * 0.55 + t * 1.9, y,
                    ramp_z(y) + 0.05))
        d = p - prev
        if d.length > 1e-4:
            q = d.to_track_quat("Z", "Y").to_euler()
            m.cyl((prev + p) / 2, 0.045, d.length * 1.1, M("mat_rope"), seg=7,
                  rot=(q.x, q.y, q.z))
        prev = p
    made.append(m.finish(c, bevel=0.008))

    # -- barrels camera-left, rope coils, buckets -----------------------------
    for (x, y, rz) in [(-4.15, -14.35, 0.4), (-3.72, -13.25, 1.2)]:
        made.append(place(kit["kit_barrel"],
                          (x, y, ramp_z(y) if y > -15 else 3.16),
                          rot=(0, 0, rz), c=c, jitter=0.05))
    for (x, y) in [(-2.30, -15.55), (0.30, -16.30), (2.15, -12.55),
                   (-1.10, -13.60)]:
        z = ramp_z(y) if y > -15 else 3.16
        made.append(place(kit["kit_rope_coil"], (x, y, z + 0.02), c=c,
                          jitter=0.14))
    for (x, y) in [(-1.85, -16.85), (1.65, -15.35)]:
        z = ramp_z(y) if y > -15 else 3.16
        made.append(place(kit["kit_bucket"], (x, y, z + 0.02), c=c, jitter=0.1))
    made.append(place(kit["kit_crate"], (2.45, -16.55, 3.16), rot=(0, 0, 0.5),
                      c=c, jitter=0.04))

    # -- OFF-FRAME shadow casters --------------------------------------------
    # The key travels up-gorge, so most casters hide their own shadow behind
    # themselves and the deck came back evenly lit. Standing gear just outside
    # the left edge of frame throws its ~17u shadows straight across the
    # slipway, which is where the raking rhythm the critique asked for comes
    # from -- and it costs nothing in the frame itself.
    # The key travels toward (0.45, 0.89) on the ground and a 5u post at 10deg
    # elevation throws a 26u shadow, so the casters that stripe the FOREGROUND
    # ramp have to stand behind and left of the camera itself.
    m = Mesh(TAG + "shadowgear")
    for (x, y, h) in [(-5.9, -21.4, 4.4), (-7.1, -21.9, 5.6), (-8.4, -21.3, 3.9),
                      (-9.6, -21.8, 5.1), (-10.8, -21.2, 4.2),
                      (-6.6, -23.6, 4.8), (-8.9, -23.9, 3.6)]:
        m.box((x, y, 3.13 + h / 2), (0.11, 0.11, h / 2), tb, jitter=0.02)
        m.box((x, y, 3.13 + h - 0.20), (0.10, 0.70, 0.10), tb)
    # a drying rack whose rails stripe the ramp
    for k in range(6):
        m.box((-8.4, -22.2, 3.13 + 1.5 + k * 0.55), (2.6, 0.06, 0.06), tb,
              jitter=0.02)
    # and a second bank further left for a denser rhythm
    for (x, y, h) in [(-12.4, -20.4, 4.9), (-13.6, -19.2, 5.8)]:
        m.box((x, y, 3.13 + h / 2), (0.12, 0.12, h / 2), tb, jitter=0.02)
    made.append(m.finish(c, bevel=0.008))

    # -- gallows lantern over the kettle: the warm pool that says 'dusk' ------
    m = Mesh(TAG + "gallows")
    gx, gy = -3.95, -11.30
    gz = ramp_z(gy)
    m.box((gx, gy, gz + 1.55), (0.085, 0.085, 1.55), tb, jitter=0.01)
    m.box((gx + 0.50, gy, gz + 3.02), (0.50, 0.055, 0.055), tb)
    m.box((gx + 0.18, gy, gz + 2.76), (0.30, 0.045, 0.045), tb,
          rot=(0, math.radians(42), 0))
    made.append(m.finish(c, bevel=0.008))
    made.append(place_lantern(kit, (gx + 0.92, gy, gz + 2.82), c, energy=320))
    return made


# ------------------------------------------------------------- 5. far depth

def far_depth(c):
    """The far ridge read as pale cardboard. Darken it (done in materials()),
    roughen its silhouette, stack bounded haze between the depth planes, and
    put a hint of far-side town on the rim the way master ref 6b does."""
    made = []
    tb = M("mat_timber")

    # -- extra relief on the back ridges so the silhouette is not a smooth arc
    # Displace along GLOBAL Z, not along normals: the ridges are near-vertical
    # walls, so a normal displace only pushes them in and out and leaves the
    # skyline exactly as smooth as it was. Z is what breaks the silhouette.
    for nm, size, strength in (("cliff_back", 24.0, 5.0),
                               ("cliff_back2", 17.0, 4.0)):
        ob = bpy.data.objects.get(nm)
        if not ob:
            continue
        for md in list(ob.modifiers):
            if md.name == "far_relief":
                ob.modifiers.remove(md)
        tex = bpy.data.textures.get("tex_far_relief_" + nm) or \
            bpy.data.textures.new("tex_far_relief_" + nm, "CLOUDS")
        tex.noise_scale = size
        tex.noise_depth = 4
        md = ob.modifiers.new("far_relief", "DISPLACE")
        md.texture = tex
        md.strength = strength
        md.mid_level = 0.5
        md.direction = "Z"
        md.texture_coords = "GLOBAL"
    bpy.context.view_layer.update()

    # -- bounded haze layers between mid and far ------------------------------
    # (bounded, per KITLIB_MANIFEST: a world volume extinguishes the sun.)
    for nm, ctr, half, mat in (
            ("haze_mid", (0, 44, 8), (75, 12, 26), "mat_haze_mid"),
            ("haze_far", (0, 68, 10), (95, 12, 30), "mat_haze_far"),
            ("haze_rim", (4, 106, 12), (130, 22, 34), "mat_haze_rim")):
        m = Mesh(TAG + nm)
        m.box(ctr, half, M(mat))
        ob = m.finish(c, bevel=0)
        ob.visible_shadow = False
        made.append(ob)

    # -- far-side town silhouetted on the rim (hazy shapes only) --------------
    # v10b built these at full village scale and they read as white deckchairs
    # on the skyline. At 105u a 1.7u character is 19px: these are hints.
    sil = M("mat_silhouette")
    m = Mesh(TAG + "far_town")
    for (wx, w, d, h, tower) in [(-11.0, 1.9, 1.5, 1.5, True),
                                 (2.5, 2.3, 1.8, 1.7, False),
                                 (16.0, 1.7, 1.4, 1.4, True),
                                 (30.0, 2.1, 1.7, 1.6, False)]:
        p = crest_at_x("cliff_back2", wx)
        if p is None:
            continue
        bx, by, bz = p.x, p.y - 1.2, p.z - 0.9
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.box((bx + sx * w * 0.42, by + sy * d * 0.42, bz - 0.85),
                      (0.10, 0.10, 0.95), sil, rot=(0, sx * 0.05, 0))
        m.box((bx, by, bz - 0.5), (w * 0.46, d * 0.46, 0.07), sil)
        m.box((bx, by, bz + h / 2), (w / 2, d / 2, h / 2), sil)
        for side in (1, -1):
            ang = math.atan2(0.62, w / 2 + 0.2)
            L = math.hypot(w / 2 + 0.2, 0.62)
            m.box((bx + side * (w / 4 + 0.1), by, bz + h + 0.31),
                  (L / 2, d / 2 + 0.2, 0.06), sil, rot=(0, -side * ang, 0))
        if tower:
            m.box((bx + w * 0.85, by + 0.2, bz + 1.05), (0.30, 0.30, 1.35), sil)
            m.box((bx + w * 0.85, by + 0.2, bz + 2.45), (0.42, 0.42, 0.07), sil)
    made.append(m.finish(c, bevel=0))
    return made


# ------------------------------------------------------------------ assembly

SRC = None


def apply_all():
    global SRC
    # re-seed: the pass must be deterministic even when called twice in one
    # process, or a rerun quietly reshuffles which foliage source lands where.
    R.seed(90210)
    purge()
    SRC = coll("V10_SRC", exclude=True)
    c = coll("PROBE_V10")
    materials()
    kit = {n: bpy.data.objects[n] for n in
           ("kit_barrel", "kit_crate", "kit_rope_coil", "kit_bucket",
            "kit_lantern_hanging")}
    dusk_light()
    colour_structures(c, kit)
    foreground(c, kit)
    far_depth(c)        # must precede vegetation: it displaces the far crests
    vegetation(c)
    lantern_halos(c)    # must be last: it shells every practical in the scene
    # tag everything so a rerun can purge it
    for o in list(c.objects) + list(SRC.objects):
        if not o.name.startswith(TAG):
            o.name = TAG + o.name
    return c


def report(prefix=TAG):
    """Screen-space audit: where each added object actually lands, and whether
    anything is standing in front of it. Cheaper and far more exact than
    eyeballing a preview render."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    dg = bpy.context.evaluated_depsgraph_get()
    org = cam.matrix_world.translation
    rows = []
    for o in sc.objects:
        if not o.name.startswith(prefix) or o.type != "MESH":
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        uv = [world_to_camera_view(sc, cam, p) for p in pts]
        xs = [p.x for p in uv]; ys = [p.y for p in uv]; zs = [p.z for p in uv]
        if max(zs) <= 0 or max(xs) < 0 or min(xs) > 1 or max(ys) < 0 or min(ys) > 1:
            state = "OFFSCREEN"
        else:
            ctr = sum(pts, Vector()) / len(pts)
            d = (ctr - org)
            dist = d.length
            ok, loc, _, _, hit, _ = sc.ray_cast(dg, org, d.normalized(),
                                                distance=dist * 0.985)
            state = "occluded by %s" % hit.name[:22] if ok else "VISIBLE"
        rows.append((o.name, min(xs), max(xs), 1 - max(ys), 1 - min(ys), state))
    for r in sorted(rows):
        print("  %-34s x %.2f-%.2f  y %.2f-%.2f  %s" % r)
    return rows


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = ROOT + "/docs/qa/dellhollow-rebuild/probe_v10.png"
    samples, scale, save, exposure = 224, 1.0, False, -0.45
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out":
            out = argv[i + 1]; i += 2
        elif a == "--samples":
            samples = int(argv[i + 1]); i += 2
        elif a == "--exposure":
            exposure = float(argv[i + 1]); i += 2
        elif a == "--scale":
            scale = float(argv[i + 1]); i += 2
        elif a == "--save":
            save = True; i += 1
        else:
            i += 1
    apply_all()
    if save:
        bpy.ops.wm.save_mainfile()
    sc = bpy.context.scene
    ru.setup_cycles(samples=samples,
                    res=(int(1344 * scale), int(768 * scale)),
                    exposure=exposure)
    sc.cycles.transparent_max_bounces = 24     # leaf cards are alpha-cut
    if not out.startswith("/"):
        out = ROOT + "/" + out
    ru.render_to(out)
    print("WROTE", out)


if __name__ == "__main__":
    main()
