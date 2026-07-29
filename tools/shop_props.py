#!/usr/bin/env python3
"""Shared vocabulary for the Dellhollow SHOP interiors.

Three things live here, and nothing else:

  1. **The room contract.** Every shop is the same FF9 cutaway box seen from
     the same fixed camera: same shell, same counter footprint, same shelving
     carcass, same beams, same walk pads. Those numbers are constants here so
     that a skin table can place things against them without importing the
     builder (which would be circular).

  2. **The prop vocabulary.** Free functions that stamp geometry into an
     `IMesh`. They know nothing about which shop they are in -- `jar` is a jar
     whether it holds salve or quenching oil, `helm` is a helm on a shelf or on
     a stand. A skin is a *selection* from this vocabulary, which is the whole
     point of splitting it out.

  3. **The shared RNG.** One stream, `R`, consumed in build order, so a rebuild
     is deterministic. The builder aliases it rather than making its own.

The builder is `tools/item_int_build.py`; the selections are in
`tools/shop_skins.py`.
"""
import bpy, bmesh, math, random, os, importlib.util
from mathutils import Matrix, Vector, Euler, noise

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TOOLS = os.path.join(ROOT, "tools")


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pb = _mod("probe_build")          # Mesh / place / append_from_kit helpers

R = random.Random(20260729)


# ============================================================ room contract

HW = 4.00          # half width  -> x in [-4, 4]
YB, YF = 3.00, -3.00   # back wall plane, open front edge
WH = 3.00          # wall height (matches the 3x3 kit panels)
CLAD = 0.126       # kit panel: cladding front face sits this far in front of origin
IX = HW - CLAD     # inner face of the side walls  (3.874)
IY = YB - CLAD     # inner face of the back wall   (2.874)

BEAM_Z = 2.860     # centre of the ceiling beams (tucked up under the plate:
BEAM_H = 0.075     # a lower beam becomes a black bar across the counter line)
BEAM_Y = (-1.70, 0.40, 2.20)
# (y, x0, x1) -- the front beam is a HALF beam carried on a post at x = -1.15
BEAMS = ((BEAM_Y[0], -HW, -1.15), (BEAM_Y[1], -HW, HW), (BEAM_Y[2], -HW, HW))
BZ = BEAM_Z - BEAM_H               # underside of the beams: hanging goods hang here
POST_X = BEAMS[0][2]               # the aisle post carrying the half beam

CTR_X0, CTR_X1 = 0.30, IX          # counter runs from the gap to the right wall
CTR_Y0, CTR_Y1 = 0.34, 1.08        # front face / back face
CTR_H = 1.05                       # counter height (project standard)
CTR_YC = (CTR_Y0 + CTR_Y1) / 2

SHELF_X0, SHELF_X1 = 0.52, IX
SHELF_Y0, SHELF_Y1 = IY - 0.36, IY
SHELF_BOARDS = (0.34, 0.82, 1.30, 1.78, 2.26)

DOOR_X = -2.50     # centre of the back-wall door bay
WIN_Y = 1.50       # centre of the left-wall window bay

# browse island (trestle) in the middle of the aisle
ISL_X0, ISL_X1, ISL_Y0, ISL_Y1, ISL_H = -2.10, -0.62, -1.20, -0.38, 0.76

# the corner the tall silhouette prop stands in (oars / polearms / armour stand)
CORNER = (-3.05, -2.05)


def M(n):
    m = bpy.data.materials.get(n)
    if m is None:
        raise KeyError("material missing: %s" % n)
    return m


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def point(name, loc, energy, color, radius=0.04):
    """A practical. Props that carry a flame make their own light."""
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    coll("INT_LIGHT").objects.link(o)
    o.location = loc
    return o


def area(name, loc, energy, color, size=1.0, size_y=None, rot=(0, 0, 0),
         camera=False, look_at=None):
    """A soft, usually camera-invisible pool light. A POINT practical models a
    flame but throws an inverse-square hotspot; the broad, low pool a fire lays
    on the surfaces AROUND it is a different light and wants its own lamp."""
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.color = color
    if size_y is None:
        d.shape, d.size = "SQUARE", size
    else:
        d.shape, d.size, d.size_y = "RECTANGLE", size, size_y
    o = bpy.data.objects.new(name, d)
    coll("INT_LIGHT").objects.link(o)
    o.location = loc
    if look_at is not None:
        o.rotation_euler = (Vector(look_at) - Vector(loc)) \
            .to_track_quat("-Z", "Y").to_euler()
    else:
        o.rotation_euler = rot
    o.visible_camera = camera
    return o


def spot(name, loc, look_at, energy, color, cone=54.0, blend=0.55, radius=0.10,
         camera=False):
    """A shaped pool. An AREA lamp lights everything in its hemisphere, so
    using one to feature a single prop washes the whole bay it stands in; a
    SPOT puts the light where the composition wants it and lets the
    surroundings stay dark, which is what makes the featured thing read.

    Note the energy scale: a spot's power is spread over its cone, not over a
    sphere, so a 54 deg cone concentrates roughly 20x versus a POINT of the
    same wattage. Two figures here do the work of a three-figure practical.
    """
    d = bpy.data.lights.new(name, "SPOT")
    d.energy = energy
    d.color = color
    d.spot_size = math.radians(cone)
    d.spot_blend = blend
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    coll("INT_LIGHT").objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(look_at) - Vector(loc)) \
        .to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = camera
    return o


