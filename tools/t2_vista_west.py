"""t2_vista_west.py — THE THREE GAPS THE RE-AIMED CAMERAS OPENED.  A vista patch
in the idiom of docs/plans/cliff-completion.md, phases C1/C2.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_vista_west.py -- [parts west,skirt,farwest] [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_vista_west.py -- revert save

WHY THIS EXISTS, AND WHY THE OLD AUDIT DID NOT CATCH IT.

`tools/t2_probe_leak.py` certified this town at 0.00% sky-leak on thirteen of
seventeen cameras.  That certificate was true and it is now partly void: the
cameras were re-solved and re-aimed (`frameExits` on, quay-east retired,
boatyard/gate/shelf-west re-aimed again in 0c0b522), and **a re-aimed camera
looks somewhere nothing was ever audited**.  Re-run against the CURRENT
`public/townmap/dellhollow.cameras.solved.json` the town leaks on five cameras:

    crossing        4.30%   1,234 rays   — the east closure stops 22 m short
                                           (fixed in tools/t2_cliff_east.py)
    shelf-west      2.48%     710 rays   — the south wall stops at x = -35
    gate            0.10%      29 rays   — under the south wall's toe
    boatyard        0.01%       2 rays   — under the south wall's toe
    north-landing   0.00%       1 ray    — over the upstream ridges' saddle

This tool closes the last four.  It adds objects only; nothing existing is
edited, so `revert` is a delete and is exact.

---- `west`:  cliff_town_west2,  x -82..-35 --------------------------------

shelf-west now stands at (47.13, 22.68, 27.41) and looks WSW along the town's
own south wall.  Its 710 leak rays are NEARLY TANGENT to that wall — elevation
-4.5..+4.0 deg, 43% downward — so they enter the strip in front of the face
around x = -25 and slide along it, descending in y about 0.32 m per metre of x,
and they pass the wall's WEST END at x = -35 still in front of the rock.  The
west end cap runs from the face BACKWARD to y = -9.6; in front of the face there
is nothing to cap, and correctly so.  The wall simply ends while the camera is
still looking along it.

Traced against candidate faces, the westmost crossing of the fan is x = -67.4 at
y = -0.35 and x = -73.7 at y = -1.6: the deeper the face, the further west a
tangential ray gets before it meets rock.  So the extension **shallows as it runs
west** — a taper from the full seven-octave `depth()` at x = -35 to a 0.7 m
skin at x = -82.  That is also the right read: a rim running away upstream
flattens into its own haze.  x = -82 leaves 8 m of margin on the worst ray.

TWO THINGS ARE COPIED FROM tools/t2_cliff_south.py AND MUST STAY COPIES:

  * `ZBANDS`/`ZR` — the ONE shared z-row list.  The extension's column at
    x = -35 has to place bit-identical vertices against `cliff_town_west`'s, or
    the join is a T-junction, and a T-junction on this wall is a pinhole to the
    world background: the exact defect the wall was built to repair.
  * `depth()` with its OCTAVES/FISSURES — same reason, plus the taper weight is
    exactly 1.0 at x = -35 so that column is the south wall's own numbers.

It wears `mat_rock_townwall` (the wall's own material, derived from
`mat_shelf_cliff`), NOT `mat_rock_farwall`: t2_cliff_south's AS-BUILT note 1 is
emphatic that farwall is an atmospheric-perspective material and reads as a cold
blue-grey slab when it is the near rock.  Recession out here comes from
`fx_haze_mid` / `fx_haze_far` / `fx_haze_rim`, which already stand in front of
this ground at x -74..-23.

---- `skirt`:  cliff_town_skirt,  z -40..-8.8 ------------------------------

`gate`'s 29 rays plunge at -40 to -42 deg and cross the wall's face plane at
z -7.6..-11.4; `boatyard`'s 2 cross it at z -18.5..-19.2.  The wall's bottom row
is z = -9.0 and its bottom cap strip runs back from there, so a ray steep enough
goes UNDER the toe and out.  A skirt box under the whole run closes it, exactly
as `fx_ridge_upstream_skirt` closed shelf-east's 22-pixel hairline in C2 — a new
object below, rather than an edit to vertex data someone else built.

Its top is z = -8.8 (0.2 m into the wall) and its front is y = -0.30 (0.05 m
proud of Y_FRONT), so there is no crack at either join.  Nothing else is down
there: `gate_ground` bottoms out at z = -8.35, `lf_ground` and
`lf_riverbed_tail` at -7.6.

---- `farwest`:  fx_ridge_far_west,  x -104..-98 ---------------------------

north-landing leaks ONE ray: azimuth 179.3 deg, elevation +3.1 deg, dead west
along the valley at the very top of frame (ndc y 0.98).  It threads the saddle
between `fx_ridge_upstream_mid` (tops at z 16.66) and `fx_ridge_upstream` (tops
at 24.51) and keeps going.  A small card standing across it at x = -100 catches
it: at that plane the ray is at y = 33.2, z = 18.1.

Deliberately SMALL — 50 x 20 m, top at z = 26, i.e. eleven metres below the
town's own z = 37 horizon — because the west vista is an ACCEPTED composition
(the boatyard hero shot) and a new ridge that rises into its skyline would be a
taste regression traded for one pixel.  It is `fx_`-prefixed, so
`tools/town_export.py`'s FX strip keeps it out of the runtime GLB, same as every
other vista card.  If the post-build per-camera visibility census shows it in any
frame other than north-landing's top edge, drop it: `parts west,skirt`.
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_vista_west.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
PARTS = None
if "parts" in argv:
    PARTS = set(argv[argv.index("parts") + 1].split(","))
want = lambda p: PARTS is None or p in PARTS

COLL = "CONTEXT"
MAT = "mat_rock_townwall"          # derived by t2_cliff_south.py; asserted below
MAT_TEMPLATE = "mat_shelf_cliff"
MAT_FAR = "mat_rock_far"
MAP_SCALE = 1.05

# ---- the south wall's own constants.  COPIES, and they must stay copies. -----
X0_OLD = -35.0                      # where t2_cliff_south.py's run begins
Z0, Z1 = -9.0, 37.0
Y_FRONT = -0.35
Y_BACK = -8.50
BACK_CAP = -9.60
ZBANDS = [(-9.0, 0.0, 2.20), (0.0, 30.0, 1.00), (30.0, 37.0, 2.20)]
OCTAVES = [
    (1.45, 0.0410,  0.0170,  0.60),
    (0.92, 0.0930, -0.0480,  2.40),
    (0.58, 0.1810,  0.0850, -1.10),
    (0.36, 0.3470, -0.1630,  0.95),
    (0.22, 0.6710,  0.3110,  3.05),
    (0.13, 1.2900, -0.5930,  1.70),
    (0.075, 2.4700, 1.1300, -2.20),
]
FISSURES = [
    (-8.0, 2.1, 2.40), (48.0, 1.6, 1.90), (72.0, 1.5, 2.30),
    (95.0, 1.9, 2.00), (110.0, 1.3, 1.80), (126.0, 1.5, 1.70),
]

# ---- this tool's own additions ----------------------------------------------
WEST = "cliff_town_west2"
WX0, WX1 = -82.0, -35.0
WCOL = 2.6                          # 90-140 m out: ~26 px per edge at 2688x1536
TAPER_SKIN = 0.70                   # face depth at the far west end

SKIRT = "cliff_town_skirt"
SKX0, SKX1 = -82.0, 137.0
SKY0, SKY1 = -9.60, -0.30
SKZ0, SKZ1 = -40.0, -8.80

FARW = "fx_ridge_far_west"
FWX0, FWX1 = -104.0, -98.0
FWY0, FWY1 = 10.0, 60.0
FWZ0, FWZ1 = 6.0, 26.0

NAMES = [WEST, SKIRT, FARW]


def axis(a, b, step):
    """inclusive sample positions from a to b, <= step apart, endpoints exact"""
    n = max(1, int(math.ceil((b - a) / step - 1e-9)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def rows():
    out = []
    for a, b, s in ZBANDS:
        for v in axis(a, b, s):
            if not out or abs(v - out[-1]) > 1e-7:
                out.append(v)
    return out


ZR = rows()


def depth(x, z):
    """t2_cliff_south.py::depth, verbatim.  Do not 'improve' it here — the whole
    point of the copy is that the shared column at x = -35 is bit-identical."""
    d = 1.60 + 0.050 * max(0.0, z - 4.0)
    for a, fx, fz, ph in OCTAVES:
        d += a * math.sin(x * fx + z * fz + ph)
    d += 0.62 * math.sin(z * 1.142 + 0.35 * math.sin(x * 0.060) + 1.10)
    d += 0.26 * math.sin(z * 2.350 + 0.60 * math.sin(x * 0.140) - 0.40)
    d -= 0.80 * math.exp(-((z - 7.5) / 3.4) ** 2)
    for fx, fw, fd in FISSURES:
        d += fd * math.exp(-(((x - (fx + 0.16 * (z - 14.0))) / fw) ** 2))
    w = math.exp(-(((x + 2.0) / 26.0) ** 2))
    d += 0.85 * w * math.exp(-(((z - (12.0 + 0.34 * (x + 25.0))) / 2.8) ** 2))
    return d


def taper(x):
    """1.0 at x = -35 (the join), 0.0 at x = -82.  Smoothstep so the rim does not
    kink where the two patches meet."""
    t = (x - WX0) / (WX1 - WX0)
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def face_y(x, z):
    w = taper(x)
    d = w * depth(x, z) + (1.0 - w) * TAPER_SKIN
    return -max(-Y_FRONT, min(-Y_BACK, d))


def new_mesh(name, verts, faces, mat, cname, smooth=True):
    old = bpy.data.objects.get(name)
    if old:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if smooth:
        # from_pydata() leaves every polygon flat; the town buys its smoothness
        # with tessellation and every built cliff face is smooth-shaded.
        for poly in me.polygons:
            poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    (bpy.data.collections.get(cname) or bpy.context.scene.collection).objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, cname):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
         (2, 6, 7, 3), (3, 7, 4, 0)]
    return new_mesh(name, v, f, mat, cname, smooth=False)


# ================================================================ REVERT ======
if REVERT:
    gone = []
    for n in NAMES:
        o = bpy.data.objects.get(n)
        if o:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
            gone.append(n)
    print("REVERT removed: %s" % (", ".join(gone) or "nothing"))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ================================================================= BUILD ======
mat = bpy.data.materials.get(MAT)
if mat is None:
    mat = bpy.data.materials[MAT_TEMPLATE].copy()
    mat.name = MAT
    mp = next(n for n in mat.node_tree.nodes if n.type == 'MAPPING')
    mp.inputs['Rotation'].default_value = (math.radians(90.0), 0.0, 0.0)
    mp.inputs['Scale'].default_value = (MAP_SCALE, MAP_SCALE, MAP_SCALE)
    print("DERIVED %s from %s" % (MAT, MAT_TEMPLATE))
stats = {}

# ---------------------------------------------------------------- the west ---
if want("west"):
    XS = axis(WX0, WX1, WCOL)
    nx, nz = len(XS), len(ZR)
    verts, faces = [], []
    for i, x in enumerate(XS):
        for j, z in enumerate(ZR):
            verts.append((x, face_y(x, z), z))
    for i in range(nx - 1):
        for j in range(nz - 1):
            a = i * nz + j
            faces.append((a, a + nz, a + nz + 1, a + 1))
    # CLOSE THE SHELL.  A heightfield sheet is not a wall: a ray that grazes a
    # crest tangentially passes behind the surface and escapes out of the back.
    # That is how the south wall's first full build leaked 6-32 rays on seven
    # cameras, and tangency is precisely the geometry this patch is answering.
    base = len(verts)                                   # top strip
    verts += [(x, BACK_CAP, Z1) for x in XS]
    for i in range(nx - 1):
        a = i * nz + (nz - 1)
        faces.append((a, (i + 1) * nz + (nz - 1), base + i + 1, base + i))
    base2 = len(verts)                                  # bottom strip
    verts += [(x, BACK_CAP, Z0) for x in XS]
    for i in range(nx - 1):
        a = i * nz
        faces.append(((i + 1) * nz, a, base2 + i, base2 + i + 1))
    base3 = len(verts)                                  # WEST end cap
    verts += [(WX0, BACK_CAP, z) for z in ZR]
    for j in range(nz - 1):
        faces.append((j, j + 1, base3 + j + 1, base3 + j))
    base4 = len(verts)                                  # back panel
    verts += [(x, BACK_CAP, z) for x in (WX0, WX1) for z in (Z0, Z1)]
    faces.append((base4 + 0, base4 + 2, base4 + 3, base4 + 1))
    # NO east cap at x = -35: `cliff_town_west` already carries the run's west
    # side strip there, and this patch's column at that x is bit-identical to
    # its own, so the two shells share an edge exactly.
    ob = new_mesh(WEST, verts, faces, mat, COLL)
    ds = [-face_y(x, z) for x in XS for z in ZR]
    stats["west"] = dict(name=WEST, verts=len(verts), polys=len(faces),
                         x=[WX0, WX1], z=[Z0, Z1], col_m=WCOL, rows=nz,
                         depth_min=round(min(ds), 3), depth_max=round(max(ds), 3),
                         material=MAT)
    print("BUILT %-22s %5d verts %5d polys  x %.0f..%.0f  z %.0f..%.0f  "
          "%d cols x %d rows  face depth %.2f..%.2f m"
          % (WEST, len(verts), len(faces), WX0, WX1, Z0, Z1, nx, nz,
             min(ds), max(ds)))
    # the join has to be exact, so ASSERT it rather than trust it
    join = [(x, z) for x in XS if abs(x - X0_OLD) < 1e-9 for z in ZR]
    bad = [(x, z) for x, z in join
           if abs(face_y(x, z) - (-max(-Y_FRONT, min(-Y_BACK, depth(x, z))))) > 1e-12]
    print("   join column x=%.1f: %d rows, %d deviating from the south wall's "
          "own depth()  %s" % (X0_OLD, len(join), len(bad),
                               "OK" if not bad else "*** T-JUNCTION RISK ***"))
    if bad:
        sys.exit(1)

# --------------------------------------------------------------- the skirt ---
if want("skirt"):
    ob = box(SKIRT, SKX0, SKX1, SKY0, SKY1, SKZ0, SKZ1, mat, COLL)
    stats["skirt"] = dict(name=SKIRT, verts=8, polys=6, x=[SKX0, SKX1],
                          y=[SKY0, SKY1], z=[SKZ0, SKZ1], material=MAT)
    print("BUILT %-22s     8 verts     6 polys  x %.0f..%.0f y %.2f..%.2f "
          "z %.0f..%.1f  (closes gate's 29 and boatyard's 2 under-toe rays)"
          % (SKIRT, SKX0, SKX1, SKY0, SKY1, SKZ0, SKZ1))

# ------------------------------------------------------------- the far west ---
if want("farwest"):
    mf = bpy.data.materials.get(MAT_FAR)
    if mf is None:
        print("   %s missing — far-west card skipped" % MAT_FAR)
    else:
        box(FARW, FWX0, FWX1, FWY0, FWY1, FWZ0, FWZ1, mf, COLL)
        stats["farwest"] = dict(name=FARW, verts=8, polys=6, x=[FWX0, FWX1],
                                y=[FWY0, FWY1], z=[FWZ0, FWZ1], material=MAT_FAR)
        print("BUILT %-22s     8 verts     6 polys  x %.0f..%.0f y %.0f..%.0f "
              "z %.0f..%.0f  (closes north-landing's single ray; fx_ = stripped "
              "from the GLB)" % (FARW, FWX0, FWX1, FWY0, FWY1, FWZ0, FWZ1))

if PARTS is None:
    json.dump(dict(
        _doc=("GENERATED by tools/t2_vista_west.py — the three gaps the re-aimed "
              "cameras opened west and under the south wall.  The fourth, "
              "crossing's 4.30%, is the north extension of cliff_east_closure in "
              "tools/t2_cliff_east.py."),
        generator="tools/t2_vista_west.py", plan="docs/plans/cliff-completion.md",
        leak_before=dict(crossing=0.0430, shelf_west=0.0248, gate=0.0010,
                         boatyard=0.0001, north_landing=0.000035),
        zbands=ZBANDS, rows=len(ZR), taper_skin_m=TAPER_SKIN,
        objects=stats,
    ), open(MANIFEST, "w"), indent=1)
    print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
