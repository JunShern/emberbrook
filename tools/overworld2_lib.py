"""overworld2_lib.py — round-2 shared parts: the tar boat, the village dock, the
procedural foliage atlases, the tree scatter, and the bake plumbing.

Round 2 branches off style D, so it does NOT rebuild the world: overworld2_build.py
imports overworld_build (round 1) for the field, the Prop accumulator and
build_base().  Everything NEW to round 2 lives here so the four variants share it.

Design rule for the whole round (the user's hard constraint): the world map must
cost far less authoring time than a town.  So every addition here is either
analytic (the boat is a parametric clinker shell, the dock is four numbers) or a
scatter over the shared field.  Nothing is hand-placed.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector, Matrix

import overworld_lib as L

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEXDIR = os.path.join(ROOT, "tools/textures/overworld")


# ------------------------------------------------------------------ tiny helpers
def poly(p, c, pts):
    """Append one n-gon to a Prop, tagged with an art class."""
    b = set(p.bm.faces)
    vs = [p.bm.verts.new(Vector(t)) for t in pts]
    try:
        p.bm.faces.new(vs)
    except ValueError:
        pass
    p.bm.normal_update()
    p._tag(b, c)


def beam(p, c, a, b_, r, rr=None):
    """A box beam from a to b_ with half-thickness r (and rr across)."""
    a, b_ = np.asarray(a, float), np.asarray(b_, float)
    d = b_ - a
    ln = float(np.linalg.norm(d))
    if ln < 1e-6:
        return
    dz = d / ln
    up = np.array([0.0, 0.0, 1.0])
    if abs(dz[2]) > 0.95:
        up = np.array([1.0, 0.0, 0.0])
    ax = np.cross(up, dz)
    ax /= np.linalg.norm(ax)
    ay = np.cross(dz, ax)
    rr = r if rr is None else rr
    m = Matrix(((ax[0], ay[0], dz[0], 0), (ax[1], ay[1], dz[1], 0),
                (ax[2], ay[2], dz[2], 0), (0, 0, 0, 1)))
    m = Matrix.Translation(Vector((a + b_) / 2)) @ m @ Matrix.Diagonal(
        Vector((r * 2, rr * 2, ln)).to_4d())
    bset = set(p.bm.faces)
    bmesh.ops.create_cube(p.bm, size=1.0, matrix=m)
    p._tag(bset, c)


def enable_gpu():
    """Try Metal for the Cycles bakes; silently fall back to CPU."""
    try:
        pr = bpy.context.preferences.addons["cycles"].preferences
        for t in ("METAL", "OPTIX", "CUDA", "HIP"):
            try:
                pr.compute_device_type = t
            except Exception:
                continue
            pr.get_devices()
            devs = [d for d in pr.devices if d.type == t]
            if devs:
                for d in pr.devices:
                    d.use = (d.type == t)
                print("  cycles device: %s (%s)" % (t, devs[0].name))
                return "GPU"
    except Exception as e:
        print("  cycles GPU unavailable (%s)" % e)
    return "CPU"


_GPU = None


def bake(sc, ob, img, btype, samples=8, direct=False, indirect=False,
         color=True, margin=20):
    """Bake one pass of `ob` into `img`.  The caller must already have put a
    TEX_IMAGE node holding `img` in as the active node of ob's active material."""
    global _GPU
    if _GPU is None:
        _GPU = enable_gpu()
    prev = sc.render.engine
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.device = _GPU
    try:
        sc.cycles.use_denoising = samples < 64 and btype in ("DIFFUSE", "COMBINED", "AO")
    except Exception:
        pass
    bk = sc.render.bake
    bk.use_pass_direct = direct
    bk.use_pass_indirect = indirect
    try:
        bk.use_pass_color = color
    except Exception:
        pass
    bk.margin = margin
    bk.use_selected_to_active = False
    # background Blender has no window, so bpy.context.scene is NOT this scene.
    # temp_override is the only way to aim ops.object.bake at a specific scene.
    vl = sc.view_layers[0]
    for o in sc.objects:
        o.select_set(False, view_layer=vl)
    ob.select_set(True, view_layer=vl)
    vl.objects.active = ob
    # bake's poll wants scene + view_layer + an ACTIVE, SELECTED object all named in
    # the override; a background Blender supplies none of them from bpy.context
    with bpy.context.temp_override(scene=sc, view_layer=vl, object=ob,
                                   active_object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        bpy.ops.object.bake(type=btype)
    sc.render.engine = prev


def set_bake_target(mat, img):
    nt = mat.node_tree
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = img
    # `for x in nt.nodes: x.select = (x is n)` silently does NOTHING: iterating a
    # bpy collection hands back a fresh proxy each time, so `is` never matches and
    # the bake target ends up deselected.  Clear, then select the node itself.
    for x in nt.nodes:
        x.select = False
    n.select = True
    nt.nodes.active = n
    return n


def img_array(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def img_write(img, arr):
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.update()


# ------------------------------------------------------- procedural leaf atlases
def _stamp(buf, cx, cy, ang, ra, rb, rgb, alpha=1.0):
    """Rasterise one rotated ellipse into an HxWx4 float buffer."""
    h, w = buf.shape[:2]
    r = int(max(ra, rb)) + 2
    x0, x1 = max(0, int(cx) - r), min(w, int(cx) + r + 1)
    y0, y1 = max(0, int(cy) - r), min(h, int(cy) + r + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx - cx, yy - cy
    ca, sa = math.cos(ang), math.sin(ang)
    u, v = (dx * ca + dy * sa) / ra, (-dx * sa + dy * ca) / rb
    d = u * u + v * v
    m = d <= 1.0
    if not m.any():
        return
    sub = buf[y0:y1, x0:x1]
    shade = (1.0 - 0.22 * np.clip(d, 0, 1))[..., None]
    sub[..., :3] = np.where(m[..., None], np.asarray(rgb) * shade, sub[..., :3])
    sub[..., 3] = np.where(m, alpha, sub[..., 3])


def leaf_atlas(name, path, size=1024, autumn=0.07, seed=5, tint=(0.44, 0.63, 0.28)):
    """A 2x2 atlas of four alpha-cut leaf clusters, drawn from ~1100 leaves.

    Real leaf silhouettes are what make a card read as foliage rather than as a
    billboard, and a procedural atlas costs one build step instead of a hunt for
    licensed foliage art.  Saved as PNG (glTF keeps its alpha; a JPEG would not)."""
    rng = np.random.RandomState(seed)
    buf = np.zeros((size, size, 4), np.float32)
    c = size // 2
    base = np.array(tint, float)
    aut = np.array([0.62, 0.31, 0.09])
    for cell in range(4):
        ox, oy = (cell % 2) * c, (cell // 2) * c
        R = c * 0.44
        for i in range(290):
            # cluster shape: a lobed blob, denser toward the middle
            a = rng.rand() * 2 * math.pi
            rr = R * (rng.rand() ** 0.52) * (0.80 + 0.34 * math.sin(3.0 * a + cell))
            lx, ly = ox + c / 2 + math.cos(a) * rr, oy + c / 2 + math.sin(a) * rr * 0.88
            k = rr / R
            col = base * (0.68 + 0.42 * (1.0 - k) + 0.26 * rng.rand())
            if rng.rand() < autumn:
                col = aut * (0.65 + 0.5 * rng.rand())
            sz = c * (0.052 + 0.030 * rng.rand()) * (1.12 - 0.3 * k)
            _stamp(buf, lx, ly, rng.rand() * math.pi, sz, sz * (0.42 + 0.22 * rng.rand()), col)
    im = bpy.data.images.new(name, size, size, alpha=True)
    im.filepath_raw = path
    im.file_format = "PNG"
    img_write(im, buf[::-1])
    im.save()
    return im


def grass_atlas(name, path, size=512, seed=9, tint=(0.46, 0.58, 0.24)):
    """A 2x2 atlas of grass/scrub tufts — the meadow scatter's alpha card."""
    rng = np.random.RandomState(seed)
    buf = np.zeros((size, size, 4), np.float32)
    c = size // 2
    base = np.array(tint, float)
    for cell in range(4):
        ox, oy = (cell % 2) * c, (cell // 2) * c
        for i in range(150):
            # a DENSE clump, not a sprinkle: a card showing four thin blades reads
            # as litter on the ground, not as grass
            bx = ox + c * (0.5 + (rng.rand() - 0.5) * 0.34)
            lean = (rng.rand() - 0.5) * c * 0.62
            hgt = c * (0.46 + 0.48 * rng.rand())
            col = base * (0.62 + 0.60 * rng.rand())
            tipc = col * 0.7 + np.array([0.55, 0.46, 0.16]) * 0.5
            n = 16
            for k in range(n):
                s = k / (n - 1.0)
                x = bx + lean * s * s
                y = oy + c * 0.06 + hgt * s
                w = max(1.2, c * 0.026 * (1.0 - 0.75 * s))
                _stamp(buf, x, y, 0.0, w, w * 1.6, col * (1 - s) + tipc * s)
    im = bpy.data.images.new(name, size, size, alpha=True)
    im.filepath_raw = path
    im.file_format = "PNG"
    img_write(im, buf[::-1])
    im.save()
    return im


# -------------------------------------------------------------- foliage cards
def card(p, c, cx, cy, cz, w, h, yaw, pitch=0.0, cell=0, uvs=None):
    """One alpha-card quad, UV'd into a 2x2 atlas cell.  Records the UV in `uvs`
    (a list parallel to the faces created) because Prop has no UV layer."""
    cw, sw = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    # local right = (cw, sw, 0); local up tilted by pitch away from the card plane
    rx, ry = cw, sw
    ux, uy, uz = -sw * sp, cw * sp, cp
    pts = []
    for (a, b_) in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
        pts.append((cx + rx * a * w / 2 + ux * b_ * h,
                    cy + ry * a * w / 2 + uy * b_ * h,
                    cz + uz * b_ * h))
    poly(p, c, pts)
    u0, v0 = (cell % 2) * 0.5, (cell // 2) * 0.5
    uvs.append([(u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.5), (u0, v0 + 0.5)])


def apply_card_uvs(ob, uvs, name="UVMap"):
    me = ob.data
    uv = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    for pi, poly_ in enumerate(me.polygons):
        if pi >= len(uvs):
            break
        for k, li in enumerate(poly_.loop_indices):
            uv.data[li].uv = uvs[pi][k % 4]


# ------------------------------------------------------------------- tree scatter
def scatter_trees(F, seed, n, min_d2=12.0, near_road=3.0, cluster=0.0):
    """Pick n tree sites on the shared field.  Returns (x, y, z, scale, kind, rot).

    `cluster` >0 biases sites toward earlier accepted sites, which is how style H
    grows hedgerows and copses out of the same one-line scatter the others use."""
    rng = np.random.RandomState(seed)
    vx, vy = L.VILLAGE
    cx, cy = L.CLIFFTOWN
    out = []
    tries = 0
    while len(out) < n and tries < 200000:
        tries += 1
        if cluster > 0 and out and rng.rand() < cluster:
            bx, by = out[rng.randint(len(out))][:2]
            tx, ty = bx + rng.randn() * 5.0, by + rng.randn() * 5.0
            if abs(tx) > 56 or abs(ty) > 42:
                continue
        else:
            tx, ty = rng.uniform(-56, 56), rng.uniform(-42, 42)
        if any((tx - a) ** 2 + (ty - b) ** 2 < min_d2 for a, b, *_ in out):
            continue
        gz = float(F.sample(np.array([tx]), np.array([ty]))[0])
        wlv = float(L.water_level(np.array([F._river_dist([tx], [ty])[1][0]]))[0])
        if gz < wlv + 1.1 or gz > wlv + 26.0:
            continue
        if float(F.slope_at(np.array([tx]), np.array([ty]))[0]) > 0.85:
            continue
        if float(F.river_dist([tx], [ty])[0]) < 4.2:
            continue
        if float(F.road_dist([tx], [ty])[0]) < near_road:
            continue
        if math.hypot(tx - vx, ty - vy) < 8.0 or math.hypot(tx - cx, ty - cy) < 9.0:
            continue
        out.append((tx, ty, gz, rng.uniform(0.85, 1.25), rng.rand(),
                    rng.uniform(0, 6.283)))
    return out


# --------------------------------------------------------------------- the boat
# THE TAR BOAT — "boat_tar".  The player leaves Dellhollow on this at the chapter
# finale and later drives it on this overworld, so it is named for the shared
# library and modelled to the Boatyard's own hull language: black-pitched clinker
# planking, workboat beam, sharp stem, transom stern, open thwarted interior.
BOAT_LEN, BOAT_BEAM = 4.6, 1.62


def _hull_shape(s):
    """Half-beam factor along the hull, s=0 transom -> s=1 stem."""
    full = np.sin(np.pi * np.clip(s, 0, 1) ** 0.78) ** 0.62
    transom = 0.46 * (1.0 - L.sstep(0.0, 0.24, s))
    return np.maximum(full, transom)


def build_boat(p, cls, org, ang, rig="mast", scale=1.0, strakes=6):
    """Append boat_tar to Prop p.  `cls` maps role -> art class.

    rig: "mast" | "furled" | "bare" | "canopy" — the one thing each style varies.
    """
    HULL, WOOD, DARK, CANVAS, ROPE, LAMP = (cls["hull"], cls["wood"], cls["dark"],
                                            cls["canvas"], cls["rope"], cls["lamp"])
    Ln, Bm = BOAT_LEN * scale, BOAT_BEAM * scale
    ca, sa = math.cos(ang), math.sin(ang)

    def W(x, y, z):
        return (org[0] + x * ca - y * sa, org[1] + x * sa + y * ca, org[2] + z)

    N = 26
    s = np.linspace(0.0, 1.0, N)
    xs = (s - 0.5) * Ln
    hb = _hull_shape(s) * Bm / 2
    keel = 0.30 * scale * (2 * s - 1) ** 2 * np.array([1.0])
    keel = 0.26 * scale * ((2 * s - 1) ** 2)
    top = scale * (0.60 + 0.11 * (2 * s - 1) + 0.34 * (2 * s - 1) ** 2)
    LAP = 0.042 * scale

    def shell(k0, k1, side, lap=True):
        """One clinker strake, k in 0..1 from keel to sheer."""
        def edge(k, bulge):
            y = hb * np.sin(k * math.pi / 2) ** 0.62
            z = keel + (top - keel) * (k ** 1.15)
            return [W(float(xs[i]), side * float(y[i] + bulge), float(z[i]))
                    for i in range(N)]
        b = LAP if lap else 0.0
        p.strip(HULL, edge(k0, b), edge(k1, 0.0))

    for k in range(strakes):
        k0, k1 = k / strakes, (k + 1) / strakes
        shell(k0, k1, +1)
        shell(k0, k1, -1)

    # transom: close the stern between the two edge chains
    def chain(side, k0=0.0, k1=1.0, m=7):
        ks = np.linspace(k0, k1, m)
        y = hb[0] * np.sin(ks * math.pi / 2) ** 0.62
        z = keel[0] + (top[0] - keel[0]) * ks ** 1.15
        return [W(float(xs[0]), side * float(y[i]), float(z[i])) for i in range(m)]
    p.strip(HULL, chain(+1), chain(-1))

    # inner skin for the top three strakes (the only interior a camera ever sees)
    k_floor = 0.52
    for k in range(3):
        k0 = k_floor + (1.0 - k_floor) * k / 3.0
        k1 = k_floor + (1.0 - k_floor) * (k + 1) / 3.0
        for side in (+1, -1):
            def edge(k, sh=0.055 * scale):
                y = hb * np.sin(k * math.pi / 2) ** 0.62 - sh
                z = keel + (top - keel) * (k ** 1.15)
                return [W(float(xs[i]), side * float(max(y[i], 0.01)), float(z[i]))
                        for i in range(N)]
            p.strip(DARK, edge(k1), edge(k0))

    # gunwale cap: joins the outer sheer to the inner sheer, both sides
    for side in (+1, -1):
        yo = hb * np.sin(math.pi / 2) ** 0.62
        zt = top
        p.strip(WOOD,
                [W(float(xs[i]), side * float(yo[i] + 0.035 * scale), float(zt[i] + 0.03 * scale)) for i in range(N)],
                [W(float(xs[i]), side * float(max(yo[i] - 0.075 * scale, 0.01)), float(zt[i] + 0.03 * scale)) for i in range(N)])

    # floorboards
    yf = hb * np.sin(k_floor * math.pi / 2) ** 0.62 - 0.06 * scale
    zf = keel + (top - keel) * k_floor ** 1.15
    p.strip(DARK, [W(float(xs[i]), float(max(yf[i], 0.0)), float(zf[i])) for i in range(N)],
            [W(float(xs[i]), -float(max(yf[i], 0.0)), float(zf[i])) for i in range(N)])

    def at(sv):
        i = float(np.interp(sv, s, xs))
        return i, float(np.interp(sv, s, hb)), float(np.interp(sv, s, top)), \
            float(np.interp(sv, s, keel))

    # ribs / frames, visible against the topsides
    for sv in (0.16, 0.30, 0.44, 0.58, 0.72, 0.86):
        x, y, t, kz = at(sv)
        yy = y * 0.985
        beam(p, DARK, W(x, -yy, kz + 0.10 * scale), W(x, yy, kz + 0.10 * scale),
             0.035 * scale, 0.05 * scale)
    # thwarts (seats)
    for sv in (0.30, 0.52, 0.74):
        x, y, t, kz = at(sv)
        yy = y * 0.96
        beam(p, WOOD, W(x, -yy, t - 0.09 * scale), W(x, yy, t - 0.09 * scale),
             0.10 * scale, 0.045 * scale)
    # stem + stern posts
    x1, y1, t1, k1z = at(1.0)
    beam(p, WOOD, W(x1 - 0.16 * scale, 0, k1z), W(x1 + 0.06 * scale, 0, t1 + 0.30 * scale),
         0.055 * scale, 0.07 * scale)
    x0, y0, t0, k0z = at(0.0)
    beam(p, WOOD, W(x0 + 0.10 * scale, 0, k0z), W(x0 - 0.02 * scale, 0, t0 + 0.16 * scale),
         0.05 * scale, 0.06 * scale)
    # rudder + tiller
    beam(p, DARK, W(x0 - 0.06 * scale, 0, k0z - 0.30 * scale),
         W(x0 - 0.06 * scale, 0, t0 + 0.05 * scale), 0.035 * scale, 0.13 * scale)
    beam(p, WOOD, W(x0 - 0.02 * scale, 0, t0 + 0.10 * scale),
         W(x0 + 0.85 * scale, 0, t0 + 0.02 * scale), 0.035 * scale, 0.035 * scale)
    # oars stowed along the port gunwale
    for k, sv in enumerate((0.34, 0.42)):
        x, y, t, kz = at(sv)
        beam(p, WOOD, W(x - 1.05 * scale, (0.26 + 0.11 * k) * scale, t - 0.07 * scale),
             W(x + 1.05 * scale, (0.36 + 0.11 * k) * scale, t - 0.11 * scale),
             0.030 * scale, 0.030 * scale)
    # mooring cleat + bow rope stub (the dock end is added by build_dock)
    xb, yb, tb, kb = at(0.92)
    beam(p, WOOD, W(xb, -0.10 * scale, tb + 0.05 * scale),
         W(xb, 0.10 * scale, tb + 0.05 * scale), 0.03 * scale, 0.03 * scale)

    xm, ym, tm, km = at(0.60)
    if rig == "mast":
        beam(p, WOOD, W(xm, 0, km), W(xm, 0, km + 3.1 * scale), 0.055 * scale, 0.055 * scale)
        beam(p, WOOD, W(xm - 0.9 * scale, 0, km + 2.55 * scale),
             W(xm + 1.0 * scale, 0, km + 2.72 * scale), 0.035 * scale, 0.035 * scale)
        for side in (-1, 1):
            beam(p, ROPE, W(xm, 0, km + 3.0 * scale), W(x0 + 0.4 * scale, side * y0 * 0.8, t0),
                 0.014 * scale, 0.014 * scale)
        beam(p, ROPE, W(xm, 0, km + 3.0 * scale), W(x1 - 0.3 * scale, 0, t1 + 0.2 * scale),
             0.014 * scale, 0.014 * scale)
    elif rig == "furled":
        beam(p, WOOD, W(xm, 0, km), W(xm, 0, km + 2.8 * scale), 0.055 * scale, 0.055 * scale)
        # sail furled onto its yard, lashed — a workboat at its mooring
        # a furled sail is a slim lashed bundle on its yard, not a plank: at 0.15
        # radius it read as a beige board bolted across the boat
        beam(p, WOOD, W(xm - 1.5 * scale, 0.12 * scale, km + 1.62 * scale),
             W(xm + 1.6 * scale, 0.12 * scale, km + 1.86 * scale),
             0.030 * scale, 0.030 * scale)
        beam(p, CANVAS, W(xm - 1.32 * scale, 0.12 * scale, km + 1.56 * scale),
             W(xm + 1.42 * scale, 0.12 * scale, km + 1.80 * scale),
             0.085 * scale, 0.070 * scale)
        for lz in (-0.9, -0.2, 0.5, 1.15):
            beam(p, ROPE, W(xm + lz * scale, 0.12 * scale, km + 1.70 * scale + lz * 0.04),
                 W(xm + lz * scale, 0.12 * scale, km + 1.44 * scale + lz * 0.04),
                 0.012 * scale, 0.012 * scale)
        for side in (-1, 1):
            beam(p, ROPE, W(xm, 0, km + 2.7 * scale), W(x0 + 0.5 * scale, side * y0 * 0.8, t0),
                 0.014 * scale, 0.014 * scale)
    elif rig == "canopy":
        for k, sv in enumerate((0.34, 0.50, 0.66, 0.82)):
            x, y, t, kz = at(sv)
            yy = y * 0.93
            m = 7
            arc = [W(x, yy * math.cos(a), t + 0.62 * scale * math.sin(a))
                   for a in np.linspace(0.0, math.pi, m)]
            for i in range(m - 1):
                beam(p, WOOD, arc[i], arc[i + 1], 0.028 * scale, 0.028 * scale)
        # tarp over the after half
        left, right = [], []
        for sv in np.linspace(0.30, 0.86, 9):
            x, y, t, kz = at(float(sv))
            yy = y * 0.95
            left.append(W(x, -yy, t + 0.30 * scale))
            right.append(W(x, yy, t + 0.30 * scale))
        mid = []
        for i, sv in enumerate(np.linspace(0.30, 0.86, 9)):
            x, y, t, kz = at(float(sv))
            mid.append(W(x, 0.0, t + 0.66 * scale))
        p.strip(CANVAS, left, mid)
        p.strip(CANVAS, mid, right)
    else:                                    # "bare": a working hull, oars only
        beam(p, WOOD, W(xm - 0.2 * scale, 0, km + 0.02 * scale),
             W(xm + 0.2 * scale, 0, km + 0.02 * scale), 0.05 * scale, 0.30 * scale)

    # stern lantern — an ORDINARY lantern (world canon: heartlights are rare and
    # magical; a river workboat carries a plain one)
    beam(p, WOOD, W(x0 + 0.15 * scale, 0, t0 + 0.16 * scale),
         W(x0 + 0.15 * scale, 0, t0 + 0.62 * scale), 0.022 * scale, 0.022 * scale)
    b = set(p.bm.faces)
    p.cube(LAMP, W(x0 + 0.15 * scale, 0, t0 + 0.50 * scale),
           (0.15 * scale, 0.15 * scale, 0.20 * scale), rz=ang)
    return W


POOL = dict(A=9.5, Bv=6.4, Bf=2.8, depth=1.25)


def pool_frame(F):
    """Where the village meets the river — and the frame the mooring basin is cut in.

    The shared field's river is only ~5u wide in the open valley: narrower than the
    boat is long.  Rather than edit round 1's field (which would invalidate style D
    as the reference row), round 2 CARVES a backwater into each style's own terrain
    copy.  It is 20 lines, it is analytic, and it is the kind of edit a world map is
    allowed to cost."""
    vx, vy = L.VILLAGE
    rt, rx, ry = L.river_pts(601)
    i = int(np.argmin(np.hypot(rx - vx, ry - vy)))
    t = float(rt[i])
    tg = np.array([rx[i + 1] - rx[i - 1], ry[i + 1] - ry[i - 1]])
    tg /= np.linalg.norm(tg)
    nrm = np.array([-tg[1], tg[0]])
    if nrm[1] < 0:
        nrm = -nrm
    ctr = np.array([float(rx[i]), float(ry[i])]) + tg * 1.0
    wl = float(L.water_level(np.array([t]))[0])
    return dict(ctr=ctr, tg=tg, nrm=nrm, wl=wl, t=t)


def pool_w(x, y, fr):
    """Basin weight in 0..1 — an ellipse elongated along the river and dug harder
    into the village bank than into the far one."""
    dx, dy = np.asarray(x, float) - fr["ctr"][0], np.asarray(y, float) - fr["ctr"][1]
    u = (dx * fr["tg"][0] + dy * fr["tg"][1]) / POOL["A"]
    v = dx * fr["nrm"][0] + dy * fr["nrm"][1]
    vv = v / np.where(v >= 0, POOL["Bv"], POOL["Bf"])
    return 1.0 - L.sstep(0.58, 1.0, np.sqrt(u * u + vv * vv))


def pool_height(F, x, y, fr):
    h = F.sample(x, y)
    tgt = fr["wl"] - POOL["depth"]
    w = pool_w(x, y, fr)
    return np.minimum(h, h + (tgt - h) * w)      # only ever DIGS, never fills


def carve_pool(ob, F, fr):
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    tgt = fr["wl"] - POOL["depth"]
    w = pool_w(co[:, 0], co[:, 1], fr)
    co[:, 2] = np.minimum(co[:, 2], co[:, 2] + (tgt - co[:, 2]) * w)
    me.vertices.foreach_set("co", co.ravel())
    me.update()


def pool_water(p, cls, fr, n=28):
    """The basin's water surface — water_* so the runtime never stands on it."""
    a = np.linspace(0, 2 * math.pi, n)
    ring = []
    for th in a:
        u = math.cos(th) * POOL["A"] * 0.90
        v = math.sin(th)
        v *= (POOL["Bv"] if v >= 0 else POOL["Bf"]) * 0.90
        ring.append((float(fr["ctr"][0] + fr["tg"][0] * u + fr["nrm"][0] * v),
                     float(fr["ctr"][1] + fr["tg"][1] * u + fr["nrm"][1] * v),
                     fr["wl"] - 0.02))
    ctr = (float(fr["ctr"][0]), float(fr["ctr"][1]), fr["wl"] - 0.02)
    p.strip(cls, ring, [ctr] * len(ring))


def build_dock(F, p_deck, p_props, cls, fr, boat_rig="mast", scale=1.0):
    """The village dock: a plank jetty out into the mooring basin with boat_tar
    alongside.  Returns everything the cameras need."""
    WOOD, DARK, ROPE = cls["wood"], cls["dark"], cls["rope"]
    ctr, tg, nrm, wl = fr["ctr"], fr["tg"], fr["nrm"], fr["wl"]
    # walk out along the village-side normal until the CARVED bank rises clear of
    # the water; that is where the jetty root belongs
    ds = np.arange(2.0, POOL["Bv"] + 9.0, 0.25)
    pts_ = ctr[None, :] + nrm[None, :] * ds[:, None]
    hs = pool_height(F, pts_[:, 0], pts_[:, 1], fr)
    k = int(np.argmax(hs >= wl + 0.45))
    if hs[k] < wl + 0.45:
        k = len(ds) - 1
    root = pts_[k]
    head = ctr + nrm * 1.1
    deck_z = wl + 0.74
    n = 9
    ts = np.linspace(0, 1, n)
    pts = root[None, :] * (1 - ts[:, None]) + head[None, :] * ts[:, None]
    HWD = 1.05
    p_deck.strip(WOOD,
                 [(float(x + tg[0] * HWD), float(y + tg[1] * HWD), deck_z) for x, y in pts],
                 [(float(x - tg[0] * HWD), float(y - tg[1] * HWD), deck_z) for x, y in pts])
    for kk in (0.10, 0.42, 0.74, 0.98):
        c = root * (1 - kk) + head * kk
        for side in (-1, 1):
            bx = float(c[0] + tg[0] * side * (HWD - 0.14))
            by = float(c[1] + tg[1] * side * (HWD - 0.14))
            gz = float(pool_height(F, np.array([bx]), np.array([by]), fr)[0])
            beam(p_props, DARK, (bx, by, min(gz, wl) - 0.45), (bx, by, deck_z + 0.02),
                 0.085, 0.085)
    for side in (-1, 1):
        bx = float(head[0] + tg[0] * side * (HWD - 0.2))
        by = float(head[1] + tg[1] * side * (HWD - 0.2))
        beam(p_props, WOOD, (bx, by, deck_z), (bx, by, deck_z + 0.52), 0.075, 0.075)

    # boat moored downstream of the jetty, bow upstream, clear of the deck
    bside = -1.0
    bo = head * 0.78 + root * 0.22 + tg * bside * (HWD + BOAT_BEAM * 0.62 * scale) \
        - nrm * 0.7
    bang = math.atan2(-tg[1], -tg[0])
    borg = (float(bo[0]), float(bo[1]), wl - 0.20 * scale)
    build_boat(p_props, cls, borg, bang, rig=boat_rig, scale=scale)
    bowx = borg[0] + math.cos(bang) * BOAT_LEN * 0.42 * scale
    bowy = borg[1] + math.sin(bang) * BOAT_LEN * 0.42 * scale
    tie = head + tg * bside * (HWD - 0.2)
    beam(p_props, ROPE, (bowx, bowy, borg[2] + 0.62 * scale),
         (float(tie[0]), float(tie[1]), deck_z + 0.42), 0.016, 0.016)
    return dict(head=(float(head[0]), float(head[1]), deck_z), boat=borg, ang=bang,
                root=(float(root[0]), float(root[1])),
                nrm=(float(nrm[0]), float(nrm[1])), tg=(float(tg[0]), float(tg[1])),
                ctr=(float(ctr[0]), float(ctr[1])), wl=wl, deck_z=deck_z)


def dock_path(F, p, cls_dirt, root, fr):
    """A short walk spur from the village green down to the jetty root."""
    vx, vy = L.VILLAGE
    a = np.array([vx, vy], float)
    b_ = np.array(root, float)
    n = 16
    ts = np.linspace(0, 1, n)
    # a slight bow so it is not a ruler line
    d = b_ - a
    nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    pts = a[None, :] * (1 - ts[:, None]) + b_[None, :] * ts[:, None] \
        + nrm[None, :] * (np.sin(ts * math.pi) * 2.1)[:, None]
    tgs = np.gradient(pts, axis=0)
    tgs /= np.linalg.norm(tgs, axis=1)[:, None]
    nx, ny = -tgs[:, 1], tgs[:, 0]
    z = pool_height(F, pts[:, 0], pts[:, 1], fr) + 0.09
    HW = 0.85
    p.strip(cls_dirt,
            [(pts[i, 0] + nx[i] * HW, pts[i, 1] + ny[i] * HW, z[i]) for i in range(n)],
            [(pts[i, 0] - nx[i] * HW, pts[i, 1] - ny[i] * HW, z[i]) for i in range(n)])