def smoke_wisp(name, loc, dims, color=(0.70, 0.52, 0.38), density=0.62,
               seed=3.1, squash=0.70, c=None):
    """A bounded smoke plume.

    Kit findings 1/12/27, all three at once. (1) Never the World volume. (2) A
    box that is harmless off-frame quietly hazes half the plate once it moves
    into shot, so it is sized to the plume and nothing else. (3) Density is a
    TEXTURE: a radial falloff on `Generated` coords -- which map any box to
    0..1 whatever its size -- takes the density to zero before it reaches a
    face, so the box never prints its own edges, and a noise ramp straddling
    the noise mean breaks the ellipsoid into something ragged.
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0,
                          matrix=Matrix.Translation(loc) @ Matrix.Diagonal(
                              (dims[0], dims[1], dims[2], 1.0)))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (c or coll("INT_LIGHT")).objects.link(ob)

    mat = bpy.data.materials.get("mat_" + name.lower()) or \
        bpy.data.materials.new("mat_" + name.lower())
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumeScatter"); vol.location = (-200, 0)
    vol.inputs["Density"].default_value = 0.0
    vol.inputs["Color"].default_value = (color[0], color[1], color[2], 1)
    vol.inputs["Anisotropy"].default_value = 0.28
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1400, 0)
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.location = (-1200, 0)
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.40)
    nt.links.new(tc.outputs["Generated"], sub.inputs[0])
    sc_ = nt.nodes.new("ShaderNodeVectorMath"); sc_.location = (-1020, 0)
    sc_.operation = "MULTIPLY"
    sc_.inputs[1].default_value = (1.0, 1.0, squash)
    nt.links.new(sub.outputs["Vector"], sc_.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.location = (-840, 0)
    ln.operation = "LENGTH"
    nt.links.new(sc_.outputs["Vector"], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange"); fall.location = (-660, 0)
    fall.inputs["From Min"].default_value = 0.12
    fall.inputs["From Max"].default_value = 0.44
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.location = (-840, -300)
    nz.inputs["Scale"].default_value = 6.2
    nz.inputs["Detail"].default_value = 6.0
    # the noise node only exposes W in 4D mode; W is how a plume is re-seeded
    # without moving the box it lives in
    try:
        nz.noise_dimensions = "4D"
        nz.inputs["W"].default_value = seed
    except (AttributeError, KeyError):
        pass
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nr = nt.nodes.new("ShaderNodeValToRGB"); nr.location = (-660, -300)
    nr.color_ramp.elements[0].position = 0.36
    nr.color_ramp.elements[0].color = (0.10, 0.10, 0.10, 1)
    nr.color_ramp.elements[1].position = 0.72
    nr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], nr.inputs["Fac"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.location = (-440, -140)
    mul.operation = "MULTIPLY"
    nt.links.new(fall.outputs["Result"], mul.inputs[0])
    nt.links.new(nr.outputs["Color"], mul.inputs[1])
    amt = nt.nodes.new("ShaderNodeMath"); amt.location = (-300, -140)
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = density
    nt.links.new(mul.outputs["Value"], amt.inputs[0])
    nt.links.new(amt.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mat.use_fake_user = True
    me.materials.append(mat)
    ob.visible_shadow = False
    return ob


# ================================================================== meshing

class IMesh(pb.Mesh):
    """probe_build.Mesh plus the primitives an interior needs: lathes for
    turned/coopered goods, strands for cordage, spheres for produce."""

    def sphere(self, center, r, mat, seg=14, rings=8, scale=(1, 1, 1), rot=(0, 0, 0)):
        try:
            res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg,
                                            v_segments=rings, radius=1.0)
        except TypeError:
            res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg,
                                            v_segments=rings, diameter=1.0)
        self.stamp(res["verts"], mat,
                   Matrix.Translation(center)
                   @ Euler(rot, "XYZ").to_matrix().to_4x4()
                   @ Matrix.Diagonal((r * scale[0], r * scale[1], r * scale[2], 1.0)))

    def lathe(self, base, profile, mat, seg=16, aspect=(1.0, 1.0), lumpy=0.0,
              seed=0.0, rot=0.0, orient=None):
        """profile: [(radius, z), ...] bottom to top. Start/end at r=0 to cap.

        `rot` spins the profile about the revolve axis. `orient` is an Euler
        that tilts the WHOLE solid -- without it a lathe always revolves about
        world Z, which is fine for a jar and catastrophic for a shield: every
        shield in the armour shop came out lying flat like a dinner plate
        however its prop was rotated, because only the boxes were listening.
        """
        E = Euler(orient, "XYZ").to_matrix() if orient else None
        B = Vector(base)
        rows = []
        for r, z in profile:
            row = []
            for k in range(seg + 1):
                a = rot + 2 * math.pi * k / seg
                rr = r
                if lumpy and r > 1e-4:
                    rr = r * (1.0 + lumpy * noise.noise(
                        Vector((math.cos(a) * 2.2, math.sin(a) * 2.2, z * 3.1 + seed))))
                p = Vector((rr * aspect[0] * math.cos(a),
                            rr * aspect[1] * math.sin(a), z))
                row.append(tuple(B + (E @ p if E else p)))
            rows.append(row)
        self.quad_strip(rows, mat)

    def strand(self, pts, r, mat, seg=6, r2=None):
        for a, b in zip(pts[:-1], pts[1:]):
            a, b = Vector(a), Vector(b)
            d = b - a
            if d.length < 1e-5:
                continue
            e = d.to_track_quat("Z", "Y").to_euler()
            self.cyl(tuple((a + b) / 2), r, d.length * 1.04, mat, seg=seg,
                     rot=(e.x, e.y, e.z), r2=r2)

    def plate(self, center, length, width, thick, mat, rot=(0, 0, 0), taper=1.0,
              tip=0.0, bow=0.0, n=5, cap=True):
        """A flat blade-like solid extruded along local +Z, `width` across
        local X and `thick` through local Y.

        The workhorse for blades, axe bits, shield boards and armour plate.
        `taper` is the width multiplier at the far end, `tip` the fraction of
        the length that converges to a point, `bow` a sideways curve.
        """
        rows = []
        seq = [(i / n) for i in range(n + 1)]
        for t in seq:
            w = width * (1.0 + (taper - 1.0) * t) * 0.5
            th = thick * 0.5
            if tip and t > 1.0 - tip:
                k = max(0.0, (1.0 - t) / tip)
                w *= k
                th *= max(0.22, k)
            z = (t - 0.5) * length
            yb = bow * math.sin(math.pi * t)
            rows.append([(-w, yb - th, z), (w, yb - th, z),
                         (w, yb + th, z), (-w, yb + th, z), (-w, yb - th, z)])
        if cap:
            z0 = rows[0][0][2]
            rows.insert(0, [(0, 0, z0)] * 5)
            zn = rows[-1][0][2]
            rows.append([(0, rows[-1][0][1], zn)] * 5)
        E = Euler(rot, "XYZ").to_matrix()
        C = Vector(center)
        self.quad_strip([[tuple(C + E @ Vector(p)) for p in row] for row in rows], mat)

    def arc_lathe(self, base, profile, mat, seg=14, a0=-1.6, a1=1.6,
                  aspect=(1.0, 1.0), rot=0.0, orient=None):
        """A partial revolve -- an open shell. Breastplates, pauldrons, hoods:
        the things that are a curved sheet rather than a closed solid.
        `orient` tilts the whole shell (see `lathe`)."""
        E = Euler(orient, "XYZ").to_matrix() if orient else None
        B = Vector(base)
        rows = []
        for r, z in profile:
            row = []
            for k in range(seg + 1):
                a = rot + a0 + (a1 - a0) * k / seg
                p = Vector((r * aspect[0] * math.cos(a),
                            r * aspect[1] * math.sin(a), z))
                row.append(tuple(B + (E @ p if E else p)))
            rows.append(row)
        self.quad_strip(rows, mat)


def frame(origin, rot):
    """Local -> world for a compound prop that is placed as a unit."""
    E = Euler(rot, "XYZ").to_matrix()
    O = Vector(origin)
    def P(lx, ly, lz):
        return tuple(O + E @ Vector((lx, ly, lz)))
    return P


def sagline(p0, p1, dz, n=12):
    """Parabolic sag between two points -- cordage, netting, bunting."""
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= dz * 4.0 * t * (1.0 - t)
        out.append(tuple(p))
    return out


# ============================================================ general goods

def jar(m, x, y, z, h=0.28, r=0.085, mat=None, label=True, lid=True, seed=0):
    mat = mat or M("mat_i_ceramic")
    prof = [(0, 0), (r * 0.80, 0), (r * 0.97, h * 0.14), (r, h * 0.42),
            (r * 0.93, h * 0.70), (r * 0.66, h * 0.90), (r * 0.62, h * 0.96), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=16, lumpy=0.02, seed=seed)
    if lid:
        m.cyl((x, y, z + h + 0.012), r * 0.70, 0.026, M("mat_i_canvas"), seg=14)
        m.strand(sagline((x - r * 0.72, y, z + h + 0.004),
                         (x + r * 0.72, y, z + h + 0.004), 0.004, 4),
                 0.006, M("mat_rope"), seg=5)
    if label:
        m.box((x, y - r * 0.99, z + h * 0.46), (r * 0.55, 0.004, h * 0.20),
              M("mat_i_label"), rot=(0, 0, 0))
        m.box((x, y - r * 1.02, z + h * 0.50), (r * 0.36, 0.003, h * 0.035),
              M("mat_i_iron"))


def bottle(m, x, y, z, h=0.30, r=0.052, mat=None, seed=0):
    mat = mat or M("mat_i_glass_brown")
    prof = [(0, 0), (r * 0.9, 0), (r, h * 0.10), (r * 0.97, h * 0.46),
            (r * 0.55, h * 0.62), (r * 0.32, h * 0.72), (r * 0.30, h * 0.94),
            (r * 0.36, h * 0.97), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=14, seed=seed)
    m.cyl((x, y, z + h * 0.96), r * 0.30, 0.03, M("mat_i_wax"), seg=10)


def tin(m, x, y, z, h=0.115, r=0.062, mat=None):
    mat = mat or M("mat_i_rust")
    m.lathe((x, y, z), [(0, 0), (r, 0), (r, h * 0.92), (r * 0.94, h), (0, h)],
            mat, seg=14)
    m.cyl((x, y, z + h + 0.006), r * 0.98, 0.012, M("mat_i_iron"), seg=14)


def candle_bundle(m, x, y, z, n=7, h=0.26, seed=0):
    w = M("mat_i_wax")
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 0.030 if i else 0.0
        m.cyl((x + rr * math.cos(a), y + rr * math.sin(a), z + h / 2),
              0.0135, h * R.uniform(0.9, 1.05), w, seg=8)
        m.strand([(x + rr * math.cos(a), y + rr * math.sin(a), z + h),
                  (x + rr * math.cos(a), y + rr * math.sin(a), z + h + 0.018)],
                 0.0028, M("mat_i_iron"), seg=4)
    m.strand(sagline((x - 0.05, y - 0.045, z + h * 0.55),
                     (x + 0.05, y - 0.045, z + h * 0.55), 0.006, 4),
             0.007, M("mat_rope"), seg=5)


def rolled_chart(m, x, y, z, h=0.34, lean=0.10, mat=None):
    m.cyl((x, y, z + h / 2), 0.030, h, mat or M("mat_i_paper"), seg=10,
          rot=(0, lean, 0))
    m.strand([(x, y - 0.033, z + h * 0.55), (x, y + 0.033, z + h * 0.55)],
             0.005, M("mat_rope"), seg=5)


def bowl_stack(m, x, y, z, n=3, r=0.085):
    for i in range(n):
        zz = z + i * 0.042
        m.lathe((x, y, zz), [(r * 0.45, 0), (r * 0.52, 0.006), (r, 0.048),
                             (r * 0.96, 0.052), (r * 0.44, 0.012)],
                M("mat_i_ceramic_b") if i % 2 else M("mat_i_ceramic"), seg=14)


def sack(m, x, y, z, h=0.40, r=0.20, seed=0.0, mat=None, tilt=0.0):
    mat = mat or M("mat_i_burlap")
    prof = [(0, 0), (r * 0.85, 0.01), (r, h * 0.22), (r * 0.97, h * 0.52),
            (r * 0.72, h * 0.74), (r * 0.34, h * 0.86), (r * 0.20, h * 0.92),
            (r * 0.26, h * 0.97), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=14, lumpy=0.085, seed=seed)
    m.strand(sagline((x - r * 0.24, y, z + h * 0.885),
                     (x + r * 0.24, y, z + h * 0.885), 0.01, 5),
             0.009, M("mat_rope"), seg=6)


def small_crate(m, x, y, z, w=0.26, d=0.24, h=0.19, rz=0.0, mat=None):
    mat = mat or M("mat_i_crate")
    tb = M("mat_i_beam")
    ca, sa = math.cos(rz), math.sin(rz)
    def P(lx, ly, lz):
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz)
    for sy in (-1, 1):
        m.box(P(0, sy * (d / 2 - 0.012), h / 2), (w / 2, 0.012, h / 2), mat, rot=(0, 0, rz))
    for sx in (-1, 1):
        m.box(P(sx * (w / 2 - 0.012), 0, h / 2), (0.012, d / 2, h / 2), mat, rot=(0, 0, rz))
    m.box(P(0, 0, 0.012), (w / 2, d / 2, 0.012), mat, rot=(0, 0, rz))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box(P(sx * (w / 2 - 0.016), sy * (d / 2 - 0.016), h / 2),
                  (0.018, 0.018, h / 2), tb, rot=(0, 0, rz))


def coil_flat(m, x, y, z, r=0.13, n=4):
    rp = M("mat_rope")
    for i in range(n):
        rr = r - i * 0.021
        pts = [(x + rr * math.cos(2 * math.pi * k / 18),
                y + rr * math.sin(2 * math.pi * k / 18), z + 0.018 * i + 0.011)
               for k in range(19)]
        m.strand(pts, 0.0115, rp, seg=5)


def barrel(m, x, y, z=0.0, r=0.36, h=0.72, mat=None, bands=(0.06, 0.62),
           staves=18, band_mat=None):
    """A coopered barrel, staves placed individually so the silhouette is
    lumpy rather than a lathe."""
    mat = mat or M("mat_i_crate")
    band_mat = band_mat or M("mat_i_iron")
    for i in range(staves):
        a = 2 * math.pi * i / staves
        m.box((x + r * math.cos(a), y + r * math.sin(a), z + h / 2),
              (0.068, 0.022, h / 2), mat, rot=(0, 0, a + math.pi / 2), jitter=0.012)
    for hz in bands:
        m.lathe((x, y, z + hz), [(r * 1.03, 0), (r * 1.07, 0.012), (r * 1.07, 0.048),
                                 (r * 1.03, 0.058)], band_mat, seg=20)


def bucket(m, x, y, z, r=0.105, h=0.26, mat=None, band=True):
    mat = mat or M("mat_i_crate_b")
    m.lathe((x, y, z), [(0, 0), (r * 0.72, 0.0), (r * 0.81, 0.02),
                        (r, h - 0.02), (r * 1.03, h), (0, h)], mat, seg=14)
    if band:
        m.lathe((x, y, z + h * 0.92), [(r * 1.00, 0), (r * 1.04, 0.012),
                                       (r * 1.04, 0.040), (r * 1.00, 0.050)],
                M("mat_i_iron"), seg=14)


def net_hank(m, x, y, z, drop=0.66, span=0.30, depth=0.17, n=30, seed=0.0,
             mat=None, floats=2, face=-1.0, axis="y"):
    """A fishing net STORED on a peg: gathered at the top, bellied out, tied
    off low, with a short skirt of loose meshes below the tie.

    v5 hung nets as long strands off a ceiling beam and the critique was exact:
    parallel verticals at regular spacing read as a BEAD CURTAIN whatever the
    material does. The fix is not a better strand -- it is a different object.
    A hank is a BUNDLE: every strand leaves and returns to the same two gather
    points, so the silhouette closes into a lens with mass, the cross ties lie
    on a curved surface instead of a flat plane, and no two strands stay
    parallel for more than a few centimetres.

    `span` runs along `axis`, `depth` is the belly away from the support, and
    `face` is which way the belly leans. The same primitive hangs mail shirts
    in the armour shop -- a mail shirt on a peg is the same folded mass.
    """
    mat = mat or M("mat_i_net_d")
    rr = random.Random(int(seed * 811) & 0xffff)
    tie = drop * 0.66                       # height of the lower binding

    def W(u, v, dz):
        """local (along-support, out-from-support, down) -> world"""
        if axis == "x":
            return (x + u, y + face * v, z + dz)
        return (x + face * v, y + u, z + dz)

    cols = []
    for i in range(n):
        t = (i + 0.5) / n
        a = math.pi * t                     # 0..pi across the face of the hank
        u = span * 0.5 * math.cos(a) * rr.uniform(0.86, 1.08)
        # belly out in the middle of the bundle, folded shut at the edges, so
        # the section is a flattened teardrop rather than a plane
        v = depth * (0.28 + 0.72 * math.sin(a) ** 0.7) * rr.uniform(0.72, 1.06)
        pts = [W(0, 0, 0),
               W(u * 0.62, v * 0.42, -drop * 0.13),
               W(u, v, -drop * 0.33),
               W(u * 1.02, v * 1.02, -tie * 0.80),
               W(u * 0.30, v * 0.30, -tie),
               W(u * 0.78 + rr.uniform(-0.02, 0.02),
                 v * 0.72 + rr.uniform(-0.02, 0.02),
                 -drop * rr.uniform(0.86, 1.00))]
        m.strand(pts, 0.0060, mat, seg=4)
        cols.append(pts)
    # cross ties woven across the belly -- this is what makes it read as NET
    for f in (0.30, 0.48, 0.64):
        row = []
        for pts in cols:
            k = min(len(pts) - 1, max(1, int(f * (len(pts) - 1) + 0.5)))
            p = pts[k]
            row.append((p[0], p[1], p[2] + rr.uniform(-0.012, 0.012)))
        for a_, b_ in zip(row[:-1], row[1:]):
            m.strand([a_, ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2,
                           (a_[2] + b_[2]) / 2 - 0.024), b_], 0.0055, mat, seg=3)
    # bindings: a whipping of rope over the peg, and the tie holding the hank
    rp = M("mat_rope")
    for k in range(3):
        m.strand([W(0.052 * math.sin(2 * math.pi * t / 10),
                    0.030 * (1 + math.cos(2 * math.pi * t / 10)),
                    -0.028 - 0.026 * k) for t in range(11)], 0.0095, rp, seg=4)
    for k in range(2):
        m.strand([W(0.070 * math.sin(2 * math.pi * t / 10),
                    (0.040 + 0.010 * k) * (1 + math.cos(2 * math.pi * t / 10)),
                    -tie + 0.018 - 0.024 * k) for t in range(11)],
                 0.0090, rp, seg=4)
    # cork floats caught in the folds -- the silhouette's only hard shapes
    for k in range(floats):
        fa = math.pi * (0.30 + 0.44 * k)
        m.lathe(W(span * 0.40 * math.cos(fa), depth * 0.92,
                  -drop * (0.30 + 0.22 * k)),
                [(0, 0), (0.048, 0.024), (0.052, 0.052), (0, 0.074)],
                M("mat_i_crate_b"), seg=10, rot=rr.uniform(0, 3))


# ============================================================ edged weapons
#
# Everything in this block is built pointing along local +Z from its BUTT, so
# `rot` leans it in a rack, hangs it flat on a wall (rot=(pi/2,..)) or stands
# it in a barrel, without the caller doing trigonometry.

def sword(m, x, y, z, ln=0.92, rot=(0, 0, 0), blade=None, grip=None, fit=None,
          curve=0.0, wide=1.0):
    blade = blade or M("mat_i_steel")
    grip = grip or M("mat_i_leather")
    fit = fit or M("mat_i_brass")
    P = frame((x, y, z), rot)
    gl = ln * 0.20                       # hilt
    bl = ln - gl
    w = ln * 0.072 * wide
    m.sphere(P(0, 0, 0.012 * ln), w * 0.40, fit, seg=10, rings=6,
             scale=(1, 0.75, 0.85), rot=rot)
    m.cyl(P(0, 0, gl * 0.52), w * 0.26, gl * 0.70, grip, seg=10, rot=rot)
    for k in range(5):                   # grip wrap
        m.cyl(P(0, 0, gl * 0.24 + k * gl * 0.12), w * 0.29, 0.010, fit, seg=10, rot=rot)
    m.box(P(0, 0, gl), (w * 1.15, w * 0.20, w * 0.19), fit, rot=rot)
    m.plate(P(0, 0, gl + bl * 0.5), bl, w, w * 0.20, blade, rot=rot,
            taper=0.55, tip=0.24, bow=curve)
    # the fuller: a darker groove down the middle, which is what tells the eye
    # this is a blade and not a strip of tin
    m.plate(P(0, w * 0.11, gl + bl * 0.46), bl * 0.80, w * 0.26, w * 0.05,
            M("mat_i_steel_b"), rot=rot, taper=0.55, tip=0.10)


def dagger(m, x, y, z, ln=0.34, rot=(0, 0, 0), blade=None):
    sword(m, x, y, z, ln=ln, rot=rot, blade=blade or M("mat_i_steel"),
          fit=M("mat_i_bronze"), wide=1.25)


def axe(m, x, y, z, ln=0.86, rot=(0, 0, 0), head=None, haft=None, bearded=True):
    head = head or M("mat_i_steel")
    haft = haft or M("mat_i_beam")
    P = frame((x, y, z), rot)
    m.strand([P(0, 0, 0), P(0, 0, ln)], ln * 0.026, haft, seg=8, r2=ln * 0.032)
    hz = ln * 0.90
    m.box(P(0, 0, hz), (ln * 0.048, ln * 0.042, ln * 0.075), head, rot=rot)   # eye
    # the bit: a widening plate swept forward, plus a beard hanging below
    m.plate(P(ln * 0.135, 0, hz + ln * 0.010), ln * 0.24, ln * 0.20, ln * 0.030,
            head, rot=(rot[0], rot[1] + math.pi / 2, rot[2]), taper=1.9, tip=0.10)
    if bearded:
        m.plate(P(ln * 0.115, 0, hz - ln * 0.085), ln * 0.15, ln * 0.13,
                ln * 0.026, head,
                rot=(rot[0], rot[1] + math.pi / 2, rot[2]), taper=1.3, tip=0.25)
    m.cyl(P(-ln * 0.055, 0, hz), ln * 0.022, ln * 0.075, head, seg=8,
          rot=(rot[0], rot[1] + math.pi / 2, rot[2]))                       # poll
    m.cyl(P(0, 0, ln * 0.055), ln * 0.036, ln * 0.030, M("mat_i_iron"), seg=10, rot=rot)


def polearm(m, x, y, z, ln=2.30, rot=(0, 0, 0), kind="spear", head=None, haft=None):
    """Spear / halberd / boar-spear. Long enough to break the ceiling line,
    which is exactly why the weapon shop stands a barrel of them in the corner
    where the chandlery stood its oars."""
    head = head or M("mat_i_steel")
    haft = haft or M("mat_i_beam")
    P = frame((x, y, z), rot)
    m.strand([P(0, 0, 0), P(0, 0, ln)], ln * 0.011, haft, seg=9, r2=ln * 0.0095)
    for k in range(2):                    # langets down the haft below the head
        m.box(P(0, 0, ln * (0.90 - 0.03 * k)), (ln * 0.013, ln * 0.013, ln * 0.030),
              M("mat_i_iron"), rot=rot)
    if kind == "halberd":
        m.plate(P(0, 0, ln + ln * 0.055), ln * 0.15, ln * 0.024, ln * 0.010,
                head, rot=rot, taper=0.6, tip=0.4)
        m.plate(P(ln * 0.055, 0, ln * 0.965), ln * 0.105, ln * 0.085, ln * 0.011,
                head, rot=(rot[0], rot[1] + math.pi / 2, rot[2]), taper=1.7, tip=0.15)
        m.plate(P(-ln * 0.050, 0, ln * 0.965), ln * 0.085, ln * 0.038, ln * 0.010,
                head, rot=(rot[0], rot[1] - math.pi / 2, rot[2]), taper=0.5, tip=0.45)
    elif kind == "boar":
        m.plate(P(0, 0, ln + ln * 0.048), ln * 0.13, ln * 0.045, ln * 0.012,
                head, rot=rot, taper=0.35, tip=0.35)
        m.box(P(0, 0, ln * 0.985), (ln * 0.042, ln * 0.010, ln * 0.008),
              M("mat_i_iron"), rot=rot)          # the cross-stop
    else:
        m.plate(P(0, 0, ln + ln * 0.042), ln * 0.115, ln * 0.032, ln * 0.010,
                head, rot=rot, taper=0.45, tip=0.42)
    m.cyl(P(0, 0, ln * 0.020), ln * 0.014, ln * 0.040, M("mat_i_iron"), seg=8, rot=rot)


def bow(m, x, y, z, ln=1.30, rot=(0, 0, 0), mat=None, recurve=0.16):
    """A stave bow hung by its grip. The string is the readable bit: one
    dead-straight bright line against the curve of the limbs."""
    mat = mat or M("mat_i_beam")
    P = frame((x, y, z), rot)
    pts, tips = [], []
    n = 14
    for i in range(n + 1):
        t = i / n - 0.5
        bend = recurve * (1 - 4 * t * t) + recurve * 1.5 * (t ** 4) * 16
        pts.append(P(bend, 0, t * ln))
    m.strand(pts, ln * 0.014, mat, seg=6)
    for s in (-1, 1):                                    # horn nocks
        m.cyl(P(recurve * 0.35, 0, s * ln * 0.49), ln * 0.014, ln * 0.045,
              M("mat_i_bronze"), seg=8, rot=rot)
    m.strand([P(recurve * 0.30, 0, -ln * 0.485), P(recurve * 0.30, 0, ln * 0.485)],
             ln * 0.0045, M("mat_i_label"), seg=3)
    for k in range(6):                                   # grip wrap
        m.cyl(P(recurve * 0.98, 0, (k - 2.5) * ln * 0.028), ln * 0.020, ln * 0.022,
              M("mat_i_leather"), seg=10, rot=rot)


def quiver(m, x, y, z, ln=0.52, rot=(0, 0, 0), mat=None, n=8):
    mat = mat or M("mat_i_leather")
    P = frame((x, y, z), rot)
    r = ln * 0.16
    m.lathe(P(0, 0, 0), [(0, 0), (r * 0.78, 0), (r * 0.86, ln * 0.10),
                         (r, ln * 0.75), (r * 1.03, ln)], mat, seg=14)
    for k in (0.18, 0.62, 0.94):
        m.lathe(P(0, 0, ln * k), [(r * 1.02, 0), (r * 1.08, 0.010),
                                  (r * 1.08, 0.034), (r * 1.02, 0.044)],
                M("mat_i_bronze"), seg=14)
    rr = random.Random(int(abs(x * 1000 + y * 17)) & 0xffff)
    for i in range(n):
        a = 2 * math.pi * i / n
        ox_, oy_ = r * 0.62 * math.cos(a), r * 0.62 * math.sin(a)
        sh = ln * rr.uniform(0.50, 0.66)
        m.strand([P(ox_, oy_, ln * 0.9), P(ox_ * 1.5, oy_ * 1.5, ln + sh)],
                 ln * 0.011, M("mat_i_beam"), seg=4)
        for f in range(3):
            fa = 2 * math.pi * f / 3
            m.plate(P(ox_ * 1.45, oy_ * 1.45, ln + sh * 0.86), sh * 0.24,
                    ln * 0.030, ln * 0.004,
                    M("mat_i_feather") if i % 3 else M("mat_i_apple"),
                    rot=(rot[0], rot[1], rot[2] + fa), taper=0.7)


def blade_bracket(m, x, y, z, span=0.34, rot=(0, 0, 0), mat=None, depth=0.13):
    """A pair of wall brackets a blade or a polearm rests across."""
    mat = mat or M("mat_i_iron")
    P = frame((x, y, z), rot)
    for s in (-1, 1):
        m.strand([P(0, 0, s * span / 2), P(depth, 0, s * span / 2)], 0.012, mat, seg=4)
        m.strand([P(depth, 0, s * span / 2), P(depth * 0.82, 0, s * span / 2 + s * 0.045)],
                 0.011, mat, seg=3)


def whetstone(m, x, y, z, rot=0.0, mat=None):
    mat = mat or M("mat_i_stone")
    m.box((x, y, z + 0.022), (0.105, 0.038, 0.022), mat, rot=(0, 0, rot))
    m.box((x - 0.005, y, z + 0.045), (0.092, 0.030, 0.004), M("mat_i_steel_b"),
          rot=(0.03, 0, rot))


def oil_rag(m, x, y, z, r=0.10, seed=0.0, mat=None):
    """A rag dropped on a counter: three overlapping lumpy discs. Reads as
    cloth because nothing about it is straight."""
    mat = mat or M("mat_i_canvas")
    rr = random.Random(int(seed * 613) & 0xffff)
    for k in range(3):
        m.lathe((x + rr.uniform(-0.03, 0.03), y + rr.uniform(-0.03, 0.03),
                 z + 0.004 * k),
                [(0, 0), (r * 0.55, 0.006), (r * rr.uniform(0.8, 1.0), 0.014),
                 (r * 0.72, 0.020), (0, 0.022)],
                mat, seg=12, lumpy=0.22, seed=seed + k, aspect=(1.0, 0.78),
                rot=rr.uniform(0, 3))


def wrapped_blade(m, x, y, z, ln=0.78, rot=(0, 0, 0)):
    """A sword half-wrapped in oiled cloth, mid-job on the counter. The bare
    half is the only mirror-bright thing at counter height, so it points at
    the transaction spot."""
    P = frame((x, y, z), rot)
    sword(m, x, y, z, ln=ln, rot=rot)
    for k in range(9):                       # the cloth, wound on
        t = 0.30 + k * 0.070
        m.lathe(P(0, 0, ln * t), [(ln * 0.052, 0), (ln * 0.062, ln * 0.012),
                                  (ln * 0.060, ln * 0.055), (ln * 0.050, ln * 0.066)],
                M("mat_i_canvas"), seg=10, aspect=(1.0, 0.42), rot=k * 0.4)
    m.strand([P(-ln * 0.06, 0, ln * 0.31), P(ln * 0.06, ln * 0.03, ln * 0.28)],
             ln * 0.010, M("mat_rope"), seg=3)


def grindstone(m, x, y, z=0.0, rot=0.0, r=0.30):
    """A treadle grindstone: wheel, frame, trough, and a foot board linked by
    a pitman rod. It is the weapon shop's answer to the chandlery's tapped
    barrel -- one prop that states the premise."""
    P = frame((x, y, z), (0, 0, rot))
    wood, ir, st = M("mat_i_beam"), M("mat_i_iron"), M("mat_i_stone")
    ax = 0.62                                   # axle height
    for s in (-1, 1):                           # A-frame legs
        for e in (-1, 1):
            m.strand([P(s * 0.30 + e * 0.10, e * 0.20, 0.0),
                      P(s * 0.30, 0.0, ax)], 0.030, wood, seg=6)
        m.box(P(s * 0.30, 0, ax), (0.048, 0.062, 0.052), wood, rot=(0, 0, rot))
    m.box(P(0, 0, 0.20), (0.30, 0.030, 0.026), wood, rot=(0, 0, rot))
    # The stone, as a VERTICAL disc. A lathe revolves about local Z, which
    # made the first pass a grindstone lying flat like a table top; the wheel
    # has to be a cylinder whose axis runs along the axle instead. The skin
    # then yaws the whole rig so the disc faces the camera -- a wheel seen
    # edge-on is a plank.
    AXIS = (0, math.pi / 2, rot)
    m.cyl(P(0, 0, ax), r, 0.070, st, seg=26, rot=AXIS)
    m.cyl(P(0, 0, ax), r * 0.965, 0.086, st, seg=26, rot=AXIS)   # worn belly
    m.cyl(P(0, 0, ax), r * 0.30, 0.096, M("mat_i_iron"), seg=16, rot=AXIS)
    m.strand([P(0.30, 0, ax), P(0.44, 0.10, ax)], 0.016, ir, seg=4)     # crank
    m.strand([P(0.44, 0.10, ax), P(0.44, 0.10, 0.16)], 0.013, wood, seg=5)  # pitman
    m.box(P(0.26, 0.16, 0.10), (0.24, 0.10, 0.020), wood, rot=(0.05, 0, rot))
    m.box(P(0.02, 0.16, 0.055), (0.030, 0.030, 0.055), wood, rot=(0, 0, rot))
    # water trough under the wheel, and the drip bucket
    m.lathe(P(0, 0, 0.28), [(0, 0), (r * 0.86, 0), (r * 0.92, 0.02),
                            (r * 0.96, 0.14), (0, 0.145)],
            M("mat_i_crate_b"), seg=16, aspect=(0.55, 1.0))
    m.lathe(P(0, 0, 0.405), [(r * 0.94, 0), (r * 0.99, 0.010),
                             (r * 0.99, 0.030), (r * 0.94, 0.038)],
            ir, seg=16, aspect=(0.55, 1.0))
    m.lathe(P(0, 0, 0.395), [(0, 0), (r * 0.86, 0)], M("mat_i_water_d"), seg=16,
            aspect=(0.55, 1.0))


def forge_nook(m, x, y, z=0.0, rot=0.0, ember=True, energy=340.0):
    """NOT a smithy -- a shop-corner forge: a raised hearth the size of a
    hearthstone with a hood, live coals, a bellows and tongs. It exists to put
    a SECOND warm pool in the room (the counter has the first) and to say a
    smith works here without turning the retail floor into a workshop.

    Kit lesson 14: the practical goes at the MOUTH of the fire, not at the
    physical coal bed, or the geometry eats it.
    """
    P = frame((x, y, z), (0, 0, rot))
    st, ir, wood = M("mat_i_stone"), M("mat_i_iron"), M("mat_i_beam")
    fs = M("mat_i_forgestone")     # sooted firebrick -- see the material note
    # stone plinth, coursed
    for k in range(4):
        m.box(P(0, 0, 0.085 + k * 0.17), (0.44 - 0.012 * k, 0.34 - 0.010 * k, 0.085),
              st, rot=(0, 0, rot), jitter=0.012)
    # The hearthstone and the bowl are the ONLY surfaces the camera can see of
    # this prop -- it clears the counter's back edge by a few centimetres, so
    # everything below z~0.64 is hidden. They are also the surfaces nearest the
    # coals. Dark firebrick here is what lets the fire be the brightest thing.
    m.box(P(0, 0, 0.70), (0.46, 0.36, 0.030), fs, rot=(0, 0, rot))
    # the fire bowl
    m.lathe(P(0, 0.02, 0.716), [(0.30, 0), (0.28, -0.018), (0.20, -0.050),
                                (0.10, -0.062), (0, -0.066)], fs, seg=18,
            aspect=(1.0, 0.80))
    rr = random.Random(int(abs(x * 733 + y * 91)) & 0xffff)
    for i in range(26):
        a = rr.uniform(0, 6.283)
        rad = rr.uniform(0, 0.21)
        # v4: 0.45 lit fewer than half the coals and the bed read as a grey
        # dish with a few sparks in it. The draw ORDER is untouched (the
        # rr.random() call still happens) -- only the threshold moved, so every
        # coal keeps its v3 position and size and the shared stream is intact.
        hot = rr.random() < 0.68
        m.sphere(P(rad * math.cos(a), 0.02 + rad * math.sin(a) * 0.8,
                   0.672 + rr.uniform(0, 0.045) + rad * 0.10),
                 rr.uniform(0.026, 0.042),
                 M("mat_i_ember") if (hot and ember) else M("mat_i_coal"),
                 seg=8, rings=6, rot=(rr.uniform(0, 3), 0, rr.uniform(0, 3)))
    # v4: a hotter CORE to the bed. The centre of a working forge is the one
    # place that is genuinely incandescent, and giving it its own cluster of
    # larger coals grows the glowing AREA -- which is what buys presence --
    # without pushing the emission into the AgX shoulder, where any colour
    # comes back cream (kit finding 21). Private rng: nothing downstream moves.
    if ember:
        rc = random.Random(int(abs(x * 733 + y * 91)) & 0xffff ^ 0x5A5A)
        for i in range(13):
            a = rc.uniform(0, 6.283)
            rad = rc.uniform(0, 0.125)
            m.sphere(P(rad * math.cos(a), 0.02 + rad * math.sin(a) * 0.8,
                       0.678 + rc.uniform(0, 0.030) + rad * 0.10),
                     rc.uniform(0.038, 0.058), M("mat_i_ember"),
                     seg=8, rings=6, rot=(rc.uniform(0, 3), 0, rc.uniform(0, 3)))
    # hood + flue, in dark sheet iron. Kept SMALL and open at the front: a
    # full conical hood at this scale is a metre-wide black funnel parked in
    # front of the back shelving, which is what the first weapon-shop pass
    # did. A canopy over the back half plus a slim flue says "this vents"
    # without taking the wall.
    m.arc_lathe(P(0, 0.16, 0.95), [(0.40, 0), (0.34, 0.10), (0.17, 0.24),
                                   (0.13, 0.30)], ir, seg=12,
                a0=-0.30, a1=3.44, aspect=(1.0, 0.72))
    m.lathe(P(0.0, 0.16, 1.24), [(0.13, 0), (0.135, 0.010), (0.135, 0.52),
                                 (0.13, 0.54)], ir, seg=12)
    # bellows slung on the side
    m.plate(P(-0.50, -0.02, 0.62), 0.46, 0.30, 0.055, M("mat_i_leather"),
            rot=(0, math.pi / 2, rot), taper=0.42)
    m.plate(P(-0.50, -0.02, 0.68), 0.44, 0.28, 0.028, wood,
            rot=(0, math.pi / 2, rot), taper=0.42)
    m.strand([P(-0.30, -0.02, 0.66), P(-0.10, -0.02, 0.70)], 0.022, wood, seg=4)
    m.strand([P(-0.72, -0.02, 0.70), P(-0.86, -0.02, 1.05)], 0.022, wood, seg=4)
    # tongs and a poker stood in the corner
    for k, (dx, lean) in enumerate(((0.40, 0.22), (0.47, 0.30))):
        m.strand([P(dx, -0.30, 0.0), P(dx - lean * 0.5, -0.30 + 0.06, 1.02)],
                 0.014, ir, seg=6)
        m.strand([P(dx - lean * 0.5, -0.30 + 0.06, 1.02),
                  P(dx - lean * 0.62, -0.30 + 0.08, 1.16)], 0.010, ir, seg=3)
    # the quench tub
    m.lathe(P(0.62, -0.16, 0.0), [(0, 0), (0.19, 0), (0.205, 0.03),
                                  (0.225, 0.34), (0.228, 0.36), (0, 0.36)],
            M("mat_i_crate_b"), seg=16)
    m.lathe(P(0.62, -0.16, 0.30), [(0.226, 0), (0.234, 0.012), (0.234, 0.040),
                                   (0.226, 0.050)], ir, seg=16)
    m.lathe(P(0.62, -0.16, 0.31), [(0, 0), (0.21, 0.0)], M("mat_i_water_d"), seg=16)
    if ember:
        # WHERE these sit matters more than how hard they are driven. v3 put
        # FORGE_glow 0.09 above and 0.16 in front of the coal bed and FORGE_up
        # 0.18 directly over it: the two lamps that were supposed to be the
        # fire's light on the ROOM were instead frying the bed itself, and a
        # measurement of the 100x30px strip of bowl the camera can actually see
        # over the counter came back 93% clipped to white in v3 -- the reason
        # the note reads "ember glow is weak" is that there was no glow there
        # at all, only a hole. Both lamps move away from the bed: the glow to
        # the hood MOUTH, throwing forward into the room, and the up-light into
        # the hood, where it models the canopy and the flue.
        # and the wattage comes down with the albedo. A POINT at 400W half a
        # metre from a surface delivers ~160 W/m^2; nothing with a stone albedo
        # survives that through AgX. 170W at ~0.6m onto dark firebrick lands
        # the hearthstone in the upper midtones, where it can still be
        # out-valued by the coals sitting in it -- which is the whole picture.
        point("FORGE_glow", P(0.0, -0.42, 1.10), energy, (1.0, 0.42, 0.13),
              radius=0.16)
        point("FORGE_up", P(0.0, 0.06, 1.30), energy * 0.30, (1.0, 0.52, 0.20),
              radius=0.10)
        # v4: WHY the ember glow read weak. Not for want of light -- the nook
        # was already the brightest thing in its half of the frame, and the
        # first v4 attempt (a big top-down pool at z=2.05) simply washed the
        # hood, the flue and the back shelving to near-white and made it read
        # weaker still. The nook was short of CONTRAST and of COLOUR, not of
        # level: everything around the coals sat in the same pale band as the
        # coals, so nothing said fire.
        #
        # So the light goes sideways instead of up. The counter's back face is
        # 1.05 tall and blocks anything below it, so the pool that lands on the
        # counter TOP -- the surface the camera sees most of -- has to be
        # thrown from above that line and aimed forward and down.
        area("FORGE_pool", P(0.0, -0.55, 1.58), energy * 0.32,
             (1.0, 0.44, 0.16), size=1.50, size_y=0.90,
             rot=(math.radians(-48), 0, rot))
        # the keep floor is hidden behind the counter for most of its width,
        # but the aisle gap off the counter's left end is open to the camera,
        # and that is where a firelit floor can actually be seen.
        area("FORGE_floor", P(-0.85, -0.72, 0.34), energy * 0.22,
             (1.0, 0.40, 0.14), size=1.20, size_y=0.90,
             rot=(math.radians(-10), 0, rot))
        # a wisp off the flue. The forge is the only thing in the room that
        # burns solid fuel, and a plume above the flue head is what says so.
        # Kept thin: at 0.58 it hazed the whole bay of shelving behind it,
        # which is kit finding 12 arriving on schedule.
        smoke_wisp("FORGE_SMOKE", P(0.04, 0.18, 2.32), (0.52, 0.46, 1.20),
                   color=(0.74, 0.52, 0.36), density=0.30, seed=2.7)


# ============================================================== armour kit

def helm(m, x, y, z, r=0.115, rot=(0, 0, 0), mat=None, kind="nasal"):
    mat = mat or M("mat_i_steel")
    P = frame((x, y, z), rot)
    m.lathe(P(0, 0, 0), [(r * 1.02, 0), (r * 1.05, r * 0.10), (r, r * 0.55),
                         (r * 0.82, r * 1.05), (r * 0.46, r * 1.42),
                         (0, r * 1.52)], mat, seg=16, orient=rot)
    m.lathe(P(0, 0, -r * 0.06), [(r * 1.02, 0), (r * 1.16, r * 0.05),
                                 (r * 1.16, r * 0.12), (r * 1.00, r * 0.16)],
            M("mat_i_steel_b"), seg=16, orient=rot)            # brow band
    if kind == "nasal":
        m.plate(P(0, -r * 1.02, r * 0.06), r * 0.62, r * 0.30, r * 0.10, mat,
                rot=(rot[0] + 0.12, rot[1], rot[2]), taper=0.7, tip=0.25)
    elif kind == "great":
        m.box(P(0, -r * 0.92, r * 0.34), (r * 0.62, r * 0.12, r * 0.055),
              M("mat_i_steel_b"), rot=rot)                    # eye slot
        m.box(P(0, -r * 0.92, r * 0.66), (r * 0.62, r * 0.12, r * 0.055),
              M("mat_i_steel_b"), rot=rot)
    elif kind == "crest":
        for k in range(9):
            m.plate(P(0, (k - 4) * r * 0.22, r * 1.50 + r * 0.16 *
                      math.sin(math.pi * (k + 0.5) / 9)),
                    r * 0.34, r * 0.09, r * 0.05, M("mat_i_apple"),
                    rot=(rot[0], rot[1], rot[2]))
    # the mail aventail: a short skirt of rings round the back of the neck
    m.arc_lathe(P(0, 0, -r * 0.05), [(r * 1.00, 0), (r * 1.05, -r * 0.30),
                                     (r * 1.10, -r * 0.62)],
                M("mat_i_mail"), seg=14, a0=0.35, a1=2.79, orient=rot)


def shield_round(m, x, y, z, r=0.31, rot=(0, 0, 0), face=None, rim=None,
                 boss=True, straps=False):
    """A dished round shield. The dish is what catches a rim highlight all the
    way round, which is the difference between a shield and a dinner plate.

    Every revolve here passes `orient=rot`. Miss one and that part stays flat
    in world space while the rest tilts -- the failure looks like a modelling
    mistake but is really an axis-convention one.
    """
    face = face or M("mat_i_oxblood")
    rim = rim or M("mat_i_steel_b")
    P = frame((x, y, z), rot)
    m.lathe((x, y, z), [(0, -r * 0.16), (r * 0.42, -r * 0.10),
                        (r * 0.78, -r * 0.035), (r * 0.96, 0)],
            face, seg=22, orient=rot)
    m.lathe((x, y, z), [(0, -r * 0.055), (r * 0.90, -r * 0.055),
                        (r * 0.96, -r * 0.035), (r * 0.96, -r * 0.005),
                        (0, 0)], M("mat_i_beam"), seg=22, orient=rot)
    m.lathe((x, y, z), [(r * 0.955, -r * 0.030), (r * 1.005, -r * 0.010),
                        (r * 1.005, r * 0.045), (r * 0.955, r * 0.065)],
            rim, seg=24, orient=rot)
    for k in range(10):                                       # rim rivets
        a = 2 * math.pi * k / 10
        m.sphere(P(r * 0.985 * math.cos(a), r * 0.985 * math.sin(a), r * 0.02),
                 r * 0.030, rim, seg=8, rings=5)
    if boss:
        m.lathe((x, y, z), [(r * 0.30, r * 0.015), (r * 0.31, r * 0.045),
                            (r * 0.24, r * 0.115), (r * 0.13, r * 0.185),
                            (0, r * 0.215)], M("mat_i_steel_bright"), seg=16,
                orient=rot)
    if straps:
        for s_ in (-1, 1):
            m.plate(P(0, s_ * r * 0.34, -r * 0.10), r * 1.3, r * 0.16, r * 0.035,
                    M("mat_i_leather"), rot=(rot[0], rot[1] + math.pi / 2, rot[2]))


def mail_shirt(m, x, y, z, ln=0.72, rot=(0, 0, 0), mat=None, sleeve=0.26,
               w_scale=0.26):
    """A hauberk hung on a peg or a bar. Modelled as a body that FLARES to the
    hem and hangs a little off-square, because a mail shirt has real weight and
    a symmetrical tube reads as a bin."""
    mat = mat or M("mat_i_mail")
    P = frame((x, y, z), rot)
    w = ln * w_scale
    m.lathe(P(0, 0, -ln), [(w * 0.42, 0), (w * 1.06, ln * 0.10),
                           (w * 1.12, ln * 0.34), (w * 1.02, ln * 0.62),
                           (w * 0.92, ln * 0.86), (w * 0.80, ln * 0.97),
                           (w * 0.66, ln)], mat, seg=16, aspect=(1.0, 0.58),
            lumpy=0.055, seed=x * 3.1, orient=rot)
    # the hem, cut in a ragged scallop so the bottom edge is not a ring
    rr = random.Random(int(abs(x * 977 + z * 131)) & 0xffff)
    for k in range(18):
        a = 2 * math.pi * k / 18
        m.strand([P(w * 1.06 * math.cos(a), w * 1.06 * 0.58 * math.sin(a), -ln),
                  P(w * 1.02 * math.cos(a), w * 1.02 * 0.58 * math.sin(a),
                    -ln - rr.uniform(0.012, 0.045))], ln * 0.016, mat, seg=3)
    for s_ in (-1, 1):                                       # sleeves
        m.lathe(P(s_ * w * 0.98, 0, -sleeve), [(w * 0.40, 0), (w * 0.44, sleeve * 0.2),
                                               (w * 0.50, sleeve)], mat, seg=12,
                aspect=(0.85, 0.62), orient=rot)
    # The collar and the shoulder yoke, in plain plate. Without a hard top the
    # whole thing reads as a hanging sack; the flat pauldrons give it a pair of
    # square shoulders, which is the entire difference between "mail shirt" and
    # "laundry".
    m.lathe(P(0, 0, 0), [(w * 0.72, -ln * 0.03), (w * 0.46, ln * 0.02),
                         (w * 0.42, ln * 0.05)], M("mat_i_steel_b"), seg=14,
            aspect=(1.0, 0.58), orient=rot)
    for s_ in (-1, 1):
        m.arc_lathe(P(s_ * w * 0.74, 0, -ln * 0.10),
                    [(w * 0.44, 0), (w * 0.48, ln * 0.07), (w * 0.40, ln * 0.13)],
                    M("mat_i_steel"), seg=10, a0=-2.9, a1=0.3,
                    aspect=(1.0, 0.62), orient=rot)


def breastplate(m, x, y, z, h=0.46, rot=(0, 0, 0), mat=None):
    mat = mat or M("mat_i_steel")
    P = frame((x, y, z), rot)
    w = h * 0.42
    m.arc_lathe(P(0, 0, 0), [(w * 0.86, 0), (w * 1.00, h * 0.28),
                             (w * 1.02, h * 0.52), (w * 0.92, h * 0.78),
                             (w * 0.72, h * 0.96), (w * 0.60, h)],
                mat, seg=16, a0=-2.62, a1=-0.52, aspect=(1.0, 0.72))
    m.arc_lathe(P(0, 0, 0), [(w * 0.86, 0), (w * 0.98, h * 0.26),
                             (w * 0.98, h * 0.55), (w * 0.86, h * 0.80),
                             (w * 0.68, h)],
                M("mat_i_steel_b"), seg=14, a0=0.52, a1=2.62, aspect=(1.0, 0.72))
    # fauld: two overlapping skirt lames under the waist
    for k in range(2):
        m.arc_lathe(P(0, 0, -h * (0.09 + 0.09 * k)),
                    [(w * (0.92 + 0.05 * k), 0), (w * (0.98 + 0.05 * k), h * 0.075)],
                    mat, seg=16, a0=-2.70, a1=0.44, aspect=(1.0, 0.74))
    for s in (-1, 1):                                        # pauldrons
        m.arc_lathe(P(s * w * 0.90, 0, h * 0.92), [(w * 0.44, 0), (w * 0.48, h * 0.10),
                                                   (w * 0.40, h * 0.20)],
                    mat, seg=12, a0=-3.0, a1=0.3, aspect=(1.0, 0.80))


def armor_stand(m, x, y, z=0.0, rot=0.0, h=1.62, full=True, hero=0.0):
    """The hero prop: a full harness on a stand, the armour shop's answer to
    the chandlery's barrel of oars. Head height, dead centre of its bay, and
    the only thing in the room with a human silhouette.

    `hero` > 0 turns the stand into the room's SECOND read, after the counter:
    it gets a low display dais to stand on and its own three-lamp rig (rake,
    rim, floor bounce), scaled by the value passed. The v3 art gate's note was
    that the harness had the silhouette but no MOMENT -- it sat in the same
    even light as the crates behind it, and polished steel with no bright
    source to mirror is just a grey shape.
    """
    P = frame((x, y, z), (0, 0, rot))
    wood, st = M("mat_i_beam"), M("mat_i_steel")
    if hero:
        # Display dais. Kept low and pushed slightly back: a 3/4 camera this
        # close to the front-left corner runs the dais's front edge off the
        # bottom of the frame, and a plinth you only see the back half of
        # still reads as a plinth -- one you see none of does not.
        dz, dr = 0.115, 0.50
        m.lathe((x, y + 0.07, z), [(0, 0), (dr, 0), (dr, dz * 0.62),
                                   (dr * 0.94, dz * 0.86), (dr * 0.90, dz),
                                   (0, dz)], wood, seg=20)
        m.lathe((x, y + 0.07, z + dz * 0.60),
                [(dr * 1.012, 0), (dr * 1.028, 0.012), (dr * 1.028, 0.030),
                 (dr * 1.012, 0.042)], M("mat_i_steelblue_b"), seg=20)
        z += dz
        P = frame((x, y, z), (0, 0, rot))
    m.lathe(P(0, 0, 0), [(0, 0), (0.30, 0), (0.32, 0.030), (0.20, 0.055),
                         (0.10, 0.070), (0, 0.075)], wood, seg=18)   # base
    m.cyl(P(0, 0, h * 0.44), 0.036, h * 0.82, wood, seg=12, rot=(0, 0, rot))
    m.box(P(0, 0, h * 0.80), (0.24, 0.045, 0.030), wood, rot=(0, 0, rot))  # shoulder bar
    breastplate(m, *P(0, 0, h * 0.50), h=h * 0.32, rot=(0, 0, rot), mat=st)
    if full:
        helm(m, *P(0, 0, h * 0.905), r=h * 0.075, rot=(0, 0, rot), kind="great")
        for s in (-1, 1):                                    # arms
            m.lathe(P(s * h * 0.145, 0, h * 0.60), [(h * 0.036, 0), (h * 0.040, -h * 0.10),
                                                    (h * 0.032, -h * 0.20)],
                    st, seg=10, aspect=(1.0, 0.80))
            m.lathe(P(s * h * 0.150, 0, h * 0.335), [(h * 0.030, 0), (h * 0.034, -h * 0.09),
                                                     (h * 0.028, -h * 0.16)],
                    M("mat_i_steel_b"), seg=10, aspect=(1.0, 0.80))
            # greaves standing at the foot of the post
            m.arc_lathe(P(s * 0.10, 0, 0.075), [(0.062, 0), (0.068, 0.14),
                                                (0.058, 0.30), (0.050, 0.40)],
                        st, seg=12, a0=-2.5, a1=0.6, aspect=(1.0, 0.78))
        mail_shirt(m, *P(0, 0, h * 0.545), ln=h * 0.30, rot=(0, 0, rot))
    m.strand([P(-0.26, 0.0, h * 0.80), P(-0.34, 0.02, h * 0.46)], 0.012,
             M("mat_i_leather"), seg=4)
    if hero:
        aim = (x + 0.02, y - 0.02, z + h * 0.58)
        # RAKE. Over the camera's left shoulder and well above the harness, so
        # it models the breastplate's curve instead of flattening it, and drops
        # the stand's own shadow away from the lens. Camera-invisible: the
        # motivating source is the floor lantern already standing beside it.
        #
        # It is a SPOT, not an area. The first pass used a 110W area here and
        # lifted the entire front-left bay 2.3x -- the shields, the peg rail
        # and the barrel behind all came up with the harness, so the harness
        # was no more featured than before, just brighter. A cone that falls
        # off inside the bay is the whole point of a spotlight moment.
        spot("STAND_rake", (x - 0.62, y - 1.55, z + 2.05), aim, 24.0 * hero,
             (1.0, 0.63, 0.33), cone=52.0, blend=0.60, radius=0.16)
        # RIM. Polished steel is a mirror -- it has no highlight of its own, it
        # can only show you a light that is already there. A small hot kicker
        # high and BEHIND the harness (opposite the camera) is what puts a lit
        # edge down the helm, the shoulder bar and the pauldrons and lifts the
        # silhouette off the wall behind it.
        spot("STAND_rim", (x - 0.48, y + 1.20, z + 1.62), aim, 11.0 * hero,
             (1.0, 0.80, 0.58), cone=46.0, blend=0.50, radius=0.08)
        # and a low warm bounce off the dais, so the greaves and the underside
        # of the breastplate do not go to black under the rake
        area("STAND_bounce", (x + 0.34, y - 0.72, z + 0.16), 7.0 * hero,
             (1.0, 0.72, 0.46), size=0.70,
             look_at=(x, y, z + h * 0.30))


def leather_roll(m, x, y, z, ln=0.34, r=0.062, rot=(0, 0, 0), mat=None, n=1):
    mat = mat or M("mat_i_leather")
    P = frame((x, y, z), rot)
    for k in range(n):
        oy = (k - (n - 1) / 2) * r * 2.15
        m.cyl(P(0, oy, r), r, ln, mat, seg=14, rot=(rot[0], rot[1] + math.pi / 2,
                                                   rot[2]))
        m.lathe(P(ln * 0.5, oy, r), [(r * 0.99, 0), (r * 1.02, 0.010)],
                M("mat_i_leather_b"), seg=14, rot=0.0)
        for s in (-1, 1):
            m.strand([P(s * ln * 0.28, oy - r * 1.02, r),
                      P(s * ln * 0.28, oy + r * 1.02, r)], 0.008,
                     M("mat_i_leather_b"), seg=3)


def buckle_tray(m, x, y, z, w=0.20, d=0.15, rot=0.0, n=14):
    wood, br = M("mat_i_shelf"), M("mat_i_bronze")
    m.box((x, y, z + 0.012), (w, d, 0.010), wood, rot=(0, 0, rot))
    for s in (-1, 1):
        m.box((x + s * w * math.cos(rot), y + s * w * math.sin(rot), z + 0.026),
              (0.011, d, 0.026), wood, rot=(0, 0, rot))
        m.box((x - s * d * math.sin(rot), y + s * d * math.cos(rot), z + 0.026),
              (w, 0.011, 0.026), wood, rot=(0, 0, rot))
    rr = random.Random(int(abs(x * 401 + y * 79)) & 0xffff)
    for i in range(n):
        bx = x + rr.uniform(-w * 0.8, w * 0.8)
        by = y + rr.uniform(-d * 0.7, d * 0.7)
        a = rr.uniform(0, 3.14)
        s = rr.uniform(0.016, 0.028)
        m.lathe((bx, by, z + 0.024), [(s * 0.72, 0), (s, 0.005), (s, 0.010),
                                      (s * 0.72, 0.014)], br, seg=8,
                aspect=(1.0, 0.72), rot=a)
        m.strand([(bx - s * math.cos(a), by - s * math.sin(a), z + 0.029),
                  (bx + s * math.cos(a), by + s * math.sin(a), z + 0.029)],
                 0.0035, br, seg=3)


def gauntlet(m, x, y, z, rot=(0, 0, 0), mat=None, ln=0.20):
    mat = mat or M("mat_i_steel")
    P = frame((x, y, z), rot)
    m.arc_lathe(P(0, 0, 0), [(ln * 0.30, 0), (ln * 0.34, ln * 0.30),
                             (ln * 0.30, ln * 0.55)], mat, seg=12,
                a0=-2.8, a1=0.4, aspect=(1.0, 0.70))
    for k in range(4):
        m.plate(P(0, -ln * 0.10, ln * (0.62 + 0.11 * k)), ln * 0.10, ln * 0.42,
                ln * 0.035, mat, rot=(rot[0] + 0.20, rot[1], rot[2]), taper=0.86)
    m.lathe(P(0, 0, -ln * 0.20), [(ln * 0.32, 0), (ln * 0.36, ln * 0.05),
                                  (ln * 0.34, ln * 0.20)],
            M("mat_i_leather"), seg=12, aspect=(1.0, 0.70))


# ============================================================== set pieces
#
# Bigger assemblies a skin picks from. They take a world position so a skin
# table can move them, but their internal proportions are fixed -- these are
# the pieces that carry the room's silhouette and they were tuned against the
# camera, not against the floor plan.

def oar_stand(m, x, y, z=0.0, n=7, tall=2.7):
    """The chandlery's barrel of oars, poles and boat hooks: the tallest
    silhouette in the room and the frame's left-hand repoussoir."""
    stv, ir = M("mat_i_oxblood"), M("mat_i_iron")
    rb, hb = 0.40, 0.78
    for i in range(18):
        a = 2 * math.pi * i / 18
        rr = rb * (1.0 + 0.055 * math.sin(math.pi * 0.5))
        m.box((x + rr * math.cos(a), y + rr * math.sin(a), hb / 2),
              (0.075, 0.024, hb / 2), stv, rot=(0, 0, a + math.pi / 2), jitter=0.012)
    for hz in (0.07, 0.40, 0.71):
        m.lathe((x, y, hz), [(rb * 1.02, 0), (rb * 1.06, 0.012),
                             (rb * 1.06, 0.052), (rb * 1.02, 0.064)], ir, seg=20)
    poles = [(-0.17, -0.10, 2.44, 0.055, "oar"), (0.02, -0.16, 2.62, 0.052, "oar"),
             (0.17, -0.02, 2.28, 0.048, "pole"), (-0.05, 0.14, 2.72, 0.050, "oar"),
             (0.13, 0.18, 2.16, 0.044, "hook"), (-0.19, 0.08, 2.36, 0.046, "pole"),
             (0.00, 0.00, 2.55, 0.050, "pole")]
    wood = [M("mat_i_beam"), M("mat_i_shelf"), M("mat_i_counter")]
    for i, (dx, dy, ln, r, kind) in enumerate(poles):
        lean_x = R.uniform(-0.10, 0.10)
        lean_y = R.uniform(-0.08, 0.08)
        base = Vector((x + dx, y + dy, 0.30))
        tipv = base + Vector((math.sin(lean_x) * ln, math.sin(lean_y) * ln,
                              math.cos(lean_x) * ln))
        w = wood[i % 3]
        m.strand([tuple(base), tuple(tipv)], r, w, seg=9, r2=r * 0.82)
        if kind == "oar":
            d = (tipv - base).normalized()
            bl0 = tipv - d * 0.62
            e = d.to_track_quat("Z", "Y").to_euler()
            m.box(tuple((bl0 + tipv) / 2), (0.098, 0.016, 0.31), w,
                  rot=(e.x, e.y, e.z + R.uniform(0, 3.1)))
        elif kind == "hook":
            d = (tipv - base).normalized()
            m.strand([tuple(tipv - d * 0.10), tuple(tipv + Vector((0.10, 0.03, 0.04)))],
                     0.020, ir, seg=6)
        else:
            m.cyl(tuple(tipv - (tipv - base).normalized() * 0.05), r * 1.18, 0.09, ir,
                  seg=10, rot=(lean_y, lean_x, 0))


