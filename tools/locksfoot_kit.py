"""locksfoot_kit.py — build tools/blends/districts/locksfoot-kit.blend.

  Blender -b --factory-startup -P tools/locksfoot_kit.py

The PREP kit for the Locksfoot district (the lock/dam end of Dellhollow, x 63..110).
It is a STANDALONE library blend: it never opens, reads or writes the master, and it
never writes kitlib.blend.  The Locksfoot custodian appends `lf_*` objects from here
into `dellhollow-master.blend` by name (`bpy.data.libraries.load` — manifest 4/31),
places them at town coordinates and stretches/clones them per manifest 61.

MATERIAL CONTRACT — everything here survives a glTF round trip
--------------------------------------------------------------
* colour is VERTEX COLOUR (`Col`, FLOAT_COLOR, CORNER) -> COLOR_0
* three materials add an IMAGE TEXTURE with real box-projected UVs; glTF writes
  baseColorTexture * COLOR_0, which is exactly the multiply the viewport shows
  (verified pattern from overworld_build.py).  The vertex colour of every face on a
  textured material is pre-divided by that map's mean luminance, or a multiply-only
  pipeline comes back muddy.
* NO procedural node trees reach a material: no box projection, no noise moss, no
  Musgrave grime.  That is the difference from kitlib.blend, whose object-space box
  projection + noise moss is Cycles-only and exports as flat grey.
* textures are referenced RELATIVE (`//../../textures/...` -> tools/textures/), so
  the blend must stay in tools/blends/districts/ — manifest 63: never copy a blend.

Scale contract inherited from kitlib: character = 1.70u, doors 2.1u, railings 1.0u,
stair rise 0.22u.  Everything is modelled at FINAL WORLD SCALE with object scale 1.0.

Collections: LF_LOCK, LF_WHEELS, LF_DAM, LF_BUILD, LF_PROPS, LF_REF.
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Matrix, Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEXDIR = os.path.join(ROOT, "tools/textures")
OUT = os.path.join(ROOT, "tools/blends/districts/locksfoot-kit.blend")

TAU = math.pi * 2


# --------------------------------------------------------------------- colour
def srgb(h):
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# The Boatyard/Waterfront palette, read off the accepted renders and the map's
# style block: weathered PAINTED timber over brown scaffold, BLACK stone for the
# dam, teal-green water, warm ordinary lanterns.  Values are deliberately low —
# manifest 42/53: everything near a practical has to be dark enough to lose to it.
PAL = {
    "oxblood":   "6d2a20",   # painted timber, the reference shed red
    "mossgreen": "45543a",   # painted timber, green
    "fadeblue":  "37505c",   # painted timber, blue
    "timber":    "5c4630",   # brown structural scaffold timber
    "timberdk":  "3d2e20",   # framing, doors, gate leaves
    "deck":      "6f5a3d",   # decking / planking
    "freshwood": "8a6f49",   # newly replaced boards, bright accents
    "stoneblk":  "24211f",   # THE dam: black stone
    "stoneblk2": "302c28",   # its coursing / cap, one step up
    "stonegrey": "4c463d",   # ordinary masonry: plinths, abutments
    "iron":      "241f1c",
    "irondk":    "171412",
    "rust":      "44291a",
    "rope":      "6b5a3c",
    "canvas":    "6a5c44",
    "fall":      "16292c",   # the dark glassy sheet over a gate leaf
    "foam":      "8e9a94",   # the ONLY near-white: crest lip + plunge boil
    "water":     "1b4344",   # teal-green pool
    "glass":     "ffc27a",   # lantern
    "shingle":   "4e5638",   # mossy shingle
    "mosswood":  "3f4a33",
    "leaf":      "374a2c",
    "pumpkin":   "9c4c10",
    "cloth_r":   "7a2f26",   # bunting
    "cloth_g":   "3f5a38",
    "cloth_b":   "34505e",
    "cloth_y":   "8a6f28",
    "skin":      "6b5240",
}
PAL_LIN = {k: srgb(v) for k, v in PAL.items()}


# ------------------------------------------------------------------ materials
# Fixed GLOBAL slot order: every assembly gets the same slots, so a face's
# material index is a constant across the whole kit and nothing has to be remapped
# when the custodian joins or splits assemblies in the master.
SLOTS = ["matte", "deck", "stone", "shingle", "iron", "glass", "water", "foam"]
MI = {n: i for i, n in enumerate(SLOTS)}
GAIN = [1.0] * len(SLOTS)     # per-material vertex-colour pre-gain (textured mats)
MATS = []


def _tex(nt, fname):
    path = os.path.join(TEXDIR, fname)
    img = bpy.data.images.load(path, check_existing=True)
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = img
    return n, img


def make_mat(name, slot, tex=None, rough=0.78, metal=0.0, uvscale=0.45,
             emit=None, emit_str=0.0):
    """Principled + Color Attribute (+ optional image texture multiply).

    The multiply node is the one node tree allowed here: the glTF exporter turns
    exactly this shape into baseColorTexture * COLOR_0.
    """
    m = bpy.data.materials.new(name)
    m.use_fake_user = True                       # manifest 3
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    ca.location = (-620, 120)
    if tex:
        tn, img = _tex(nt, tex)
        tn.location = (-620, -160)
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap"
        uv.location = (-820, -160)
        nt.links.new(uv.outputs["UV"], tn.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.location = (-320, 0)
        pick = lambda nm, t: [x for x in mix.inputs if x.name == nm and x.type == t][0]
        pick("Factor", "VALUE").default_value = 1.0
        nt.links.new(tn.outputs["Color"], pick("A", "RGBA"))
        nt.links.new(ca.outputs["Color"], pick("B", "RGBA"))
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
        GAIN[MI[slot]] = float(np.clip(0.44 / max(px.mean(), 0.03), 1.0, 3.2))
        print("  mat %-10s tex mean %.3f -> vcol gain x%.2f" % (name, px.mean(), GAIN[MI[slot]]))
        m["uvscale"] = uvscale
    else:
        nt.links.new(ca.outputs["Color"], b.inputs["Base Color"])
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def build_materials():
    MATS.append(make_mat("lf_matte", "matte", rough=0.80))
    MATS.append(make_mat("lf_deck", "deck", "weathered_planks_Diffuse.jpg", rough=0.74, uvscale=0.42))
    MATS.append(make_mat("lf_stone", "stone", "old_stone_wall_02_Diffuse.jpg", rough=0.86, uvscale=0.34))
    MATS.append(make_mat("lf_shingle", "shingle", "red_slate_roof_tiles_01_Diffuse.jpg", rough=0.82, uvscale=0.55))
    MATS.append(make_mat("lf_iron", "iron", rough=0.44, metal=0.62))
    MATS.append(make_mat("lf_glass", "glass", rough=0.28,
                         emit=PAL_LIN["glass"], emit_str=9.0))
    MATS.append(make_mat("lf_water", "water", rough=0.10))
    MATS.append(make_mat("lf_foam", "foam", rough=0.62))
    return MATS


# ---------------------------------------------------------------- accumulator
class A:
    """One assembly: a bmesh where every face carries a colour index + a material
    index, finished into a single object with one `Col` attribute and the shared
    material slot list."""

    def __init__(self, name, seed=0):
        self.name = name
        self.bm = bmesh.new()
        self.lm = self.bm.faces.layers.int.new("mi")
        self.lc = self.bm.faces.layers.int.new("ci")
        self.cols = []
        self.cidx = {}
        self.rng = random.Random(seed or (hash(name) & 0xffff))   # manifest 46

    # -- tagging ----------------------------------------------------------
    def _ci(self, col):
        if col not in self.cidx:
            self.cidx[col] = len(self.cols)
            self.cols.append(PAL_LIN[col])
        return self.cidx[col]

    def _tag(self, before, col, mat, jit=0.0):
        ci = self._ci(col)
        mi = MI[mat]
        for f in self.bm.faces:
            if f not in before:
                f[self.lc] = ci
                f[self.lm] = mi

    # -- primitives -------------------------------------------------------
    def box(self, col, mat, c, s, rz=0.0, rx=0.0, ry=0.0):
        before = set(self.bm.faces)
        m = (Matrix.Translation(Vector(c)) @ Matrix.Rotation(rz, 4, "Z")
             @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
             @ Matrix.Diagonal(Vector(s).to_4d()))
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(before, col, mat)

    def bnd(self, col, mat, x0, x1, y0, y1, z0, z1):
        self.box(col, mat, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                 (x1 - x0, y1 - y0, z1 - z0))

    def beam(self, col, mat, a, b, w, h, roll=0.0):
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        if L < 1e-6:
            return
        zv = d.normalized()
        up = Vector((0, 0, 1)) if abs(zv.z) < 0.985 else Vector((0, 1, 0))
        xv = up.cross(zv).normalized()
        yv = zv.cross(xv)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            xv, yv = xv * c + yv * s, -xv * s + yv * c
        m = Matrix((xv, yv, zv)).transposed().to_4x4()
        m.translation = (a + b) / 2
        before = set(self.bm.faces)
        bmesh.ops.create_cube(self.bm, size=1.0,
                              matrix=m @ Matrix.Diagonal(Vector((w, h, L)).to_4d()))
        self._tag(before, col, mat)

    def cyl(self, col, mat, a, b, r, seg=10, r2=None, mat_cap=None):
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        if L < 1e-6:
            return
        zv = d.normalized()
        up = Vector((0, 0, 1)) if abs(zv.z) < 0.985 else Vector((0, 1, 0))
        xv = up.cross(zv).normalized()
        yv = zv.cross(xv)
        m = Matrix((xv, yv, zv)).transposed().to_4x4()
        m.translation = (a + b) / 2
        before = set(self.bm.faces)
        try:
            bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r, radius2=(r if r2 is None else r2),
                                  depth=L, matrix=m)
        except TypeError:
            bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  diameter1=r * 2, diameter2=(r if r2 is None else r2) * 2,
                                  depth=L, matrix=m)
        self._tag(before, col, mat)

    def sphere(self, col, mat, c, r, subd=2):
        before = set(self.bm.faces)
        bmesh.ops.create_icosphere(self.bm, subdivisions=subd, radius=r,
                                   matrix=Matrix.Translation(Vector(c)))
        self._tag(before, col, mat)

    def add(self, col, mat, verts, faces):
        before = set(self.bm.faces)
        vs = [self.bm.verts.new(v) for v in verts]
        for f in faces:
            try:
                self.bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
        self._tag(before, col, mat)

    def hex8(self, col, mat, p):
        """8 points: bottom quad 0-3 then the matching top quad 4-7."""
        self.add(col, mat, p, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                               (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])

    def quad(self, col, mat, p):
        self.add(col, mat, p, [(0, 1, 2, 3)])

    # -- composites -------------------------------------------------------
    def planks(self, col, mat, a, b, z0, z1, t, pw=0.30, gap=0.012, jit=0.010,
               vertical=True):
        """A clad wall / deck face made of individual boards between XY points a,b."""
        a = Vector((a[0], a[1], 0.0))
        b = Vector((b[0], b[1], 0.0))
        d = (b - a)
        L = d.xy.length
        if L < 1e-6:
            return
        u = Vector((d.x, d.y, 0)).normalized()
        n = Vector((-u.y, u.x, 0))
        s = 0.0
        while s < L - 1e-4:
            w = min(pw, L - s)
            p0 = a + u * s
            p1 = a + u * (s + w - gap)
            j = (self.rng.random() - 0.5) * 2 * jit
            q0 = p0 + n * j
            q1 = p1 + n * j
            zz0 = z0 + (self.rng.random() - 0.5) * 0.018
            zz1 = z1 + (self.rng.random() - 0.5) * 0.018
            self.hex8(col, mat, [
                (q0.x, q0.y, zz0), (q1.x, q1.y, zz0),
                (q1.x + n.x * t, q1.y + n.y * t, zz0), (q0.x + n.x * t, q0.y + n.y * t, zz0),
                (q0.x, q0.y, zz1), (q1.x, q1.y, zz1),
                (q1.x + n.x * t, q1.y + n.y * t, zz1), (q0.x + n.x * t, q0.y + n.y * t, zz1)])
            s += w

    def deckboards(self, col, mat, x0, x1, y0, y1, z, t=0.09, pw=0.30, gap=0.014,
                   along_x=False):
        """Flat plank deck, top face AT z (manifest: decks sit at the walk top)."""
        if along_x:
            s = x0
            while s < x1 - 1e-4:
                w = min(pw, x1 - s)
                self.bnd(col, mat, s, s + w - gap, y0, y1, z - t, z)
                s += w
        else:
            s = y0
            while s < y1 - 1e-4:
                w = min(pw, y1 - s)
                self.bnd(col, mat, x0, x1, s, s + w - gap, z - t, z)
                s += w

    def rail(self, col, a, b, h=1.02, post=0.09, mat="matte"):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        n = max(2, int(L / 1.35) + 1)
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            self.beam(col, mat, (p.x, p.y, p.z), (p.x, p.y, p.z + h), post, post)
        for zz, th in ((h, 0.075), (h * 0.52, 0.055)):
            self.beam(col, mat, (a.x, a.y, a.z + zz), (b.x, b.y, b.z + zz), 0.075, th)

    # -- finish -----------------------------------------------------------
    def finish(self, cname, loc=(0, 0, 0)):
        me = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in MATS:
            me.materials.append(m)
        mi = np.zeros(len(me.polygons), dtype=np.int32)
        ci = np.zeros(len(me.polygons), dtype=np.int32)
        me.attributes["mi"].data.foreach_get("value", mi)
        me.attributes["ci"].data.foreach_get("value", ci)
        me.polygons.foreach_set("material_index", mi)
        # --- UVs: manual box projection, headless-safe, exports as REAL UVs ---
        uv = me.uv_layers.new(name="UVMap")
        us = 0.45
        for poly in me.polygons:
            n = poly.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            ui, vi = ((1, 2), (0, 2), (0, 1))[ax]
            sc = MATS[mi[poly.index]].get("uvscale", us)
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (co[ui] * sc, co[vi] * sc)
        # --- vertex colours, pre-gained per material -------------------------
        att = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        me.color_attributes.active_color = att
        me.color_attributes.render_color_index = 0
        cols = np.array(self.cols) if self.cols else np.ones((1, 3))
        g = np.array(GAIN)[mi][:, None]
        fc = np.clip(cols[ci] * g, 0.0, 1.0)
        data = np.zeros((len(me.loops), 4))
        data[:, 3] = 1.0
        for p in me.polygons:
            for li in p.loop_indices:
                data[li, :3] = fc[p.index]
        att.data.foreach_set("color", data.ravel())
        for nm in ("mi", "ci"):                       # build-time scratch, not shipped
            me.attributes.remove(me.attributes[nm])
        ob = bpy.data.objects.new(self.name, me)
        ob.location = loc
        coll(cname).objects.link(ob)
        return ob


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


# ===========================================================================
# 1. LOCK MACHINERY
# ===========================================================================
def gate_leaf(name, W=3.20, H=3.60, walkway=True):
    """One mitre-gate leaf, hung on its heel post.

    Origin = FOOT OF THE HEEL POST, leaf runs +Y, water face is -X.  The custodian
    places two of these mirrored about the chamber centreline and yaws each by the
    mitre angle (~18 deg) so they close pointing upstream, which is the only way a
    mitre gate holds a head of water.
    """
    a = A(name)
    T = 0.15                                    # leaf half-thickness
    a.cyl("timberdk", "matte", (0, 0, -0.20), (0, 0, H + 0.30), 0.21, 10)   # heel post
    a.cyl("timberdk", "matte", (0, W, 0.0), (0, W, H + 0.05), 0.17, 8)      # mitre post
    # planked skin, laid vertically so the head of water bears on the ledgers
    # planks() lays boards on the +normal side of the run, so the run is started
    # at -T and given 2T of thickness: the skin then straddles the post centreline.
    a.planks("timberdk", "matte", (T, 0.16), (T, W - 0.12), 0.10, H - 0.06, 2 * T,
             pw=0.29, gap=0.010, jit=0.008)
    # ledgers (horizontal ribs) + a diagonal brace, on the downstream face
    for z in (0.42, H * 0.44, H - 0.55):
        a.beam("timber", "matte", (T + 0.06, 0.05, z), (T + 0.06, W - 0.05, z), 0.16, 0.20)
        a.beam("iron", "iron", (T + 0.16, 0.02, z), (T + 0.16, W - 0.02, z), 0.055, 0.24)
    a.beam("timber", "matte", (T + 0.06, 0.25, 0.55), (T + 0.06, W - 0.25, H - 0.70), 0.13, 0.17)
    # strap hinges off the heel post
    for z in (0.55, H * 0.5, H - 0.45):
        a.beam("iron", "iron", (0, 0.02, z), (0, 1.05, z), 0.05, 0.16)
        a.cyl("iron", "iron", (-0.26, 0.0, z - 0.13), (-0.26, 0.0, z + 0.13), 0.075, 8)
    if walkway:
        a.deckboards("deck", "deck", -0.36, 0.36, 0.0, W, H + 0.14, t=0.10, pw=0.26)
        a.rail("timber", (0.30, 0.10, H + 0.14), (0.30, W - 0.10, H + 0.14), h=0.94)
    # balance beam: the long tail the keeper leans on to swing the leaf
    a.beam("timber", "matte", (0, 0.05, H + 0.34), (-0.35, -3.10, H + 0.30), 0.24, 0.30)
    a.beam("iron", "iron", (-0.34, -3.05, H + 0.30), (-0.36, -3.30, H + 0.30), 0.20, 0.24)
    a.cyl("iron", "iron", (0.0, -0.55, H + 0.20), (0.0, -0.55, H + 0.50), 0.055, 8)
    # mitre sill nose + a pintle shoe at the foot
    a.bnd("iron", "iron", -0.26, 0.26, -0.10, 0.30, -0.22, 0.02)
    return a.finish("LF_LOCK")


def gate_winch(name="lf_gate_winch"):
    """Rack-and-pinion winding gear for a sluice/gate paddle: the thing that makes
    a lock READ as machinery from any camera.  Origin at the plinth base centre."""
    a = A(name)
    a.bnd("stonegrey", "stone", -0.62, 0.62, -0.62, 0.62, 0.0, 0.34)      # plinth
    for sy in (-0.38, 0.38):                                              # A-frame legs
        a.beam("timber", "matte", (-0.10, sy, 0.34), (0.02, sy * 0.55, 1.86), 0.20, 0.22)
        a.beam("timber", "matte", (0.34, sy, 0.34), (0.06, sy * 0.55, 1.86), 0.18, 0.20)
        a.beam("timber", "matte", (-0.06, sy, 0.95), (0.30, sy, 0.95), 0.13, 0.14)
    a.beam("timber", "matte", (0.04, -0.46, 1.90), (0.04, 0.46, 1.90), 0.22, 0.22)   # head
    # gear wheel (plane = XZ, axis along Y) — rim, 8 spokes, 14 teeth
    cz, cy, R = 1.52, 0.0, 0.60
    a.cyl("iron", "iron", (0.04, cy - 0.05, cz), (0.04, cy + 0.05, cz), R, 20)
    a.cyl("irondk", "iron", (0.04, cy - 0.10, cz), (0.04, cy + 0.10, cz), 0.15, 10)
    for i in range(8):
        t = i * TAU / 8
        a.beam("iron", "iron", (0.04 + 0.13 * math.cos(t), cy, cz + 0.13 * math.sin(t)),
               (0.04 + (R - 0.05) * math.cos(t), cy, cz + (R - 0.05) * math.sin(t)), 0.06, 0.07)
    for i in range(14):
        t = i * TAU / 14
        a.box("iron", "iron", (0.04 + (R + 0.055) * math.cos(t), cy, cz + (R + 0.055) * math.sin(t)),
              (0.13, 0.11, 0.10), ry=-t)
    # pinion + crank
    a.cyl("iron", "iron", (0.04, 0.10, cz + R + 0.28), (0.04, 0.62, cz + R + 0.28), 0.16, 12)
    a.cyl("iron", "iron", (0.04, 0.62, cz + R + 0.28), (0.04, 0.80, cz + R + 0.28), 0.05, 8)
    a.beam("iron", "iron", (0.04, 0.80, cz + R + 0.28), (0.04, 0.82, cz + R + 0.70), 0.06, 0.06)
    a.cyl("timberdk", "matte", (-0.13, 0.82, cz + R + 0.70), (0.21, 0.82, cz + R + 0.70), 0.055, 8)
    # the rack: a toothed bar dropping into the sluice slot
    a.beam("iron", "iron", (0.04, -0.02, 0.10), (0.04, -0.02, cz + 0.50), 0.14, 0.11)
    for i in range(11):
        a.box("iron", "iron", (0.16, -0.02, 0.28 + i * 0.19), (0.10, 0.10, 0.09))
    # pawl + ratchet stop
    a.beam("iron", "iron", (0.34, -0.30, cz + 0.42), (0.10, -0.30, cz + 0.12), 0.05, 0.07)
    a.cyl("rust", "iron", (0.30, -0.40, cz + 0.44), (0.30, -0.20, cz + 0.44), 0.045, 6)
    return a.finish("LF_LOCK")


def capstan(name="lf_capstan"):
    """Warping capstan — how a barge is pulled into the chamber by hand."""
    a = A(name)
    a.cyl("irondk", "iron", (0, 0, 0.0), (0, 0, 0.09), 0.56, 14)
    for i in range(9):                                    # staved drum
        t = i * TAU / 9
        a.box("timberdk", "matte", (0.36 * math.cos(t), 0.36 * math.sin(t), 0.52),
              (0.14, 0.26, 0.86), rz=t)
    a.cyl("rust", "iron", (0, 0, 0.24), (0, 0, 0.32), 0.44, 16)
    a.cyl("rust", "iron", (0, 0, 0.74), (0, 0, 0.82), 0.44, 16)
    a.cyl("timber", "matte", (0, 0, 0.94), (0, 0, 1.10), 0.50, 14)
    for i in range(2):                                    # two bars shipped
        t = i * math.pi / 2 + 0.35
        a.cyl("freshwood", "matte", (0.28 * math.cos(t), 0.28 * math.sin(t), 1.02),
              (1.55 * math.cos(t), 1.55 * math.sin(t), 1.02), 0.055, 8, r2=0.045)
    a.cyl("rope", "matte", (0, 0, 0.86), (0, 0, 0.93), 0.47, 14)    # a turn of rope
    return a.finish("LF_LOCK")


def sluice_paddle(name="lf_sluice_paddle"):
    """A penstock paddle in its slotted frame with a screw stem and hand wheel —
    the small machine that repeats along a dam crest."""
    a = A(name)
    a.bnd("stonegrey", "stone", -0.90, 0.90, -0.28, 0.10, -0.20, 2.30)   # back plate
    a.bnd("stoneblk", "stone", -0.90, -0.60, -0.30, 0.22, -0.20, 2.30)   # slot cheeks
    a.bnd("stoneblk", "stone", 0.60, 0.90, -0.30, 0.22, -0.20, 2.30)
    a.bnd("stoneblk2", "stone", -0.95, 0.95, -0.32, 0.24, 2.30, 2.52)    # lintel
    a.planks("timberdk", "matte", (-0.58, 0.06), (0.58, 0.06), 0.05, 1.05, 0.10,
             pw=0.24, gap=0.008)                                          # the paddle
    for z in (0.22, 0.86):
        a.beam("iron", "iron", (-0.58, 0.18, z), (0.58, 0.18, z), 0.05, 0.14)
    a.beam("iron", "iron", (-0.03, 0.12, 1.02), (-0.03, 0.12, 2.42), 0.10, 0.10)
    a.cyl("iron", "iron", (0, 0.12, 2.42), (0, 0.12, 2.60), 0.05, 8)
    a.cyl("iron", "iron", (0, 0.12, 2.58), (0, 0.12, 2.66), 0.30, 16)     # hand wheel
    for i in range(4):
        t = i * TAU / 4 + 0.4
        a.beam("iron", "iron", (0.05 * math.cos(t), 0.12, 2.62 + 0.05 * math.sin(t)),
               (0.27 * math.cos(t), 0.12, 2.62 + 0.27 * math.sin(t)), 0.05, 0.05)
    a.cyl("irondk", "iron", (0, 0.06, 2.62), (0, 0.18, 2.62), 0.08, 8)
    return a.finish("LF_LOCK")


# ===========================================================================
# 2. WATERWHEELS  (ref 6b: three on the face of the black dam)
# ===========================================================================
def wheel(name, R=2.20, width=1.24, nb=24, spokes=12, bucket=True, rimw=0.16):
    """A wheel in the YZ plane, axis along X, origin at the hub centre.

    bucket=True  -> BREASTSHOT: shrouded rim, sole boards, angled buckets (ref 6b)
    bucket=False -> UNDERSHOT:  open frame, flat radial paddles
    """
    a = A(name)
    hx = width / 2
    ri, ro = R - 0.34, R                      # rim inner / outer radius

    def p(t, r, x):
        return (x, r * math.cos(t), r * math.sin(t))

    # --- axle + gudgeons + hubs ---
    a.cyl("irondk", "iron", (-hx - 0.75, 0, 0), (hx + 0.75, 0, 0), 0.115, 10)
    for sx in (-hx, hx):
        a.cyl("timberdk", "matte", (sx - 0.09, 0, 0), (sx + 0.09, 0, 0), 0.34, 12)
        a.cyl("iron", "iron", (sx - 0.13, 0, 0), (sx + 0.13, 0, 0), 0.20, 10)
    # --- shrouds: faceted rings of chord segments ---
    for sx in (-hx, hx):
        for i in range(nb):
            t0, t1 = i * TAU / nb, (i + 1) * TAU / nb
            a.hex8("timber", "matte", [
                p(t0, ri, sx - rimw / 2), p(t1, ri, sx - rimw / 2),
                p(t1, ro, sx - rimw / 2), p(t0, ro, sx - rimw / 2),
                p(t0, ri, sx + rimw / 2), p(t1, ri, sx + rimw / 2),
                p(t1, ro, sx + rimw / 2), p(t0, ro, sx + rimw / 2)])
        # iron tyre over the shroud
        for i in range(0, nb, 2):
            t0, t1 = i * TAU / nb, (i + 2) * TAU / nb
            a.hex8("rust", "iron", [
                p(t0, ro, sx - rimw / 2), p(t1, ro, sx - rimw / 2),
                p(t1, ro + 0.055, sx - rimw / 2), p(t0, ro + 0.055, sx - rimw / 2),
                p(t0, ro, sx + rimw / 2), p(t1, ro, sx + rimw / 2),
                p(t1, ro + 0.055, sx + rimw / 2), p(t0, ro + 0.055, sx + rimw / 2)])
    # --- spokes ---
    for sx in (-hx, hx):
        for i in range(spokes):
            t = i * TAU / spokes + 0.13
            a.beam("timber", "matte", p(t, 0.28, sx), p(t, ri + 0.06, sx), rimw * 0.62, 0.11)
    # --- buckets / paddles ---
    for i in range(nb):
        t = i * TAU / nb + TAU / nb / 2
        if bucket:
            skew = 0.42
            pi_ = Vector((0, (ri - 0.30) * math.cos(t), (ri - 0.30) * math.sin(t)))
            po_ = Vector((0, ro * math.cos(t - skew), ro * math.sin(t - skew)))
            d = (po_ - pi_).normalized()
            n = Vector((0, -d.z, d.y)) * 0.035
            a.hex8("mosswood", "matte", [
                (-hx + 0.06, pi_.y - n.y, pi_.z - n.z), (-hx + 0.06, po_.y - n.y, po_.z - n.z),
                (-hx + 0.06, po_.y + n.y, po_.z + n.z), (-hx + 0.06, pi_.y + n.y, pi_.z + n.z),
                (hx - 0.06, pi_.y - n.y, pi_.z - n.z), (hx - 0.06, po_.y - n.y, po_.z - n.z),
                (hx - 0.06, po_.y + n.y, po_.z + n.z), (hx - 0.06, pi_.y + n.y, pi_.z + n.z)])
            # sole board closing the back of the bucket
            t2 = t + TAU / nb
            a.hex8("mosswood", "matte", [
                (-hx + 0.06, (ri - 0.30) * math.cos(t), (ri - 0.30) * math.sin(t)),
                (-hx + 0.06, (ri - 0.30) * math.cos(t2), (ri - 0.30) * math.sin(t2)),
                (-hx + 0.06, (ri - 0.24) * math.cos(t2), (ri - 0.24) * math.sin(t2)),
                (-hx + 0.06, (ri - 0.24) * math.cos(t), (ri - 0.24) * math.sin(t)),
                (hx - 0.06, (ri - 0.30) * math.cos(t), (ri - 0.30) * math.sin(t)),
                (hx - 0.06, (ri - 0.30) * math.cos(t2), (ri - 0.30) * math.sin(t2)),
                (hx - 0.06, (ri - 0.24) * math.cos(t2), (ri - 0.24) * math.sin(t2)),
                (hx - 0.06, (ri - 0.24) * math.cos(t), (ri - 0.24) * math.sin(t))])
        else:
            a.hex8("mosswood", "matte", [
                (-hx + 0.05, (ri - 0.42) * math.cos(t) - 0.03 * math.sin(t),
                 (ri - 0.42) * math.sin(t) + 0.03 * math.cos(t)),
                (-hx + 0.05, (ro + 0.10) * math.cos(t) - 0.03 * math.sin(t),
                 (ro + 0.10) * math.sin(t) + 0.03 * math.cos(t)),
                (-hx + 0.05, (ro + 0.10) * math.cos(t) + 0.03 * math.sin(t),
                 (ro + 0.10) * math.sin(t) - 0.03 * math.cos(t)),
                (-hx + 0.05, (ri - 0.42) * math.cos(t) + 0.03 * math.sin(t),
                 (ri - 0.42) * math.sin(t) - 0.03 * math.cos(t)),
                (hx - 0.05, (ri - 0.42) * math.cos(t) - 0.03 * math.sin(t),
                 (ri - 0.42) * math.sin(t) + 0.03 * math.cos(t)),
                (hx - 0.05, (ro + 0.10) * math.cos(t) - 0.03 * math.sin(t),
                 (ro + 0.10) * math.sin(t) + 0.03 * math.cos(t)),
                (hx - 0.05, (ro + 0.10) * math.cos(t) + 0.03 * math.sin(t),
                 (ro + 0.10) * math.sin(t) - 0.03 * math.cos(t)),
                (hx - 0.05, (ri - 0.42) * math.cos(t) + 0.03 * math.sin(t),
                 (ri - 0.42) * math.sin(t) - 0.03 * math.cos(t))])
    # --- iron tie rods between the shrouds ---
    for i in range(0, spokes, 2):
        t = i * TAU / spokes + 0.13
        a.cyl("iron", "iron", p(t, ri - 0.12, -hx + 0.10), p(t, ri - 0.12, hx - 0.10), 0.028, 6)
    return a.finish("LF_WHEELS")


def wheel_bearing(name="lf_wheel_bearing"):
    """The corbel + pillow block a wheel gudgeon runs in, built into the dam face.
    Origin at the AXLE CENTRE so it drops straight onto a wheel."""
    a = A(name)
    a.hex8("stoneblk", "stone", [(-0.42, -0.55, -1.60), (0.42, -0.55, -1.60),
                                 (0.42, 0.25, -1.60), (-0.42, 0.25, -1.60),
                                 (-0.42, -0.34, -0.18), (0.42, -0.34, -0.18),
                                 (0.42, 0.25, -0.18), (-0.42, 0.25, -0.18)])
    a.bnd("stoneblk2", "stone", -0.46, 0.46, -0.40, 0.28, -0.20, -0.06)
    a.bnd("timberdk", "matte", -0.34, 0.34, -0.30, 0.30, -0.06, 0.02)     # sole
    a.cyl("iron", "iron", (-0.30, 0, 0), (0.30, 0, 0), 0.19, 12)          # brass box
    a.bnd("iron", "iron", -0.32, 0.32, -0.22, 0.22, 0.0, 0.20)
    for sx in (-0.24, 0.24):                                              # hold-down bolts
        a.cyl("irondk", "iron", (sx, -0.16, -0.10), (sx, -0.16, 0.30), 0.035, 6)
    a.cyl("rust", "iron", (-0.34, 0, 0), (-0.26, 0, 0), 0.24, 12)
    return a.finish("LF_WHEELS")


# ===========================================================================
# 3. DAM  (black stone — the darkest thing in frame)
# ===========================================================================
def crest_bay(name="lf_crest_bay", LEN=3.90, H=5.20, THK=3.50):
    """ONE repeat of the dam crest, ready to clone along Y at `LEN` pitch
    (manifest 61: extend detailed art by duplicating its own components).

    Origin: crest-deck level at z=0, upstream face at x=-THK/2, the unit runs
    y 0..LEN.  Everything below z=0 is the drowned mass.
    """
    a = A(name)
    x0, x1 = -THK / 2, THK / 2
    # battered mass: the downstream face leans back as it rises
    a.hex8("stoneblk", "stone", [(x0, 0, -H), (x1 + 0.55, 0, -H), (x1 + 0.55, LEN, -H), (x0, LEN, -H),
                                 (x0, 0, -0.22), (x1, 0, -0.22), (x1, LEN, -0.22), (x0, LEN, -0.22)])
    # string courses, broken at the unit ends so a run of them reads as coursing
    for z in (-3.60, -2.40, -1.30):
        f = (z + H) / H
        xf = x1 + 0.55 * (1 - f)
        a.bnd("stoneblk2", "stone", xf - 0.02, xf + 0.20, 0.18, LEN - 0.18, z, z + 0.24)
    # battered downstream pier (the ref's wheel piers stand proud of the wall)
    a.hex8("stoneblk2", "stone", [(x1, LEN * 0.34, -H), (x1 + 1.22, LEN * 0.34, -H),
                                  (x1 + 1.22, LEN * 0.34 + 0.86, -H), (x1, LEN * 0.34 + 0.86, -H),
                                  (x1, LEN * 0.34, -0.22), (x1 + 0.30, LEN * 0.34, -0.22),
                                  (x1 + 0.30, LEN * 0.34 + 0.86, -0.22), (x1, LEN * 0.34 + 0.86, -0.22)])
    # cap + parapet + upstream nosing
    a.bnd("stoneblk2", "stone", x0 - 0.24, x1 + 0.34, 0, LEN, -0.22, 0.0)
    a.bnd("stoneblk2", "stone", x1 + 0.02, x1 + 0.34, 0, LEN, 0.0, 0.86)   # downstream parapet
    a.bnd("stoneblk2", "stone", x0 - 0.24, x0 + 0.06, 0, LEN, 0.0, 0.52)   # upstream kerb
    # the crest walkway itself — timber over the stone, so it reads as a WALK
    a.deckboards("deck", "deck", x0 + 0.10, x1 + 0.00, 0.0, LEN, 0.12, t=0.10, pw=0.28)
    for u in (0.55, LEN - 0.55):
        a.beam("timber", "matte", (x0 + 0.12, u, -0.02), (x1 - 0.02, u, -0.02), 0.14, 0.16)
    return a.finish("LF_DAM")


def spill_bay(name="lf_spill_bay", LEN=3.90, DROP=1.80, THK=3.50, H=5.20):
    """A SPILL BAY — one full crest unit (same 3.90 m pitch as lf_crest_bay) with a
    gate window cut through it, so a run reads pier/bay/pier/bay like ref 6b.  Drop
    it into a GAP in a run of crest bays; the crest walk carries straight over it.

    The leaf is RAISED in its slot and the water pours from under it.  Water is a
    dark glassy sheet with foam ONLY at the lip and in the boil — the Boatyard v4
    lesson: a full-height sheet of white water turns a black dam into concrete
    panels, and manifest 40 (a volume `mat_spray` is invisible: this is a surface).

    Origin: crest level z=0 at the bay centre, unit runs y -LEN/2..+LEN/2,
    downstream is +X.  Tailwater is expected at z = -DROP.
    """
    a = A(name)
    x0, x1 = -THK / 2, THK / 2
    HW, OW = LEN / 2, 0.98              # unit half-length, window half-width
    # the sill has to stand ABOVE the tail pool or the opening is drowned and there
    # is no fall to see.  DROP is the map's dam-five drop (1.8 m) — see the plan's
    # open question about whether that is enough head for ref 6b's wheels.
    SILL = -DROP + 1.02
    for s in (-1, 1):                   # battered cheeks either side of the window
        ya, yb = sorted((s * OW, s * HW))
        a.hex8("stoneblk", "stone", [(x0, ya, -H), (x1 + 0.55, ya, -H),
                                     (x1 + 0.55, yb, -H), (x0, yb, -H),
                                     (x0, ya, -0.22), (x1, ya, -0.22),
                                     (x1, yb, -0.22), (x0, yb, -0.22)])
    a.bnd("stoneblk", "stone", x0, x1 + 0.34, -OW, OW, -H, SILL)          # the sill
    a.bnd("stoneblk2", "stone", x1 + 0.02, x1 + 0.30, -OW, OW, SILL - 0.02, SILL + 0.16)
    a.bnd("stoneblk2", "stone", x0 - 0.24, x1 + 0.34, -HW, HW, -0.22, 0.0)   # cap
    for ya, yb in ((-HW, -1.22), (1.22, HW)):   # parapet, BROKEN around the gate slot
        a.bnd("stoneblk2", "stone", x1 + 0.02, x1 + 0.34, ya, yb, 0.0, 0.86)
    a.bnd("stoneblk2", "stone", x0 - 0.24, x0 + 0.06, -HW, HW, 0.0, 0.52)    # kerb
    a.deckboards("deck", "deck", x0 + 0.10, x1 + 0.00, -HW, HW, 0.12, t=0.10, pw=0.28)
    # the leaf stands DRAWN UP in its guides above the cap, held on two chains off a
    # head beam — from the crest walk it reads as a machine, from the basin as the
    # reason the bay is spilling (manifest 20: model it where it can be SEEN)
    LZ0, LZ1 = 0.04, 0.92
    a.planks("timberdk", "matte", (x1 + 0.38, 0.92), (x1 + 0.38, -0.92), LZ0, LZ1, 0.26,
             pw=0.26, gap=0.008)
    for z in (LZ0 + 0.14, LZ1 - 0.14):
        a.beam("iron", "iron", (x1 + 0.54, -0.94, z), (x1 + 0.54, 0.94, z), 0.12, 0.11)
    for sy in (-1.06, 1.06):            # guides, rising past the parapet
        a.beam("timber", "matte", (x1 + 0.50, sy, -0.20), (x1 + 0.50, sy, 1.52), 0.34, 0.24)
    a.beam("timber", "matte", (x1 + 0.50, -1.18, 1.56), (x1 + 0.50, 1.18, 1.56), 0.24, 0.22)
    a.cyl("iron", "iron", (x1 + 0.50, -0.34, 1.56), (x1 + 0.50, 0.34, 1.56), 0.16, 10)
    for sy in (-0.72, 0.72):            # lift chains
        for k in range(3):
            zz = LZ1 + k * 0.22
            a.cyl("irondk", "iron", (x1 + 0.50, sy + 0.03 * (k % 2), zz),
                  (x1 + 0.50, sy - 0.03 * (k % 2), zz + 0.19), 0.030, 6)
    # WATER.  A nappe leaves the sill clear and glassy, aerates white as it falls,
    # and boils where it lands.  Boatyard v4: the white belongs at the LIP and in
    # the BOIL, never as a full-height panel across the whole weir.
    NAP = 0.24
    a.bnd("fall", "water", x1 + 0.06, x1 + 0.46, -0.92, 0.92, SILL - NAP, SILL + 0.08)
    a.bnd("foam", "foam", x1 + 0.10, x1 + 0.60, -0.88, 0.88, -DROP - 0.06, SILL - NAP + 0.03)
    a.bnd("foam", "foam", x1 - 0.06, x1 + 0.50, -0.94, 0.94, SILL + 0.02, SILL + 0.20)
    # the boil.  It has to break the waterline, not lie ON it: a flat plate of foam
    # at tail level reads as a sheet of paper floating in the pool.  Low wedges,
    # tops barely proud, sloping away downstream.
    for k in range(4):
        u = -0.78 + k * 0.52
        w = 0.26 + 0.08 * ((k * 5) % 3)
        a.hex8("foam", "foam", [(x1 + 0.32, u - w / 2, -DROP - 0.30),
                                (x1 + 0.88 + w, u - w / 2 - 0.08, -DROP - 0.30),
                                (x1 + 0.88 + w, u + w / 2 + 0.08, -DROP - 0.30),
                                (x1 + 0.32, u + w / 2, -DROP - 0.30),
                                (x1 + 0.32, u - w / 2, -DROP + 0.11),
                                (x1 + 0.88 + w, u - w / 2 - 0.08, -DROP - 0.05),
                                (x1 + 0.88 + w, u + w / 2 + 0.08, -DROP - 0.05),
                                (x1 + 0.32, u + w / 2, -DROP + 0.11)])
    return a.finish("LF_DAM")


def crest_gate(name="lf_crest_gate"):
    """The iron-banded gate barring the dam-crest walk to the far shore.  CLOSED
    this chapter (map: dam-crest-gate.state = 'closed'); the far-side stairs are
    'not kept', so the gate is the story beat, not a doorway.
    Origin: centre of the walkway at deck level, the walk runs +Y."""
    a = A(name)
    for sx in (-1.42, 1.42):                                   # stone jamb piers
        a.hex8("stoneblk", "stone", [(sx - 0.44, -0.42, -1.10), (sx + 0.44, -0.42, -1.10),
                                     (sx + 0.44, 0.42, -1.10), (sx - 0.44, 0.42, -1.10),
                                     (sx - 0.36, -0.34, 2.55), (sx + 0.36, -0.34, 2.55),
                                     (sx + 0.36, 0.34, 2.55), (sx - 0.36, 0.34, 2.55)])
        a.bnd("stoneblk2", "stone", sx - 0.44, sx + 0.44, -0.42, 0.42, 2.55, 2.76)
    a.bnd("stoneblk2", "stone", -1.86, 1.86, -0.34, 0.34, 2.34, 2.60)     # lintel
    # the leaf: vertical boards, three iron bands, a cross brace, strap hinges
    a.planks("timberdk", "matte", (-1.06, -0.09), (1.06, -0.09), 0.06, 2.28, 0.11,
             pw=0.24, gap=0.010, jit=0.006)
    for z in (0.34, 1.16, 2.02):
        a.beam("iron", "iron", (-1.08, 0.06, z), (1.08, 0.06, z), 0.05, 0.15)
    a.beam("timber", "matte", (-1.00, 0.05, 0.22), (1.00, 0.05, 2.10), 0.11, 0.13)
    for z in (0.42, 1.98):
        a.beam("iron", "iron", (-1.06, 0.07, z), (-0.30, 0.07, z), 0.05, 0.14)
        a.cyl("iron", "iron", (-1.16, -0.02, z - 0.11), (-1.16, -0.02, z + 0.11), 0.07, 8)
    # chain + padlock across the mitre stile: the "closed" reads at 30 m
    for i in range(7):
        a.cyl("irondk", "iron", (0.72 + i * 0.10, -0.14, 1.28 + 0.04 * math.sin(i * 1.7)),
              (0.80 + i * 0.10, -0.14, 1.24 + 0.04 * math.sin(i * 1.7 + 1)), 0.032, 6)
    a.bnd("irondk", "iron", 1.34, 1.52, -0.20, -0.08, 1.10, 1.30)
    # the "not kept" board, hung canted off one band
    a.box("timberdk", "matte", (0.28, -0.16, 1.72), (0.86, 0.05, 0.34), rx=0.0, ry=0.10)
    a.cyl("iron", "iron", (0.10, -0.14, 1.90), (0.10, -0.14, 2.02), 0.02, 5)
    a.cyl("iron", "iron", (0.48, -0.14, 1.88), (0.48, -0.14, 2.02), 0.02, 5)
    return a.finish("LF_DAM")


# ===========================================================================
# 4. BUILDINGS — the established painted-timber language
# ===========================================================================
def clad_shell(a, W, D, H, body, trim, door_at=None, windows=(), sill=0.0):
    """A timber-framed, painted, plank-clad box centred on the origin, floor at z=0.
    Cladding is vertical boards with per-board jitter (kitlib's wall language,
    rebuilt with vertex colour instead of a procedural moss shader)."""
    hw, hd = W / 2, D / 2
    a.bnd("stonegrey", "stone", -hw - 0.22, hw + 0.22, -hd - 0.22, hd + 0.22, -0.55 + sill, 0.0 + sill)
    z0, z1 = sill, sill + H
    # cladding on all four faces
    a.planks(body, "matte", (-hw, -hd), (hw, -hd), z0 + 0.05, z1, 0.11, pw=0.32, gap=0.012)
    a.planks(body, "matte", (hw, hd), (-hw, hd), z0 + 0.05, z1, 0.11, pw=0.32, gap=0.012)
    a.planks(body, "matte", (hw, -hd), (hw, hd), z0 + 0.05, z1, 0.11, pw=0.32, gap=0.012)
    a.planks(body, "matte", (-hw, hd), (-hw, -hd), z0 + 0.05, z1, 0.11, pw=0.32, gap=0.012)
    # frame: corner posts, sill, head plate, mid rail, one brace per long face
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        a.beam(trim, "matte", (sx * hw, sy * hd, z0 - 0.10), (sx * hw, sy * hd, z1 + 0.12), 0.24, 0.24)
    for sy in (-1, 1):
        for z in (z0 + 0.10, z0 + H * 0.52, z1):
            a.beam(trim, "matte", (-hw, sy * (hd + 0.06), z), (hw, sy * (hd + 0.06), z), 0.16, 0.19)
        a.beam(trim, "matte", (-hw + 0.2, sy * (hd + 0.06), z0 + 0.2),
               (hw - 0.2, sy * (hd + 0.06), z1 - 0.2), 0.12, 0.15)
    for sx in (-1, 1):
        for z in (z0 + 0.10, z1):
            a.beam(trim, "matte", (sx * (hw + 0.06), -hd, z), (sx * (hw + 0.06), hd, z), 0.16, 0.19)
    # windows: casing + mullions + dark glass, applied ON the cladding
    for (fx, fy, u, wz, ww, wh) in windows:
        n = Vector((fx, fy, 0))
        t = Vector((-fy, fx, 0))
        c = Vector((fx * hw, fy * hd, 0)) + t * u
        o = n * 0.13
        a.bnd("glass", "glass", *sorted((c.x + o.x - abs(t.x) * ww / 2 - abs(n.x) * 0.02,
                                         c.x + o.x + abs(t.x) * ww / 2 + abs(n.x) * 0.02)),
              *sorted((c.y + o.y - abs(t.y) * ww / 2 - abs(n.y) * 0.02,
                       c.y + o.y + abs(t.y) * ww / 2 + abs(n.y) * 0.02)),
              wz, wz + wh)
        for k in (-1, 1):                       # jambs
            p = c + t * (k * (ww / 2 + 0.09)) + n * 0.16
            a.beam(trim, "matte", (p.x, p.y, wz - 0.10), (p.x, p.y, wz + wh + 0.10), 0.18, 0.11)
        for z, th in ((wz - 0.10, 0.16), (wz + wh + 0.10, 0.13)):
            p0 = c + t * (-ww / 2 - 0.16) + n * 0.17
            p1 = c + t * (ww / 2 + 0.16) + n * 0.17
            a.beam(trim, "matte", (p0.x, p0.y, z), (p1.x, p1.y, z), 0.22, th)
        p0 = c + t * (-ww / 2) + n * 0.15
        p1 = c + t * (ww / 2) + n * 0.15
        a.beam(trim, "matte", (p0.x, p0.y, wz + wh / 2), (p1.x, p1.y, wz + wh / 2), 0.06, 0.05)
        a.beam(trim, "matte", ((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, wz),
               ((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, wz + wh), 0.05, 0.06)
    # door
    if door_at:
        fx, fy, u = door_at
        n = Vector((fx, fy, 0))
        t = Vector((-fy, fx, 0))
        c = Vector((fx * hw, fy * hd, 0)) + t * u + n * 0.13
        a.planks("timberdk", "matte", (c.x - t.x * 0.52 - n.x * 0.02, c.y - t.y * 0.52 - n.y * 0.02),
                 (c.x + t.x * 0.52 + n.x * 0.02, c.y + t.y * 0.52 + n.y * 0.02),
                 sill + 0.02, sill + 2.10, 0.07, pw=0.26, gap=0.008)
        for k in (-1, 1):
            p = c + t * (k * 0.62) + n * 0.04
            a.beam(trim, "matte", (p.x, p.y, sill), (p.x, p.y, sill + 2.26), 0.20, 0.13)
        p0, p1 = c + t * (-0.70) + n * 0.05, c + t * 0.70 + n * 0.05
        a.beam(trim, "matte", (p0.x, p0.y, sill + 2.26), (p1.x, p1.y, sill + 2.26), 0.24, 0.16)
        for z in (sill + 0.42, sill + 1.72):
            q0, q1 = c + t * (-0.50) + n * 0.09, c + t * 0.50 + n * 0.09
            a.beam("iron", "iron", (q0.x, q0.y, z), (q1.x, q1.y, z), 0.045, 0.12)
        s = c + n * 0.34
        a.bnd("stonegrey", "stone", s.x - 0.62, s.x + 0.62, s.y - 0.42, s.y + 0.42, sill - 0.22, sill)


def gable_roof(a, W, D, H, rise, over=0.42, courses=9, ridge_along_x=True):
    """Shingled gable, courses OVERLAPPED and sheathed in the same material —
    manifest 13: courses laid at 0.62 of their step show the board underneath and
    the roof reads as pale louvres."""
    hw, hd = W / 2 + over, D / 2 + over
    span = hd if ridge_along_x else hw
    for sgn in (-1, 1):
        # sheathing
        n = Vector((0, -sgn * rise, span)) if ridge_along_x else Vector((-sgn * rise, 0, span))
        n.normalize()
        for i in range(courses):
            f0 = i / courses
            f1 = (i + 1.0) / courses
            step = span / courses
            y0 = sgn * (span - f0 * span)
            y1 = sgn * (span - f1 * span)
            z0 = H + rise * f0
            z1 = H + rise * f1
            if ridge_along_x:
                a.hex8("shingle", "shingle",
                       [(-hw, y0, z0 - 0.09), (hw, y0, z0 - 0.09), (hw, y1, z1 - 0.09), (-hw, y1, z1 - 0.09),
                        (-hw, y0, z0 + 0.055), (hw, y0, z0 + 0.055),
                        (hw, y1, z1 + 0.055), (-hw, y1, z1 + 0.055)])
                # the course lip, standing proud where it laps the one below
                a.hex8("shingle", "shingle",
                       [(-hw, y0, z0 - 0.02), (hw, y0, z0 - 0.02),
                        (hw, y0 - sgn * step * 0.55, z0 + rise / courses * 0.55 - 0.02),
                        (-hw, y0 - sgn * step * 0.55, z0 + rise / courses * 0.55 - 0.02),
                        (-hw, y0, z0 + 0.10), (hw, y0, z0 + 0.10),
                        (hw, y0 - sgn * step * 0.55, z0 + rise / courses * 0.55 + 0.10),
                        (-hw, y0 - sgn * step * 0.55, z0 + rise / courses * 0.55 + 0.10)])
    a.bnd("timberdk", "matte", -hw, hw, -0.14, 0.14, H + rise + 0.02, H + rise + 0.20)   # ridge
    # barge boards + rafter tails
    for sy in (-1, 1):
        a.beam("timberdk", "matte", (-hw - 0.03, sy * hd, H - 0.06), (-hw - 0.03, 0, H + rise), 0.10, 0.20)
        a.beam("timberdk", "matte", (hw + 0.03, sy * hd, H - 0.06), (hw + 0.03, 0, H + rise), 0.10, 0.20)
    n = max(3, int(W / 0.85))
    for i in range(n + 1):
        x = -hw + 0.2 + i * (W + 0.4 - 0.4) / n
        for sy in (-1, 1):
            a.beam("timberdk", "matte", (x, sy * (hd - 0.02), H - 0.02),
                   (x, sy * (hd + 0.30), H - 0.20), 0.09, 0.12)


def keepers_cottage(name="lf_keeper_cottage"):
    """'The house over the locks' — the map's enterable landmark, perched on the
    Keepers' Spur with a BALCONY over the drop whose lantern-lit underside is what
    Locksfoot sees from below.  Origin: centre of the footprint at floor level;
    the balcony hangs off +Y (the river side)."""
    a = A(name, seed=5011)
    W, D, H = 6.40, 5.00, 2.95
    clad_shell(a, W, D, H, "mossgreen", "timberdk",
               door_at=(0, -1, -1.30),
               windows=[(0, -1, 1.55, 1.45, 1.15, 1.20),
                        (0, 1, -1.35, 1.50, 1.20, 1.10),
                        (0, 1, 1.55, 1.50, 1.00, 1.10),
                        (1, 0, 0.30, 1.55, 1.05, 1.05),
                        (-1, 0, -0.40, 1.55, 0.95, 1.05)])
    gable_roof(a, W, D, H, 1.55, over=0.46, courses=9)
    # chimney off the west gable, stone, with a sooted cap
    a.bnd("stonegrey", "stone", -W / 2 - 0.42, -W / 2 + 0.34, -0.62, 0.62, -0.30, 4.30)
    a.bnd("stoneblk2", "stone", -W / 2 - 0.56, -W / 2 + 0.46, -0.74, 0.74, 4.30, 4.56)
    a.bnd("iron", "iron", -W / 2 - 0.14, -W / 2 + 0.06, -0.18, 0.18, 4.56, 4.86)
    # --- the balcony: 4.6 x 2.4 cantilevered on raking braces ----------------
    by0, by1 = D / 2, D / 2 + 2.40
    a.deckboards("deck", "deck", -2.30, 2.30, by0, by1, 0.02, t=0.10, pw=0.28, along_x=False)
    for x in (-2.10, -0.70, 0.70, 2.10):
        a.beam("timber", "matte", (x, by0 - 0.10, -0.08), (x, by1 + 0.06, -0.08), 0.14, 0.20)
        a.beam("timber", "matte", (x, by1 - 0.06, -0.16), (x, by0 - 0.10, -1.52), 0.14, 0.18)
        a.beam("timber", "matte", (x, by0 - 0.10, -1.52), (x, by0 - 0.10, -0.10), 0.16, 0.16)
    a.beam("timber", "matte", (-2.34, by1 - 0.05, -0.10), (2.34, by1 - 0.05, -0.10), 0.16, 0.22)
    a.rail("timberdk", (-2.28, by1 - 0.06, 0.02), (2.28, by1 - 0.06, 0.02), h=1.02)
    a.rail("timberdk", (-2.28, by0 + 0.10, 0.02), (-2.28, by1 - 0.06, 0.02), h=1.02)
    a.rail("timberdk", (2.28, by0 + 0.10, 0.02), (2.28, by1 - 0.06, 0.02), h=1.02)
    # supper laid out (the scene the map promises): table, two stools, a lantern post
    a.bnd("freshwood", "deck", -0.95, 0.95, by0 + 0.75, by0 + 1.75, 0.72, 0.80)
    for sx, sy in ((-0.80, by0 + 0.90), (0.80, by0 + 0.90), (-0.80, by0 + 1.60), (0.80, by0 + 1.60)):
        a.beam("timberdk", "matte", (sx, sy, 0.02), (sx, sy, 0.72), 0.09, 0.09)
    for sx in (-1.50, 1.50):
        a.cyl("timberdk", "matte", (sx, by0 + 1.25, 0.02), (sx, by0 + 1.25, 0.46), 0.20, 8)
    a.beam("timber", "matte", (2.16, by1 - 0.20, 0.02), (2.16, by1 - 0.20, 2.30), 0.11, 0.11)
    a.beam("timber", "matte", (2.16, by1 - 0.20, 2.28), (1.72, by1 - 0.20, 2.28), 0.08, 0.08)
    lantern_body(a, (1.72, by1 - 0.20, 2.10))
    # under-balcony lantern — the light Locksfoot sees from the basin below
    lantern_body(a, (0.0, by1 - 0.55, -0.34))
    a.cyl("iron", "iron", (0.0, by1 - 0.55, -0.16), (0.0, by1 - 0.55, -0.10), 0.02, 6)
    # cottage lantern by the door + a bench against the wall
    lantern_body(a, (-0.35, -D / 2 - 0.30, 2.25))
    a.beam("iron", "iron", (-0.35, -D / 2 - 0.06, 2.44), (-0.35, -D / 2 - 0.30, 2.44), 0.06, 0.06)
    a.bnd("timberdk", "matte", 0.90, 2.40, -D / 2 - 0.62, -D / 2 - 0.22, 0.44, 0.52)
    for sx in (1.05, 2.25):
        a.beam("timberdk", "matte", (sx, -D / 2 - 0.42, 0.0), (sx, -D / 2 - 0.42, 0.44), 0.09, 0.09)
    return a.finish("LF_BUILD")


def tenant_shack(name="lf_tenant_shack"):
    """The tenant's shack at the moorage: a mono-pitch lean-to in oxblood paint,
    corrugated roof, stove pipe, a porch of two posts and a net."""
    a = A(name, seed=911)
    W, D, H = 3.80, 3.10, 2.35
    clad_shell(a, W, D, H, "oxblood", "timberdk",
               door_at=(0, -1, 0.55),
               windows=[(0, -1, -1.05, 1.20, 0.85, 0.85), (1, 0, 0.10, 1.25, 0.75, 0.75)])
    # mono-pitch roof, corrugated: boards running down the fall
    hw, hd = W / 2 + 0.40, D / 2 + 0.40
    for i in range(int(W / 0.34) + 1):
        x = -hw + i * 0.34
        a.hex8("rust", "matte", [(x, -hd, H + 0.10), (x + 0.30, -hd, H + 0.10),
                                 (x + 0.30, hd, H + 0.92), (x, hd, H + 0.92),
                                 (x, -hd, H + 0.20), (x + 0.30, -hd, H + 0.20),
                                 (x + 0.30, hd, H + 1.02), (x, hd, H + 1.02)])
    a.beam("timberdk", "matte", (-hw, -hd + 0.05, H + 0.06), (hw, -hd + 0.05, H + 0.06), 0.14, 0.16)
    a.beam("timberdk", "matte", (-hw, hd - 0.05, H + 0.88), (hw, hd - 0.05, H + 0.88), 0.14, 0.16)
    a.cyl("irondk", "iron", (1.05, 0.55, H + 0.55), (1.05, 0.55, H + 1.75), 0.10, 8)
    a.cyl("irondk", "iron", (1.05, 0.55, H + 1.72), (1.05, 0.55, H + 1.86), 0.15, 8)
    # porch: two posts, a shallow awning, a net hung to dry
    for sx in (-1.35, 1.35):
        a.beam("timber", "matte", (sx, -hd - 1.05, -0.02), (sx, -hd - 1.05, 2.28), 0.14, 0.14)
        a.beam("timber", "matte", (sx, -hd - 1.05, 2.26), (sx, -D / 2 - 0.06, 2.44), 0.11, 0.13)
    for i in range(int((W + 1.2) / 0.30) + 1):
        x = -W / 2 - 0.60 + i * 0.30
        a.hex8("canvas", "matte", [(x, -hd - 1.10, 2.24), (x + 0.27, -hd - 1.10, 2.24),
                                   (x + 0.27, -D / 2 - 0.05, 2.42), (x, -D / 2 - 0.05, 2.42),
                                   (x, -hd - 1.10, 2.30), (x + 0.27, -hd - 1.10, 2.30),
                                   (x + 0.27, -D / 2 - 0.05, 2.48), (x, -D / 2 - 0.05, 2.48)])
    a.beam("rope", "matte", (-1.35, -hd - 1.02, 1.55), (1.35, -hd - 1.02, 1.42), 0.03, 0.03)
    for i in range(9):
        u = -1.20 + i * 0.30
        a.beam("rope", "matte", (u, -hd - 1.02, 1.50), (u + 0.10, -hd - 0.92, 0.72), 0.02, 0.02)
        a.beam("rope", "matte", (u, -hd - 0.92, 1.10), (u + 0.30, -hd - 1.02, 1.06), 0.02, 0.02)
    return a.finish("LF_BUILD")


# ===========================================================================
# 5. DOCKSIDE CLUTTER
# ===========================================================================
def lantern_body(a, c, r=0.145, h=0.34):
    """An ORDINARY hanging lantern (world canon: Heartlights do not exist here).
    Iron cage + emissive glass; the custodian parents a POINT light to it in the
    master (manifest 43: put the lamp at the MOUTH, not inside the fitting)."""
    x, y, z = c
    a.bnd("glass", "glass", x - r * 0.68, x + r * 0.68, y - r * 0.68, y + r * 0.68,
          z - h * 0.36, z + h * 0.36)
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.beam("irondk", "iron", (x + sx * r, y + sy * r, z - h / 2),
                   (x + sx * r, y + sy * r, z + h / 2), 0.022, 0.022)
    a.bnd("irondk", "iron", x - r * 1.15, x + r * 1.15, y - r * 1.15, y + r * 1.15,
          z + h / 2, z + h / 2 + 0.07)
    a.bnd("irondk", "iron", x - r, x + r, y - r, y + r, z - h / 2 - 0.05, z - h / 2)
    a.cyl("irondk", "iron", (x, y, z + h / 2 + 0.07), (x, y, z + h / 2 + 0.19), 0.018, 6)


def lantern_post(name="lf_lantern_post"):
    a = A(name)
    a.beam("timber", "matte", (0, 0, 0.0), (0, 0, 2.30), 0.13, 0.13)
    a.beam("timber", "matte", (0, 0, 2.26), (0, 0.44, 2.26), 0.08, 0.08)
    a.beam("timber", "matte", (0, 0, 1.95), (0, 0.34, 2.24), 0.06, 0.06)
    a.cyl("irondk", "iron", (0, 0.44, 2.26), (0, 0.44, 2.16), 0.018, 6)
    lantern_body(a, (0, 0.44, 1.98))
    return a.finish("LF_PROPS")


def bollard(name="lf_bollard"):
    a = A(name)
    a.cyl("timberdk", "matte", (0, 0, -0.35), (0, 0, 0.62), 0.17, 10, r2=0.155)
    a.cyl("rust", "iron", (0, 0, 0.58), (0, 0, 0.70), 0.21, 12)
    a.cyl("rust", "iron", (0, 0, 0.30), (0, 0, 0.38), 0.185, 12)
    for i in range(3):                                   # rope turns
        a.cyl("rope", "matte", (0, 0, 0.12 + i * 0.075), (0, 0, 0.17 + i * 0.075), 0.20, 12)
    return a.finish("LF_PROPS")


def cleat(name="lf_cleat"):
    a = A(name)
    a.bnd("irondk", "iron", -0.10, 0.10, -0.07, 0.07, 0.0, 0.09)
    a.cyl("irondk", "iron", (0, 0, 0.06), (0, 0, 0.19), 0.043, 8)
    a.cyl("irondk", "iron", (-0.24, 0, 0.19), (0.24, 0, 0.19), 0.038, 8, r2=0.028)
    return a.finish("LF_PROPS")


def mooring_post(name="lf_mooring_post"):
    a = A(name)
    a.cyl("mosswood", "matte", (0, 0, -1.90), (0.04, 0.02, 1.05), 0.155, 9, r2=0.135)
    a.cyl("rust", "iron", (0.03, 0.01, 0.94), (0.04, 0.02, 1.02), 0.18, 12)
    a.cyl("rope", "matte", (0.02, 0.01, 0.62), (0.03, 0.01, 0.80), 0.185, 12)
    return a.finish("LF_PROPS")


def barrel(name="lf_barrel"):
    a = A(name)
    for i in range(11):
        t = i * TAU / 11
        a.box("timberdk", "matte", (0.30 * math.cos(t), 0.30 * math.sin(t), 0.44),
              (0.075, 0.20, 0.88), rz=t)
    for z in (0.10, 0.44, 0.78):
        a.cyl("rust", "iron", (0, 0, z - 0.035), (0, 0, z + 0.035), 0.335, 14)
    a.cyl("timber", "matte", (0, 0, 0.84), (0, 0, 0.90), 0.28, 12)
    return a.finish("LF_PROPS")


def crate(name="lf_crate", s=0.72, col="timber"):
    a = A(name)
    h = s / 2
    for sx in (-1, 1):
        a.bnd(col, "matte", sx * h - 0.05, sx * h + 0.05, -h, h, 0, s)
        a.bnd(col, "matte", -h, h, sx * h - 0.05, sx * h + 0.05, 0, s)
    a.bnd(col, "matte", -h, h, -h, h, s - 0.06, s)
    a.bnd(col, "matte", -h, h, -h, h, 0.0, 0.05)
    for z in (0.10, s - 0.14):
        a.bnd("timberdk", "matte", -h - 0.02, h + 0.02, -h - 0.02, h + 0.02, z, z + 0.06)
    return a.finish("LF_PROPS")


def cargo_stack(name="lf_cargo_stack"):
    """Crates, barrels and a pumpkin load — the map's motif, as ONE prop the
    custodian can drop on a deck or a barge without composing it each time."""
    a = A(name, seed=771)
    a.bnd("timber", "matte", -0.42, 0.42, -0.42, 0.42, 0.0, 0.70)
    a.bnd("timberdk", "matte", -0.44, 0.44, -0.44, 0.44, 0.10, 0.16)
    a.bnd("timberdk", "matte", -0.44, 0.44, -0.44, 0.44, 0.56, 0.62)
    a.box("timber", "matte", (0.10, 0.06, 1.04), (0.72, 0.72, 0.68), rz=0.28)
    a.bnd("timberdk", "matte", -0.30, 0.50, -0.34, 0.46, 1.08, 1.14)
    for i in range(11):                                          # a pumpkin load
        r = a.rng
        a.sphere("pumpkin", "matte",
                 (-0.90 + r.random() * 0.70, -0.85 + r.random() * 1.55, 0.18 + (i // 6) * 0.30),
                 0.16 + r.random() * 0.05, subd=2)
    a.bnd("canvas", "matte", -1.10, -0.30, -1.00, 0.85, 0.0, 0.06)
    for z in (0.09, 0.44):
        a.cyl("rust", "iron", (0.92, -0.55, z), (0.92, -0.55, z + 0.05), 0.30, 12)
    for i in range(9):
        t = i * TAU / 9
        a.box("timberdk", "matte", (0.92 + 0.27 * math.cos(t), -0.55 + 0.27 * math.sin(t), 0.39),
              (0.07, 0.18, 0.78), rz=t)
    return a.finish("LF_PROPS")


def rope_coil(name="lf_rope_coil"):
    a = A(name)
    for i in range(4):
        r = 0.36 - i * 0.055
        n = 18
        for k in range(n):
            t0, t1 = k * TAU / n, (k + 1) * TAU / n
            a.beam("rope", "matte", (r * math.cos(t0), r * math.sin(t0), 0.04 + i * 0.062),
                   (r * math.cos(t1), r * math.sin(t1), 0.04 + i * 0.062), 0.055, 0.055)
    return a.finish("LF_PROPS")


def bunting(name="lf_bunting_swag", span=9.0, sag=1.05, n=15):
    """A festival swag — the town's signature motif, strung across the gorge and
    between houses.  Origin at the LEFT anchor; the run goes +X and hangs -Z."""
    a = A(name)
    cols = ("cloth_r", "cloth_g", "cloth_b", "cloth_y")

    def z(u):
        return -sag * 4 * u * (1 - u)

    for k in range(n * 2):
        u0, u1 = k / (n * 2), (k + 1) / (n * 2)
        a.beam("rope", "matte", (u0 * span, 0, z(u0)), (u1 * span, 0, z(u1)), 0.028, 0.028)
    for i in range(n):
        u = (i + 0.5) / n
        x, zz = u * span, z(u)
        c = cols[i % 4]
        w, hh = 0.30, 0.42
        tilt = (a.rng.random() - 0.5) * 0.5
        a.add(c, "matte", [(x - w / 2, 0.01, zz - 0.02), (x + w / 2, 0.01, zz - 0.02),
                           (x + tilt * 0.1, 0.01 + tilt * 0.14, zz - hh)],
              [(0, 1, 2)])
        a.add(c, "matte", [(x - w / 2, -0.01, zz - 0.02), (x + w / 2, -0.01, zz - 0.02),
                           (x + tilt * 0.1, -0.01 + tilt * 0.14, zz - hh)],
              [(2, 1, 0)])
    return a.finish("LF_PROPS")


def barge(name="lf_barge"):
    """A flat cargo barge — the map's 'moored flat barges with cargo' motif, and
    the hull the boat-gained-at-Lock-Five beat needs at the moorage.
    Manifest 77: a boat is a SOLID with a floor ABOVE the waterline, not a sheet.
    Origin at the waterline, bow +X."""
    a = A(name, seed=331)
    L, B, D = 7.60, 2.55, 0.78
    fl = -0.26                                  # floor, above the water plane
    hb = B / 2
    st = [(-L / 2, hb * 0.42), (-L / 2 + 1.05, hb * 0.86), (-1.6, hb), (1.6, hb),
          (L / 2 - 1.35, hb * 0.84), (L / 2, hb * 0.36)]
    for i in range(len(st) - 1):
        (x0, y0), (x1, y1) = st[i], st[i + 1]
        for sy in (-1, 1):
            a.hex8("timberdk", "matte", [
                (x0, sy * y0, fl - 0.10), (x1, sy * y1, fl - 0.10),
                (x1, sy * (y1 - 0.10), fl - 0.10), (x0, sy * (y0 - 0.10), fl - 0.10),
                (x0, sy * y0, fl + D), (x1, sy * y1, fl + D),
                (x1, sy * (y1 - 0.10), fl + D), (x0, sy * (y0 - 0.10), fl + D)])
            a.hex8("timber", "matte", [                       # gunwale, folded inboard
                (x0, sy * (y0 + 0.04), fl + D), (x1, sy * (y1 + 0.04), fl + D),
                (x1, sy * (y1 - 0.20), fl + D), (x0, sy * (y0 - 0.20), fl + D),
                (x0, sy * (y0 + 0.04), fl + D + 0.09), (x1, sy * (y1 + 0.04), fl + D + 0.09),
                (x1, sy * (y1 - 0.20), fl + D + 0.09), (x0, sy * (y0 - 0.20), fl + D + 0.09)])
        # floor + bottom
        a.hex8("deck", "deck", [(x0, -y0, fl - 0.10), (x1, -y1, fl - 0.10),
                                (x1, y1, fl - 0.10), (x0, y0, fl - 0.10),
                                (x0, -y0, fl), (x1, -y1, fl), (x1, y1, fl), (x0, y0, fl)])
    a.bnd("timberdk", "matte", -L / 2 - 0.14, -L / 2 + 0.02, -hb * 0.46, hb * 0.46, fl - 0.12, fl + D + 0.10)
    a.bnd("timberdk", "matte", L / 2 - 0.02, L / 2 + 0.14, -hb * 0.40, hb * 0.40, fl - 0.12, fl + D + 0.10)
    for x in (-2.35, 0.0, 2.35):                              # thwarts
        a.bnd("timber", "matte", x - 0.11, x + 0.11, -hb + 0.14, hb - 0.14, fl + D - 0.16, fl + D)
    a.cyl("timber", "matte", (-L / 2 + 0.55, 0, fl + 0.02), (-L / 2 + 0.30, 0.10, fl + 2.55), 0.055, 8)
    for sx in (-1, 1):
        a.cyl("rust", "iron", (sx * (L / 2 - 0.55), -hb + 0.06, fl + D + 0.05),
              (sx * (L / 2 - 0.55), -hb + 0.06, fl + D + 0.14), 0.075, 8)
    return a.finish("LF_PROPS")


def ref_human(name="REF_human_1p7"):
    """1.70u scale reference — keep one in frame while composing (kitlib contract)."""
    a = A(name)
    a.cyl("skin", "matte", (0, 0, 0.02), (0, 0, 0.92), 0.16, 10)
    a.cyl("fadeblue", "matte", (0, 0, 0.86), (0, 0, 1.42), 0.20, 10)
    a.sphere("skin", "matte", (0, 0, 1.55), 0.145, 2)
    for sx in (-1, 1):
        a.cyl("fadeblue", "matte", (sx * 0.20, 0, 1.35), (sx * 0.24, 0, 0.92), 0.055, 6)
    return a.finish("LF_REF")


# ===========================================================================
def main():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    build_materials()

    made = []
    made.append(gate_leaf("lf_gate_leaf", 3.20, 3.60))
    made.append(gate_leaf("lf_gate_leaf_low", 2.60, 2.40))
    made.append(gate_winch())
    made.append(capstan())
    made.append(sluice_paddle())
    made.append(wheel("lf_wheel_breast", R=2.20, width=1.24, nb=24, spokes=12, bucket=True))
    made.append(wheel("lf_wheel_breast_wide", R=2.60, width=1.80, nb=28, spokes=14, bucket=True))
    made.append(wheel("lf_wheel_undershot", R=1.50, width=0.86, nb=16, spokes=8, bucket=False))
    made.append(wheel_bearing())
    made.append(crest_bay())
    made.append(spill_bay())
    made.append(crest_gate())
    made.append(keepers_cottage())
    made.append(tenant_shack())
    made.append(lantern_post())
    made.append(bollard())
    made.append(cleat())
    made.append(mooring_post())
    made.append(barrel())
    made.append(crate())
    made.append(cargo_stack())
    made.append(rope_coil())
    made.append(bunting())
    made.append(barge())
    made.append(ref_human())

    # relative texture paths — the blend MUST stay in tools/blends/districts/
    for im in bpy.data.images:
        if im.filepath:
            im.filepath = bpy.path.relpath(im.filepath, start=os.path.dirname(OUT))
    txt = bpy.data.texts.new("LOCKSFOOT_KIT_NOTES")
    txt.write(__doc__)
    txt.use_fake_user = True

    tot = 0
    print("\n%-24s %7s %7s  %s" % ("object", "verts", "tris", "bbox (m)"))
    for ob in made:
        me = ob.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        tot += tris
        xs = [v.co for v in me.vertices]
        bb = (max(v.x for v in xs) - min(v.x for v in xs),
              max(v.y for v in xs) - min(v.y for v in xs),
              max(v.z for v in xs) - min(v.z for v in xs))
        print("%-24s %7d %7d  %.2f x %.2f x %.2f"
              % (ob.name, len(me.vertices), tris, *bb))
        assert tuple(ob.scale) == (1.0, 1.0, 1.0), ob.name
        assert "Col" in me.color_attributes, ob.name
        assert "UVMap" in me.uv_layers, ob.name
    print("TOTAL %d objects, %d tris" % (len(made), tot))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("saved", OUT)


main()