def polearm_barrel(m, x, y, z=0.0, stave=None):
    """The weapon shop's corner: the same coopered barrel, standing hafted
    weapons instead of oars. Deliberately the same footprint and the same
    height band -- the room's composition is the archetype's, only the goods
    change."""
    stv, ir = stave or M("mat_i_oxblood_d"), M("mat_i_iron")
    rb, hb = 0.40, 0.80
    for i in range(18):
        a = 2 * math.pi * i / 18
        m.box((x + rb * math.cos(a), y + rb * math.sin(a), hb / 2),
              (0.075, 0.024, hb / 2), stv, rot=(0, 0, a + math.pi / 2), jitter=0.012)
    for hz in (0.07, 0.42, 0.73):
        m.lathe((x, y, hz), [(rb * 1.02, 0), (rb * 1.06, 0.012),
                             (rb * 1.06, 0.052), (rb * 1.02, 0.064)], ir, seg=20)
    arms = [(-0.17, -0.10, 2.10, "halberd"), (0.03, -0.17, 2.34, "spear"),
            (0.18, -0.02, 1.98, "boar"), (-0.06, 0.15, 2.44, "spear"),
            (0.13, 0.18, 1.88, "halberd"), (-0.20, 0.07, 2.16, "boar"),
            (0.00, 0.01, 2.26, "spear")]
    for i, (dx, dy, ln, kind) in enumerate(arms):
        lx, ly = R.uniform(-0.09, 0.09), R.uniform(-0.07, 0.07)
        polearm(m, x + dx, y + dy, 0.30, ln=ln, kind=kind,
                rot=(ly, lx, R.uniform(0, 3.1)),
                head=M("mat_i_steel") if i % 3 else M("mat_i_steel_b"))
    # a bundle of spare hafts leaning against the barrel, un-headed
    for k in range(4):
        a = 2.2 + k * 0.16
        m.strand([(x + 0.44 * math.cos(a), y + 0.44 * math.sin(a), 0.0),
                  (x + 0.20 * math.cos(a), y + 0.20 * math.sin(a), 1.94)],
                 0.019, M("mat_i_beam"), seg=8)


def apple_crate_open(m, x, y, z=0.0, w=0.62, d=0.54, h=0.44, rz=0.10, n=34,
                     fill="apple"):
    """An open crate with the lid propped against it, heaped to the rim. The
    heap is the point: a flat-topped crate reads as a box, a domed one reads
    as stock."""
    for sy in (-1, 1):
        m.box((x, y + sy * (d / 2), h / 2), (w / 2, 0.018, h / 2), M("mat_i_crate"),
              rot=(0, 0, rz))
    for sx in (-1, 1):
        m.box((x + sx * (w / 2) * math.cos(rz), y + sx * (w / 2) * math.sin(rz),
               h / 2), (0.018, d / 2, h / 2), M("mat_i_crate"), rot=(0, 0, rz))
    m.box((x, y, 0.02), (w / 2, d / 2, 0.02), M("mat_i_crate"), rot=(0, 0, rz))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((x + sx * 0.28, y + sy * 0.24, h / 2), (0.026, 0.026, h / 2),
                  M("mat_i_beam"), rot=(0, 0, rz))
    m.box((x - 0.02, y - 0.40, 0.30), (w / 2, 0.022, 0.28), M("mat_i_crate_b"),
          rot=(0.30, 0, rz))
    m.box((x - 0.02, y - 0.42, 0.30), (0.055, 0.018, 0.30), M("mat_i_oxblood"),
          rot=(0.30, 0, rz))
    for i in range(n):
        a = R.uniform(0, 2 * math.pi)
        rr = R.uniform(0, 0.235)
        px, py = x + rr * math.cos(a), y + rr * math.sin(a) * 0.86
        pz = 0.36 + R.uniform(0, 0.09) - rr * 0.20
        if fill == "apple":
            m.sphere((px, py, pz), R.uniform(0.040, 0.052),
                     M("mat_i_apple") if R.random() < 0.72 else M("mat_i_apple_g"),
                     seg=12, rings=8, rot=(R.uniform(0, 3), 0, R.uniform(0, 3)))
        elif fill == "billet":
            # rough iron billets and blade blanks: heavy, dull, stacked flat
            m.plate((px, py, pz - 0.10), R.uniform(0.26, 0.40), 0.055, 0.028,
                    M("mat_i_iron") if R.random() < 0.6 else M("mat_i_steel_b"),
                    rot=(1.57, R.uniform(0, 3.1), R.uniform(0, 3.1)), taper=0.8)
        else:                       # "buckler": small shield boards on edge
            shield_round(m, px, py, pz - 0.06, r=R.uniform(0.11, 0.145),
                         rot=(R.uniform(1.2, 1.9), 0, R.uniform(0, 3.1)),
                         face=M("mat_i_beam"), boss=True)


def provisions_barrel(m, x, y, z=0.0, n=9, fill="root"):
    barrel(m, x, y, 0.0, r=0.36, h=0.72, mat=M("mat_i_crate"), bands=(0.06, 0.62))
    for i in range(n):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0, 0.21)
        px, py = x + rr * math.cos(a), y + rr * math.sin(a)
        if fill == "root":
            m.lathe((px, py, 0.55 + R.uniform(0, 0.06)),
                    [(0, 0), (0.05, 0.02), (0.062, 0.07), (0.038, 0.12), (0, 0.14)],
                    M("mat_i_ceramic_b"), seg=10, lumpy=0.14, seed=i * 2.1,
                    aspect=(1.0, 0.78), rot=R.uniform(0, 3))
        elif fill == "helm":
            helm(m, px, py, 0.58 + R.uniform(0, 0.04), r=0.098,
                 rot=(R.uniform(-0.3, 0.3), R.uniform(-0.3, 0.3), R.uniform(0, 3)),
                 mat=M("mat_i_steel_b") if i % 2 else M("mat_i_steel"),
                 kind="nasal")
        else:                       # "hilt": a barrel of loose sword blanks
            m.strand([(px, py, 0.50), (px + R.uniform(-0.12, 0.12),
                                       py + R.uniform(-0.12, 0.12),
                                       0.50 + R.uniform(0.34, 0.62))],
                     0.016, M("mat_i_steel_b"), seg=4, r2=0.007)


def cordage_peg_rack(m, x0, y0, z, y1=0.0, face=-1.0, pegs=6, shelf=True):
    """The right-hand repoussoir: a peg rail carrying coils and buckets over a
    top shelf of stock.

    `face` is the sign of the direction the pegs point INTO the room: +1 for
    the right (+X) wall, -1 for the left. Getting this backwards buries the
    entire rack inside the wall panel, where it renders as nothing at all and
    looks exactly like a rack that simply did not get built.
    """
    g, bm_, ir = M("mat_i_green"), M("mat_i_beam"), M("mat_i_iron")
    yc, dy = (y0 + y1) / 2, (y1 - y0) / 2
    m.box((x0 - face * 0.045, yc, z + 0.10), (0.045, dy, 0.055), g)
    ys = [y0 + (y1 - y0) * (i + 0.5) / pegs for i in range(pegs)]
    for i, py in enumerate(ys):
        m.cyl((x0 - face * 0.14, py, z + 0.14), 0.022, 0.20, bm_, seg=8,
              rot=(0, math.pi / 2, 0))
    for i, py in enumerate(ys):
        if i % 2 == 0:
            for k in range(3):
                rr = 0.20 - k * 0.032
                pts = [(x0 - face * (0.20 + 0.012 * k) +
                        rr * math.sin(2 * math.pi * t / 16) * 0.28,
                        py + rr * math.cos(2 * math.pi * t / 16),
                        z + 0.12 - rr * (1 - math.cos(2 * math.pi * t / 16)))
                       for t in range(17)]
                m.strand(pts, 0.0135, M("mat_rope"), seg=5)
        else:
            m.strand([(x0 - face * 0.16, py, z + 0.12),
                      (x0 - face * 0.30, py, z - 0.12)], 0.010, M("mat_rope"), seg=4)
            bucket(m, x0 - face * 0.30, py, z - 0.52, r=0.150, h=0.30,
                   mat=M("mat_i_crate_b"))
    if shelf:
        m.box((x0 - face * 0.17, yc, z + 0.50), (0.17, dy + 0.07, 0.022),
              M("mat_i_shelf"))
        for by in (y0 - 0.09, y1 + 0.09):
            m.box((x0 - face * 0.17, by, z + 0.33), (0.17, 0.030, 0.19), bm_)
        for i in range(5):
            m.box((x0 - face * 0.20, y0 + 0.02 + i * 0.44, z + 0.34),
                  (0.11, 0.055, 0.13), bm_, rot=(0, math.radians(-38) * face, 0))


def weapon_peg_rack(m, x0, y0, z, y1=0.0, face=1.0, pegs=6):
    """Same rail, hafted goods: blades point-down, quivers, bows. Alternating
    long verticals with big gaps, so the rail never fills in the way a row of
    identical items does."""
    g, bm_ = M("mat_i_green"), M("mat_i_beam")
    yc, dy = (y0 + y1) / 2, (y1 - y0) / 2
    m.box((x0 - face * 0.045, yc, z + 0.10), (0.045, dy, 0.055), g)
    ys = [y0 + (y1 - y0) * (i + 0.5) / pegs for i in range(pegs)]
    for i, py in enumerate(ys):
        m.cyl((x0 - face * 0.14, py, z + 0.14), 0.022, 0.20, bm_, seg=8,
              rot=(0, math.pi / 2, 0))
        px = x0 - face * 0.20
        if i % 3 == 0:
            m.strand([(x0 - face * 0.16, py, z + 0.12), (px, py, z + 0.02)],
                     0.008, M("mat_i_leather"), seg=3)
            bow(m, px, py, z - 0.60, ln=1.18, rot=(0, 0, 0), mat=M("mat_i_beam"))
        elif i % 3 == 1:
            m.strand([(x0 - face * 0.16, py, z + 0.12), (px, py, z - 0.14)],
                     0.009, M("mat_i_leather"), seg=3)
            quiver(m, px, py, z - 0.66, ln=0.52, rot=(0, 0, 1.2))
        else:
            m.strand([(x0 - face * 0.16, py, z + 0.12), (px, py, z + 0.04)],
                     0.008, M("mat_rope"), seg=3)
            sword(m, px, py, z + 0.02, ln=0.94, rot=(0, math.pi, 0),
                  blade=M("mat_i_steel_bright") if i % 2 else M("mat_i_steel"))
    # top shelf, same carcass as the chandlery rail
    m.box((x0 - face * 0.17, yc, z + 0.50), (0.17, dy + 0.07, 0.022),
          M("mat_i_shelf"))
    for by in (y0 - 0.09, y1 + 0.09):
        m.box((x0 - face * 0.17, by, z + 0.33), (0.17, 0.030, 0.19), bm_)
    # a rank of spare hafts stood on end behind the rail
    for i in range(5):
        m.strand([(x0 - face * 0.12, y0 + 0.10 + i * 0.42, z - 1.50),
                  (x0 - face * 0.20, y0 + 0.14 + i * 0.42, z + 0.06)],
                 0.018, bm_, seg=6)


def armour_peg_rack(m, x0, y0, z, y1=0.0, face=-1.0, pegs=6):
    """Mail shirts and round shields on the rail. The shields are the readable
    element -- a disc with a rim highlight is legible at any size, which is
    exactly what a room full of grey needs."""
    g, bm_ = M("mat_i_steelblue"), M("mat_i_beam")
    yc, dy = (y0 + y1) / 2, (y1 - y0) / 2
    m.box((x0 - face * 0.045, yc, z + 0.10), (0.045, dy, 0.055), g)
    ys = [y0 + (y1 - y0) * (i + 0.5) / pegs for i in range(pegs)]
    faces = [M("mat_i_oxblood"), M("mat_i_steelblue_b"), M("mat_i_beam")]
    for i, py in enumerate(ys):
        m.cyl((x0 - face * 0.14, py, z + 0.14), 0.022, 0.20, bm_, seg=8,
              rot=(0, math.pi / 2, 0))
        if i % 2 == 0:
            shield_round(m, x0 - face * 0.20, py, z - 0.16, r=0.30,
                         rot=(0, -face * math.pi / 2, 0), face=faces[i % 3],
                         rim=M("mat_i_steel_b"), boss=True)
            m.strand([(x0 - face * 0.16, py, z + 0.12),
                      (x0 - face * 0.20, py, z + 0.10)], 0.009,
                     M("mat_i_leather"), seg=3)
        else:
            m.strand([(x0 - face * 0.14, py - 0.16, z + 0.14),
                      (x0 - face * 0.14, py + 0.16, z + 0.14)], 0.014, bm_, seg=3)
            mail_shirt(m, x0 - face * 0.22, py, z + 0.06, ln=0.66,
                       rot=(0, 0, math.pi / 2))
    m.box((x0 - face * 0.17, yc, z + 0.50), (0.17, dy + 0.07, 0.022),
          M("mat_i_shelf"))
    for by in (y0 - 0.09, y1 + 0.09):
        m.box((x0 - face * 0.17, by, z + 0.33), (0.17, 0.030, 0.19), bm_)


def tapped_barrel(m, x, y, z=0.62, stave=None, label=True):
    """The chandlery premise in one prop: a barrel of lamp oil on a cradle
    with a spigot and a catch bucket."""
    ox, ir, bm_, g = stave or M("mat_i_oxblood"), M("mat_i_iron"), \
        M("mat_i_beam"), M("mat_i_green")
    bh, br = 0.66, 0.315
    for i in range(18):
        a = 2 * math.pi * i / 18
        m.box((x, y + br * math.cos(a), z + br * math.sin(a)),
              (bh / 2, 0.060, 0.023), ox, rot=(a + math.pi / 2, 0, 0), jitter=0.010)
    for hx in (-bh / 2 + 0.10, 0.0, bh / 2 - 0.10):
        for i in range(20):
            a = 2 * math.pi * i / 20
            m.box((x + hx, y + br * 1.05 * math.cos(a), z + br * 1.05 * math.sin(a)),
                  (0.028, 0.052, 0.012), ir, rot=(a + math.pi / 2, 0, 0))
    for hx in (-bh / 2 - 0.012, bh / 2 + 0.012):
        m.cyl((x + hx, y, z), br * 0.97, 0.026, M("mat_i_crate"), seg=20,
              rot=(0, math.pi / 2, 0))
    for s_ in (-1, 1):
        m.box((x + s_ * 0.36, y, 0.145), (0.052, 0.30, 0.145), bm_)
        for e_ in (-1, 1):
            m.box((x + s_ * 0.36, y + e_ * 0.215, 0.375), (0.048, 0.075, 0.105),
                  bm_, rot=(math.radians(-24) * e_, 0, 0))
    m.box((x, y, 0.042), (0.44, 0.30, 0.042), g)
    m.cyl((x, y - br - 0.055, 0.50), 0.023, 0.14, M("mat_i_brass"), seg=10,
          rot=(math.pi / 2, 0, 0))
    m.cyl((x, y - br - 0.105, 0.545), 0.011, 0.075, M("mat_i_brass"), seg=8)
    bucket(m, x, y - br - 0.15, 0.0, r=0.150, h=0.28, mat=M("mat_i_crate_b"))
    if label:
        m.box((x, y - br - 0.010, 0.90), (0.23, 0.013, 0.095), ox)
        m.box((x, y - br - 0.022, 0.90), (0.19, 0.008, 0.062), M("mat_i_label"))


def coir_mat(m, x, y, z=0.006, w=0.52, d=0.30, mat=None):
    mat = mat or M("mat_i_net")
    for i in range(22):
        m.strand([(x - w, y + 0.028 * i, z), (x + w, y + 0.028 * i, z)],
                 0.011, mat, seg=4)
    for i in range(9):
        xx = x - w + (2 * w / 8) * i
        m.strand([(xx, y - 0.01, z + 0.004), (xx, y + 0.61, z + 0.004)],
                 0.010, mat, seg=4)


def notices(m, x, y, z, spots=((0.0, 0.0, 0.095, 0.125, 0.05),
                              (0.26, -0.14, 0.075, 0.095, -0.09),
                              (0.04, -0.38, 0.082, 0.065, 0.03))):
    """Bills nailed to the wall by the door. Every shop has them; only the
    positions are a skin's business."""
    for (dx, dz, nw, nh, rr_) in spots:
        nx, nz = x + dx, z + dz
        m.box((nx, y - 0.010, nz), (nw, 0.010, nh), M("mat_i_paper"), rot=(0, rr_, 0))
        for k in range(3):
            m.box((nx + R.uniform(-nw * 0.5, nw * 0.5), y - 0.021,
                   nz + (k - 1) * nh * 0.5), (nw * R.uniform(0.3, 0.6), 0.003, 0.005),
                  M("mat_i_iron"))


def stool(m, x, y, z=0.0, h=0.56, top=None):
    top = top or M("mat_i_shelf")
    m.lathe((x, y, h), [(0, 0), (0.19, 0.0), (0.20, 0.018), (0.19, 0.030),
                        (0, 0.032)], top, seg=16)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        m.strand([(x + 0.145 * math.cos(a), y + 0.145 * math.sin(a), z),
                  (x + 0.085 * math.cos(a), y + 0.085 * math.sin(a), h)],
                 0.026, M("mat_i_beam"), seg=6)
    m.box((x, y, h + 0.04), (0.14, 0.10, 0.016), M("mat_i_leather"), rot=(0, 0, 0.4))


def broom(m, x, y, z=0.02, h=1.60, mat=None):
    bm_ = M("mat_i_beam")
    top = Vector((x + 0.16, y - 0.42, z + h))
    bot = Vector((x, y - 0.02, z))
    m.strand([tuple(bot), tuple(top)], 0.019, bm_, seg=8)
    d = (top - bot).normalized()
    for k in range(16):
        a = 2 * math.pi * k / 16
        m.strand([tuple(bot + d * 0.30),
                  (bot.x + 0.10 * math.cos(a), bot.y + 0.10 * math.sin(a), z - 0.01)],
                 0.010, mat or M("mat_i_net"), seg=4, r2=0.004)


def price_board(m, x, wall_y, z, w=0.44, h=0.30, frame_mat=None, n=6):
    m.box((x, wall_y - 0.025, z), (w, 0.025, h), frame_mat or M("mat_i_oxblood"))
    m.box((x, wall_y - 0.055, z), (w - 0.06, 0.012, h - 0.055), M("mat_tar"))
    for i in range(n):
        m.box((x + R.uniform(-w * 0.6, w * 0.6), wall_y - 0.070,
               z - h * 0.47 + i * 0.075), (R.uniform(0.05, 0.17), 0.004, 0.009),
              M("mat_i_label"))


def crossed_sign(m, x, wall_y, z=0.0, kind="oars", trim=None):
    """The trade sign over the door: two crossed tools of the trade. The one
    piece of the room that names the shop from across the frame."""
    bm_, sh, g = M("mat_i_beam"), M("mat_i_shelf"), trim or M("mat_i_green")
    if kind == "oars":
        for s_ in (-1, 1):
            m.strand([(x - s_ * 0.92, wall_y - 0.075, 2.21),
                      (x + s_ * 0.92, wall_y - 0.075, 2.84)], 0.029, bm_, seg=6)
            m.box((x + s_ * 0.735, wall_y - 0.104, 2.74), (0.115, 0.019, 0.30), sh,
                  rot=(0, math.radians(20) * s_, 0))
    elif kind == "swords":
        # dark steel on a dark wall is invisible; the sign only reads because
        # of the painted board behind it
        m.box((x, wall_y - 0.030, 2.42), (0.86, 0.030, 0.30), M("mat_i_oxblood"))
        m.box((x, wall_y - 0.056, 2.42), (0.80, 0.020, 0.255), M("mat_i_shelf"))
        # NOTE the wall is 3.0 tall and the sign sits at 2.2: a 1.3u blade
        # standing on that point goes straight through the roof. Everything
        # here is sized to finish under z = 2.9.
        for s_ in (-1, 1):
            sword(m, x - s_ * 0.66, wall_y - 0.085, 2.02, ln=1.12,
                  rot=(0, math.radians(-42) * s_, 0),
                  blade=M("mat_i_steel_bright") if s_ > 0 else M("mat_i_steel"))
    else:                                     # "shield": shield over a sword
        m.box((x, wall_y - 0.030, 2.42), (0.80, 0.030, 0.30), M("mat_i_steelblue_b"))
        sword(m, x, wall_y - 0.075, 2.02, ln=0.86, rot=(0, 0, 0),
              blade=M("mat_i_steel_bright"))
        # rot about X by +90 turns the disc's normal from +Z to -Y, i.e. out
        # into the room. At (0,0,0) it faces the ceiling and reads as a hole.
        shield_round(m, x, wall_y - 0.145, 2.50, r=0.34,
                     rot=(math.radians(90), 0, 0),
                     face=M("mat_i_oxblood"), rim=M("mat_i_steel_b"), boss=True)
    m.box((x, wall_y - 0.048, 2.53), (0.070, 0.048, 0.070), g)


def hawser(m, x, y, z=0.036, k=5, r0=0.44, tail=True):
    for i in range(k):
        rr = r0 - i * 0.075
        pts = [(x + rr * math.cos(2 * math.pi * t / 26),
                y + rr * math.sin(2 * math.pi * t / 26) * 0.92,
                z + i * 0.062) for t in range(27)]
        m.strand(pts, 0.034, M("mat_rope"), seg=6)
    if tail:
        m.strand(sagline((x + r0, y, z), (x + r0 + 0.51, y - 0.42, z - 0.002), 0.02, 6),
                 0.034, M("mat_rope"), seg=6)


def floor_litter(m, x0, x1, y0, y1, n=190, hot=(1.9, -0.2), spread=2.2,
                 base=0.30, mat=None, ln=(0.05, 0.155), r=0.0040):
    """Straw / sawdust / metal swarf: denser where goods are handled."""
    mat = mat or M("mat_i_straw")
    for i in range(n):
        x = R.uniform(x0, x1)
        y = R.uniform(y0, y1)
        if R.random() > base + (1.0 - base) * math.exp(
                -((x - hot[0]) ** 2 + (y - hot[1]) ** 2) / spread):
            continue
        a = R.uniform(0, math.pi)
        L = R.uniform(*ln)
        m.strand([(x, y, 0.004), (x + L * math.cos(a), y + L * math.sin(a), 0.004)],
                 r, mat, seg=3)


# =========================================================== counter dressing

def ledger(m, x, y, z, rz=0.13, open_=True):
    m.box((x, y, z + 0.022), (0.20, 0.145, 0.022), M("mat_i_leather"), rot=(0, 0, rz))
    if open_:
        for sx in (-1, 1):
            m.box((x + sx * 0.098 * math.cos(rz), y + sx * 0.098 * math.sin(rz),
                   z + 0.052), (0.098, 0.135, 0.014), M("mat_i_paper"),
                  rot=(0, sx * 0.05, rz))
        m.box((x, y, z + 0.048), (0.016, 0.14, 0.026), M("mat_i_leather"), rot=(0, 0, rz))
    m.lathe((x + 0.30, y - 0.06, z), [(0, 0), (0.036, 0), (0.040, 0.03),
                                      (0.030, 0.055), (0.020, 0.062), (0, 0.066)],
            M("mat_i_ceramic_b"), seg=12)
    m.strand([(x + 0.30, y - 0.06, z + 0.05), (x + 0.36, y + 0.02, z + 0.20)],
             0.005, M("mat_i_paper"), seg=5, r2=0.001)


def balance_scale(m, x, y, z, weights=True):
    br = M("mat_i_brass")
    m.lathe((x, y, z), [(0, 0), (0.085, 0), (0.090, 0.016), (0.048, 0.026),
                        (0.020, 0.034), (0, 0.036)], M("mat_i_beam"), seg=14)
    m.cyl((x, y, z + 0.20), 0.014, 0.34, br, seg=10)
    m.box((x, y, z + 0.375), (0.175, 0.011, 0.011), br, rot=(0.045, 0, 0))
    for s in (-1, 1):
        px = x + s * 0.172
        pz = z + 0.375 + s * 0.008
        for k in range(3):
            a = 2 * math.pi * k / 3
            m.strand([(px, y, pz),
                      (px + 0.052 * math.cos(a), y + 0.052 * math.sin(a), pz - 0.105)],
                     0.0022, br, seg=4)
        m.lathe((px, y, pz - 0.115), [(0, 0), (0.030, 0.004), (0.058, 0.016),
                                      (0.058, 0.019), (0.028, 0.008), (0, 0.005)],
                br, seg=14)
    if weights:
        for i, rr in enumerate((0.030, 0.026, 0.022)):
            m.lathe((x - 0.30 + i * 0.072, y - 0.08, z),
                    [(0, 0), (rr, 0), (rr * 0.92, 0.042), (rr * 0.45, 0.048), (0, 0.052)],
                    M("mat_i_iron"), seg=12)


def oil_lamp(m, x, y, z, energy=400.0, name="LAMP_counter"):
    br = M("mat_i_brass")
    m.lathe((x, y, z), [(0, 0), (0.075, 0), (0.080, 0.014), (0.040, 0.030),
                        (0.036, 0.052), (0.062, 0.075), (0.066, 0.115),
                        (0.050, 0.140), (0.048, 0.150), (0, 0.152)], br, seg=16)
    m.lathe((x, y, z + 0.150), [(0.048, 0), (0.058, 0.012), (0.062, 0.11),
                                (0.050, 0.155)], M("mat_i_lampglass"), seg=16)
    m.lathe((x, y, z + 0.300), [(0.052, 0), (0.058, 0.010), (0.030, 0.038),
                                (0.014, 0.050), (0, 0.054)], br, seg=14)
    m.lathe((x, y, z + 0.185), [(0, 0), (0.012, 0.008), (0.008, 0.055), (0, 0.070)],
            M("mat_i_flame"), seg=10)
    if energy:
        point(name, (x, y, z + 0.225), energy, (1.0, 0.60, 0.26), radius=0.05)


def candle_lantern(m, x, y, z, energy=85.0, name="LAMP_counter_l"):
    ir = M("mat_i_iron")
    m.lathe((x, y, z), [(0, 0), (0.070, 0), (0.074, 0.014), (0.058, 0.028),
                        (0.052, 0.040)], ir, seg=12)
    m.lathe((x, y, z + 0.040), [(0.050, 0), (0.056, 0.010), (0.058, 0.135),
                                (0.048, 0.170)], M("mat_i_lampglass"), seg=12)
    m.lathe((x, y, z + 0.210), [(0.052, 0), (0.056, 0.010), (0.028, 0.036),
                                (0, 0.050)], ir, seg=12)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        m.strand([(x + 0.054 * math.cos(a), y + 0.054 * math.sin(a), z + 0.040),
                  (x + 0.054 * math.cos(a), y + 0.054 * math.sin(a), z + 0.210)],
                 0.005, ir, seg=3)
    m.lathe((x, y, z + 0.070), [(0, 0), (0.011, 0.006), (0.007, 0.042), (0, 0.054)],
            M("mat_i_flame"), seg=8)
    if energy:
        point(name, (x, y, z + 0.115), energy, (1.0, 0.62, 0.28), radius=0.04)


def coin_dish(m, x, y, z, n=7):
    br = M("mat_i_brass")
    m.lathe((x, y, z), [(0, 0), (0.058, 0.004), (0.075, 0.020), (0.074, 0.024),
                        (0.056, 0.010), (0, 0.006)], br, seg=14)
    for i in range(n):
        m.cyl((x + R.uniform(-0.035, 0.035), y + R.uniform(-0.035, 0.035),
               z + 0.024 + i * 0.004), 0.012, 0.004, br, seg=8)


def fruit_box(m, x, y, z, n=3):
    small_crate(m, x, y, z, w=0.20, d=0.18, h=0.13, rz=0.22, mat=M("mat_i_crate_b"))
    for i in range(n):
        m.sphere((x + R.uniform(-0.05, 0.05), y + R.uniform(-0.04, 0.04), z + 0.145),
                 0.043, M("mat_i_apple") if i else M("mat_i_apple_g"), seg=12, rings=8)


def book_stack(m, x, y, z, n=3, step=0.036):
    for i in range(n):
        m.box((x, y, z + i * step), (0.19, 0.135, 0.018),
              M("mat_i_leather") if i % 2 else M("mat_i_paper"),
              rot=(0, 0, R.uniform(-0.09, 0.09)))


def parts_bin(m, x, y, z, w=0.17, d=0.13, n=9, kind="rivet"):
    """A partitioned tray of small metal parts. The armour shop's answer to a
    bowl of apples: lots of tiny specular hits at counter height."""
    m.box((x, y, z + 0.010), (w, d, 0.010), M("mat_i_shelf"))
    for s in (-1, 1):
        m.box((x + s * w, y, z + 0.028), (0.010, d, 0.028), M("mat_i_shelf"))
        m.box((x, y + s * d, z + 0.028), (w, 0.010, 0.028), M("mat_i_shelf"))
    m.box((x, y, z + 0.028), (0.008, d, 0.024), M("mat_i_shelf"))
    for i in range(n):
        bx, by = x + R.uniform(-w * 0.8, w * 0.8), y + R.uniform(-d * 0.7, d * 0.7)
        if kind == "rivet":
            m.sphere((bx, by, z + 0.026), 0.011, M("mat_i_bronze"), seg=8, rings=5,
                     scale=(1, 1, 0.6))
        else:
            m.cyl((bx, by, z + 0.026), 0.013, 0.006, M("mat_i_steel_b"), seg=8,
                  rot=(0, 0, R.uniform(0, 3)))


def dresser(m, x0, x1, y0, y1, boards=(0.42, 0.90, 1.38, 1.86), trim=None,
            accent=None, cornice=2.02):
    """The narrow shelving unit in the dead bay beside the door."""
    sh, shb = M("mat_i_shelf"), M("mat_i_shelf_b")
    g = trim or M("mat_i_green")
    ox = accent or M("mat_i_oxblood")
    for z in boards:
        m.box(((x0 + x1) / 2, (y0 + y1) / 2, z), ((x1 - x0) / 2, 0.17, 0.020),
              sh if z in boards[::2] else shb)
        m.box(((x0 + x1) / 2, y0 + 0.012, z + 0.032), ((x1 - x0) / 2, 0.012, 0.022), g)
    for ux in (x0 + 0.032, x1 - 0.032):
        m.box((ux, (y0 + y1) / 2, 1.10), (0.032, 0.17, 1.10), shb)
    m.box(((x0 + x1) / 2, y1 - 0.04, cornice), ((x1 - x0) / 2 + 0.03, 0.04, 0.10), ox)


def trestle(m, x0, x1, y0, y1, h=0.76, trim=None, accent=None):
    """The browse island: a trestle table of open stock in the middle of the
    aisle. Its top is the only mid-height horizontal in the left half of the
    frame, so whatever a skin puts on it is read immediately."""
    bm_ = M("mat_i_beam")
    g = trim or M("mat_i_green")
    ox = accent or M("mat_i_oxblood")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    m.box((cx, cy, h), ((x1 - x0) / 2, (y1 - y0) / 2, 0.024), M("mat_i_counter"))
    for ex in (x0 + 0.16, x1 - 0.16):
        for ey in (y0 + 0.12, y1 - 0.12):
            m.strand([(ex, ey, 0.0), (ex, ey, h - 0.024)], 0.030, bm_, seg=6)
        m.box((ex, cy, 0.30), (0.030, (y1 - y0) / 2 - 0.10, 0.026), g)
    m.box((cx, cy, 0.34), ((x1 - x0) / 2 - 0.14, 0.026, 0.024), bm_)
    m.box((cx, y0 + 0.02, 0.90), ((x1 - x0) / 2 - 0.06, 0.018, 0.085), ox)


def window_bench(m, x, y, trim=None):
    g = trim or M("mat_i_green")
    m.box((x, y, 0.60), (0.24, 0.62, 0.022), M("mat_i_shelf"))
    for sy in (-1, 1):
        m.box((x, y + sy * 0.56, 0.30), (0.20, 0.035, 0.30), g)
    m.box((x, y, 0.14), (0.20, 0.56, 0.020), M("mat_i_shelf_b"))


def measure_set(m, x, y, z):
    cu = M("mat_i_copper")
    m.lathe((x, y - 0.30, z), [(0, 0), (0.085, 0), (0.092, 0.02), (0.086, 0.20),
                               (0.070, 0.225), (0, 0.228)], cu, seg=14)
    m.lathe((x + 0.02, y + 0.02, z), [(0, 0), (0.022, 0), (0.024, 0.12),
                                      (0.115, 0.24), (0.118, 0.25), (0, 0.25)],
            cu, seg=14)
    for i in range(3):
        tin(m, x - 0.02, y + 0.34, z + i * 0.122,
            mat=M("mat_i_rust") if i % 2 else cu)


def pot_row(m, x, y, z, n=4, spread=0.45):
    for i in range(n):
        m.lathe((x + R.uniform(-0.08, 0.08), y + R.uniform(-spread, spread), z),
                [(0, 0), (0.055, 0.01), (0.062, 0.16), (0.048, 0.19), (0, 0.20)],
                M("mat_i_ceramic_gn") if i % 2 else M("mat_i_ceramic_ox"), seg=12)


# ============================================================ hanging goods

def hung_from_beam(m, x, y, z, fn, drop=0.30, cord=0.008, mat=None, **kw):
    """A hook rope from the beam underside down to whatever hangs on it. The
    rope matters: without a visible suspension the goods read as floating."""
    m.strand([(x, y, z), (x, y, z - drop)], cord, mat or M("mat_i_iron"), seg=4)
    if fn is not None:
        fn(m, x, y, z - drop, **kw)


def dried_fish_line(m, x, y, z, x1=None, n=9, sag=0.14, span=3.0):
    rp = M("mat_rope")
    x1 = x + span if x1 is None else x1
    line = sagline((x, y, z), (x1, y, z), sag, 14)
    m.strand(line, 0.008, rp, seg=5)
    for i in range(n):
        t = (i + 0.5) / n
        k = int(t * 14)
        px, py, pz = line[k]
        ln = R.uniform(0.30, 0.40)
        tilt = R.uniform(-0.12, 0.12)
        m.lathe((px, py, pz - ln), [(0, 0), (0.020, ln * 0.10), (0.042, ln * 0.38),
                                    (0.046, ln * 0.55), (0.030, ln * 0.82),
                                    (0.011, ln * 0.95), (0, ln)],
                M("mat_i_fish"), seg=10, aspect=(1.0, 0.42), rot=tilt)
        m.box((px, py, pz - ln + 0.012), (0.055, 0.006, 0.030), M("mat_i_fish"),
              rot=(0, 0.5, tilt))
        m.strand([(px, py, pz), (px, py, pz - 0.04)], 0.0035, rp, seg=3)


def hung_coils(m, x, y, z, r=0.24, n=4, drop=0.16):
    rp = M("mat_rope")
    m.strand([(x, y, z), (x, y, z - drop)], 0.010, rp, seg=4)
    for k in range(n):
        r2 = r - k * 0.030
        top = z - drop - k * 0.055
        pts = [(x + r2 * math.sin(2 * math.pi * t / 18) * 0.34,
                y + r2 * math.cos(2 * math.pi * t / 18),
                top - r2 * (1 - math.cos(2 * math.pi * t / 18)))
               for t in range(19)]
        m.strand(pts, 0.0135, rp, seg=5)


def block_tackle(m, x, y, z, drop=0.22):
    m.strand([(x, y, z), (x, y, z - drop)], 0.008, M("mat_rope"), seg=4)
    m.box((x, y, z - drop - 0.08), (0.045, 0.035, 0.075), M("mat_i_beam"))
    m.cyl((x, y, z - drop - 0.08), 0.030, 0.078, M("mat_i_iron"), seg=12,
          rot=(0, math.pi / 2, 0))


def herb_bunch(m, x, y, z, n=11, drop=0.14, ln=0.30, mat=None):
    m.strand([(x, y, z), (x, y, z - drop)], 0.007, M("mat_rope"), seg=3)
    for k in range(n):
        a = 2 * math.pi * k / n
        m.strand([(x, y, z - drop),
                  (x + 0.075 * math.cos(a), y + 0.075 * math.sin(a), z - drop - ln)],
                 0.010, mat or M("mat_i_net"), seg=5, r2=0.003)


def hang_bar(m, x, y, z, span=2.8, drop=0.18, mat=None):
    """A steel bar slung under a beam on two cords -- what a shop hangs mail
    shirts and shields from."""
    mat = mat or M("mat_i_iron")
    x0, x1 = x - span / 2, x + span / 2
    for xx in (x0, x1):
        m.strand([(xx, y, z), (xx, y, z - drop)], 0.008, mat, seg=4)
    m.strand([(x0, y, z - drop), (x1, y, z - drop)], 0.016, mat, seg=6)


def hung_arms_row(m, x, y, z, span=2.8, n=4, drop=0.20, kind="bow"):
    """Bows and quivers slung under a beam: the weapon shop's dried-fish line.
    Long verticals with a big gap between them, so it never fills in."""
    hang_bar(m, x, y, z, span=span, drop=drop)
    x0, x1 = x - span / 2, x + span / 2
    for i in range(n):
        xx = x0 + (x1 - x0) * (i + 0.5) / n
        if (i + (kind == "quiver")) % 2 == 0:
            m.strand([(xx, y, z - drop), (xx, y, z - drop - 0.10)], 0.006,
                     M("mat_i_leather"), seg=3)
            bow(m, xx, y, z - drop - 0.78, ln=1.28, rot=(0, 0, R.uniform(-0.2, 0.2)),
                mat=M("mat_i_beam"))
        else:
            m.strand([(xx, y, z - drop), (xx, y - 0.02, z - drop - 0.24)], 0.007,
                     M("mat_i_leather"), seg=3)
            quiver(m, xx, y - 0.02, z - drop - 0.78, ln=0.54,
                   rot=(0, 0, R.uniform(0, 3.1)))


def hung_mail_row(m, x, y, z, span=2.8, n=3, drop=0.20, shields=True):
    """Shields and mail shirts under a beam.

    The SHIELDS lead. A disc turned to the camera with a rim highlight all the
    way round is the most legible silhouette available, and an armour shop is
    otherwise a room of grey lumps in a brown box. Mail hangs between them as
    the soft, dark counterpoint -- never more of it than shields, because five
    hanging hauberks in a row read as laundry.
    """
    hang_bar(m, x, y, z, span=span, drop=drop)
    x0, x1 = x - span / 2, x + span / 2
    faces = [M("mat_i_oxblood"), M("mat_i_beam"), M("mat_i_oxblood")]
    for i in range(n):
        xx = x0 + (x1 - x0) * (i + 0.5) / n
        if i % 2 == 1 and shields is not False:
            m.strand([(xx - 0.16, y, z - drop), (xx + 0.16, y, z - drop)], 0.010,
                     M("mat_i_iron"), seg=3)
            if i == 1:
                breastplate(m, xx, y + 0.02, z - drop - 0.62, h=0.50,
                            rot=(0, 0, R.uniform(-0.2, 0.2)))
            else:
                mail_shirt(m, xx, y, z - drop - 0.08, ln=0.58, rot=(0, 0, 0))
        else:
            m.strand([(xx, y, z - drop), (xx, y + 0.03, z - drop - 0.20)], 0.007,
                     M("mat_i_leather"), seg=3)
            shield_round(m, xx, y + 0.05, z - drop - 0.54, r=0.31,
                         rot=(math.radians(87), 0, R.uniform(0, 3.1)),
                         face=faces[i % 3], rim=M("mat_i_steel_bright"), boss=True)


def blade_hang_row(m, x, y, z, span=2.8, n=5, drop=0.16, mats=None):
    """Blades hung point-down in a row under a beam -- the weapon shop's
    strongest single graphic.

    Two things stop it being a row of blue planks. Each blade is turned about
    30-60 degrees off square, so it shows a narrow three-quarter face and a
    lit edge instead of one broad flat mirror of the cool overhead wash; and
    the row alternates blade lengths and slips an axe in, so the silhouette
    has a rhythm rather than a beat.
    """
    hang_bar(m, x, y, z, span=span, drop=drop)
    x0, x1 = x - span / 2, x + span / 2
    mats = mats or [M("mat_i_steel_bright"), M("mat_i_steel"),
                    M("mat_i_steel_bright"), M("mat_i_steel_b")]
    for i in range(n):
        xx = x0 + (x1 - x0) * (i + 0.5) / n
        ln = R.uniform(0.74, 1.06)
        m.strand([(xx, y, z - drop), (xx, y, z - drop - 0.06)], 0.005,
                 M("mat_rope"), seg=3)
        if i == n // 2:                       # one axe, for silhouette relief
            axe(m, xx, y, z - drop - 0.06, ln=ln * 0.82,
                rot=(R.uniform(0.06, 0.16), math.pi, R.uniform(0.5, 1.0)),
                head=M("mat_i_steel"))
            continue
        # rot=(0, pi, .) makes the blade grow DOWNWARD from the given point,
        # so the point IS the hanging point -- do not subtract ln as well or
        # the whole row ends up at counter height, crossing the counter.
        sword(m, xx, y, z - drop - 0.06, ln=ln,
              rot=(R.uniform(0.10, 0.20), math.pi,
                   R.choice([1, -1]) * R.uniform(0.55, 1.05)),
              blade=mats[i % len(mats)], wide=0.86)


# ======================================================== heaps and clusters
#
# The small compound props a skin drops on a trestle or a counter. Each is
# the same idea in three trades: a container plus a heap of goods whose tops
# make a dome, because a flat-topped pile reads as an empty box.

def apple_heap(m, x, y, z, n=11, r=0.15, spread=0.05):
    for i in range(n):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0, r)
        m.sphere((x + rr * math.cos(a), y + rr * math.sin(a),
                  z + R.uniform(0, spread)), R.uniform(0.042, 0.052),
                 M("mat_i_apple_g") if i % 3 else M("mat_i_apple"), seg=12, rings=8)


def tin_stack(m, x, y, z, n=3):
    for i in range(n):
        tin(m, x, y, z + i * 0.122,
            mat=M("mat_i_rust") if i % 2 else M("mat_i_copper"))


def blade_fan(m, x, y, z, n=5, r=0.17):
    """Swords stood on their points in a crate, fanned so no two are parallel.
    The fan is what stops five identical blades reading as a comb."""
    for i in range(n):
        a = -0.55 + 1.10 * i / max(1, n - 1)
        sword(m, x + r * math.sin(a) * 0.4, y + R.uniform(-0.04, 0.04), z,
              ln=R.uniform(0.78, 0.94),
              rot=(R.uniform(-0.10, 0.10), a, R.uniform(0, 3.1)),
              blade=[M("mat_i_steel"), M("mat_i_steel_bright"),
                     M("mat_i_steel_b")][i % 3])


def axe_row(m, x, y, z, n=3, step=0.13):
    """Axes stood head-up in a bracket. Their heads make a row of heavy
    horizontals at one height, which is the counterpoint the blades need."""
    m.box((x + step * (n - 1) / 2, y, z + 0.030), (step * n * 0.5, 0.055, 0.030),
          M("mat_i_beam"))
    for i in range(n):
        axe(m, x + i * step, y + R.uniform(-0.02, 0.02), z + 0.058,
            ln=R.uniform(0.46, 0.58),
            rot=(R.uniform(-0.06, 0.06), R.uniform(-0.14, 0.14), R.uniform(0, 3.1)),
            head=M("mat_i_steel") if i % 2 else M("mat_i_steel_b"))


def helm_heap(m, x, y, z, n=5, r=0.16):
    for i in range(n):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0, r)
        helm(m, x + rr * math.cos(a), y + rr * math.sin(a), z + R.uniform(0, 0.05),
             r=R.uniform(0.082, 0.098),
             rot=(R.uniform(-0.5, 0.5), R.uniform(-0.5, 0.5), R.uniform(0, 3.1)),
             mat=[M("mat_i_steel"), M("mat_i_steel_b"),
                  M("mat_i_steel_bright")][i % 3],
             kind="nasal" if i % 2 else "great")


def shield_lean(m, x, y, z, r=0.26, face=None):
    """A shield propped on edge against something. Its rim is a full circle of
    highlight: the cheapest legibility in the room."""
    shield_round(m, x, y, z + r * 0.92, r=r, rot=(math.radians(76), 0, 0.4),
                 face=face or M("mat_i_oxblood"), rim=M("mat_i_steel_b"),
                 boss=True, straps=False)


def helm_block(m, x, y, z, r=0.125, kind="great", mat=None):
    """A helm on a turned display block -- how a shop shows its best piece."""
    m.lathe((x, y, z), [(0, 0), (0.088, 0), (0.092, 0.016), (0.060, 0.040),
                        (0.056, 0.090), (0.072, 0.112), (0, 0.118)],
            M("mat_i_beam"), seg=14)
    helm(m, x, y, z + 0.125, r=r, rot=(0.06, 0, 0.35),
         mat=mat or M("mat_i_steel_bright"), kind=kind)


def polish_bench(m, x, y, z=0.0, rot=0.0):
    """A low bench where pieces get buffed: a leather-faced wheel on a crank,
    a tray of rouge and rags, a half-finished pauldron in the vice. The
    armour shop's second working corner, opposite the counter."""
    P = frame((x, y, z), (0, 0, rot))
    wood, st = M("mat_i_beam"), M("mat_i_steel")
    m.box(P(0, 0, 0.72), (0.54, 0.30, 0.026), M("mat_i_counter"), rot=(0, 0, rot))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.strand([P(sx * 0.46, sy * 0.22, 0.0), P(sx * 0.44, sy * 0.20, 0.70)],
                     0.032, wood, seg=5)
    m.box(P(0, 0, 0.28), (0.46, 0.026, 0.024), wood, rot=(0, 0, rot))
    # the buffing wheel on its crank
    m.lathe(P(-0.30, 0.02, 0.90), [(0, 0), (0.10, 0), (0.19, 0.014),
                                   (0.19, 0.052), (0.10, 0.066), (0, 0.066)],
            M("mat_i_leather"), seg=18, aspect=(1.0, 1.0), rot=0.0)
    m.cyl(P(-0.30, 0.02, 0.923), 0.016, 0.34, M("mat_i_iron"), seg=10,
          rot=(0, math.pi / 2, rot))
    for sx in (-1, 1):
        m.strand([P(-0.30 + sx * 0.16, 0.02, 0.746), P(-0.30 + sx * 0.16, 0.02, 0.923)],
                 0.020, wood, seg=4)
    m.strand([P(-0.13, 0.02, 0.923), P(-0.05, 0.12, 0.923)], 0.012,
             M("mat_i_iron"), seg=4)
    # the vice, with a pauldron half polished in its jaws
    m.box(P(0.34, -0.06, 0.79), (0.070, 0.055, 0.045), M("mat_i_iron"), rot=(0, 0, rot))
    m.cyl(P(0.34, -0.20, 0.79), 0.014, 0.18, M("mat_i_iron"), seg=8,
          rot=(math.pi / 2, 0, rot))
    m.arc_lathe(P(0.34, -0.02, 0.83), [(0.10, 0), (0.115, 0.075), (0.095, 0.15)],
                st, seg=12, a0=-2.8, a1=0.4, aspect=(1.0, 0.78))
    oil_rag(m, *P(0.14, 0.10, 0.746), r=0.095, seed=8.8)
    parts_bin(m, *P(-0.02, -0.14, 0.746), w=0.10, d=0.08, n=7, kind="plate")


def peg_hook_pot(m, x, y, z, face=1.0, r=0.105, h=0.26, drop=0.20, mat=None):
    """A pot / bucket / helm slung on a wall peg by a short cord."""
    m.strand([(x, y, z), (x + face * 0.14, y, z - drop)], 0.010,
             M("mat_rope"), seg=4)
    bucket(m, x + face * 0.14, y, z - drop - h - 0.08, r=r, h=h, mat=mat)


def peg_hang(m, x, y, z, fn=None, side=1.0, drop=0.16, cord=0.009,
             cord_mat=None, **kw):
    """Generic wall-peg hanger: a cord out to the peg tip, then whatever the
    skin wants hanging off it. `side` is the direction out of the wall -- named
    `side`, not `face`, because several props take a `face` MATERIAL and a
    table row has to be able to pass both."""
    m.strand([(x, y, z), (x + side * 0.10, y, z - drop)], cord,
             cord_mat or M("mat_i_leather"), seg=3)
    if fn is not None:
        fn(m, x + side * 0.10, y, z - drop, **kw)


def floor_lantern(m, x, y, z=0.0, h=0.92, energy=120.0, name="LAMP_floor"):
    """A lantern on a spike stand, stood on the floor beside a display piece.

    In a shop full of dark metal this is not decoration: a practical BELOW eye
    level throws light up the front of a standing piece, which is the only way
    a breastplate or a polearm gets an edge instead of a hole. The armoury
    warning -- dark metal in a dark room disappears -- is answered here as much
    as in the shader.
    """
    ir = M("mat_i_iron")
    m.lathe((x, y, z), [(0, 0), (0.13, 0), (0.135, 0.018), (0.055, 0.030),
                        (0.030, 0.040), (0, 0.044)], ir, seg=14)
    m.cyl((x, y, z + h * 0.42), 0.018, h * 0.76, ir, seg=8)
    m.lathe((x, y, z + h * 0.80), [(0, 0), (0.075, 0), (0.079, 0.014),
                                   (0.062, 0.028), (0.056, 0.040)], ir, seg=12)
    m.lathe((x, y, z + h * 0.80 + 0.040), [(0.054, 0), (0.060, 0.010),
                                           (0.062, 0.145), (0.052, 0.182)],
            M("mat_i_lampglass"), seg=12)
    m.lathe((x, y, z + h * 0.80 + 0.222), [(0.056, 0), (0.060, 0.010),
                                           (0.030, 0.038), (0, 0.052)], ir, seg=12)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        m.strand([(x + 0.058 * math.cos(a), y + 0.058 * math.sin(a), z + h * 0.80 + 0.040),
                  (x + 0.058 * math.cos(a), y + 0.058 * math.sin(a), z + h * 0.80 + 0.222)],
                 0.005, ir, seg=3)
    m.lathe((x, y, z + h * 0.80 + 0.075), [(0, 0), (0.012, 0.006), (0.008, 0.046),
                                           (0, 0.060)], M("mat_i_flame"), seg=8)
    if energy:
        point(name, (x, y, z + h * 0.80 + 0.125), energy, (1.0, 0.62, 0.28),
              radius=0.05)
