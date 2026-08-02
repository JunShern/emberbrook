"""gate_gorgeface.py — THE GORGE FACE: the gate tier's north side, built as a
slope down to the boatyard instead of a vertical cut over a bottomless slot.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_gorgeface.py -- [save] [--report <json>]

THE REDLINE.  User, annotating the gate plate 2026-08-02
(docs/qa/refs/user_gate_landing_bluecut_20260802.png): *"...replace that with a
cliff that slopes down to the boatyard."*  The same clause was in the 2026-07-31
annotation ("replace with the more-realistic cliff face?") and had never been
built: `gate_rimchop.py` moved the LIP and left the FACE exactly as it was.

WHAT THE FACE ACTUALLY WAS, measured before anything was touched
(tools/gate_gorge_census.py / _census2.py on today's master, Blender ray-cast,
the repo's only visibility oracle):

  * `Terrain.top()` drops `30.0 * over**1.30` past the rim and clamps at
    BASEZ = -8: within ~1.3 m of the lip the sheet is already 30 m down.  It is
    not a cliff, it is a curtain, and it wears `mat_rock` (Mapping scale 0.17 =
    a 5.9 m texture period) flat-shaded, so it reads as a smear, not as rock.
  * `has_ground` refuses everything past `rim(x) + 1.35`, and the next surface
    north — `yard_ground`'s crest — does not start until y = 17.4.  Down-rays on
    a 0.25 m grid found a bottomless band on 128 of 137 columns over x 0..34,
    y 8.0..17.75: **the slot DAYLOG 2026-08-02 recorded as "863 of 3,111 cells
    hit NOTHING" is still there, and the apron chop made it WIDER** (it now
    opens at y = 8.25 where the rim was cut back, against 12.5 at the yard).
  * From the solved `gate` camera, 15.05% of the frame is rays that reach that
    void unoccluded.  That is the hole the user keeps pointing at.

WHAT THIS BUILDS.  One object, `gate_gorgeface`: a rock slope from just under
the tier's own lip down and north to `yard_ground`'s crest at y = 17.55, where
the existing north bank takes over and carries on down to the boatyard.  So the
ground is continuous from the gate road to the water for the first time.

  * The lip it starts from is `gate_lib.Terrain.rim()` — THE SAME ONE LIST the
    chop is authored in — so a future rim edit re-derives this face for free.
  * Every seam height is RAY-CAST off the master, never assumed: the top row
    takes the tier's own measured surface just inside the lip (LIP_BACK, and it
    walks further in if the tier is not under that first sample), the bottom row
    takes `yard_ground`'s own measured crest.  Nothing is welded to a number.
  * Relief is the south wall's proven language (cliff-completion.md AS BUILT 3):
    seven incommensurate octaves, two strata biases, four fissures, a talus
    swell at the toe, and NO periodic ledges — a regular vertical period under
    this town's raking key reads as a quarry.
  * Smooth-shaded (AS BUILT 4: `from_pydata` leaves every polygon flat, and a
    flat 0.35 m facet at 30 m is a visible rectangle).
  * `mat_gate_gorgeface`, a COPY of `mat_gate_cliff` — the material the built
    faces 13-20 m from a camera already wear — so `gate_cliffface` is untouched
    and this face cannot be told apart from the cliff beside it.  NOT
    `mat_rock_farwall`: that is an atmospheric-perspective material and this
    face stands 22-35 m from the gate camera (AS BUILT 1).

THE GATE THIS TOOL PRINTS EVERY RUN: the same 0.25 m down-ray census, re-run
after the build over the face's own footprint.  A single cell that still hits
nothing is a hole in the thing built to close the hole, and the tool says so.

REVERT: the object is built from scratch each run and is the only thing this
file touches; deleting `gate_gorgeface` restores the master exactly.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
sys.path.insert(0, REPO + "/tools")
import gate_lib
from gate_lib import Terrain

OBJ = "gate_gorgeface"
MAT = "mat_gate_gorgeface"
SRC_MAT = "mat_gate_cliff"

X0, X1 = gate_lib.GX0 + 0.17, 18.90    # +0.17 = half a ground cell (ST 0.34):
                            # a down-ray at exactly GX0 lands on the sheet's
                            # boundary edge, where no CELL is filled, and the
                            # top seam misses on that one column.
                            # X0 FOLLOWS THE GROUND SHEET (2026-08-02, user redline #4:
                            # GX0 1.20 -> -3.22, so the entry road runs off the bottom of
                            # the gate frame).  Hardcoded at 1.20 this face would have
                            # stopped where the old sheet stopped and left the extension's
                            # own north lip standing over the same bottomless slot this
                            # tool exists to close — and its coverage gate would have
                            # reported 0 misses, because it only censuses its own
                            # footprint.  A constant that is really "wherever the ground
                            # starts" has to say so.
                            # EAST OF 18.9 IS NOT ROCK: gate_lib's
                            # own regime note says the town is already stacked under the
                            # tier there and the ground is a corbelled PLATE, and
                            # `gate_corbels` starts at x = 19.05 — the first draft ran to
                            # x = 21 and geometry_audit named 14 corbel faces 0.36 m
                            # inside this face.  A rock slope under a corbelled gallery
                            # is a modelling error, not a tight fit.
DX = 0.35                   # ~29 px/edge at the gate camera's 30 m
DY = 0.35
JOIN_Y = 17.55              # yard_ground's crest, measured (17.40..17.50)
LIP_BACK = 0.10             # start this far INSIDE the lip so the sheet buries the top
                            # of the old curtain and cannot crack.  0.35 put the top row
                            # 0.21 m inside `gate_arch`, whose north pier foot stands at
                            # y = 7.09 against a rim of 7.10 — at the arch the tier has
                            # no spare depth at all.
END_SKIRT = 3.0             # west/east end walls, so the sheet is not paper

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
NOFACE = "--noface" in argv          # render the BEFORE at identical draft settings
REPORT = PROBE = None
for i, a in enumerate(argv):
    if a == "--report":
        REPORT = argv[i + 1]
    if a == "--probe":
        PROBE = argv[i + 1]

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# THE SEAM MAY ONLY BE TAKEN OFF GROUND.  The first draft sampled the first hit
# under (x, rim-0.35) and got 28.84 m on some columns: the arch, the toll-yard
# awning, loose clutter and rim veg all stand over the lip, and welding the
# face's top row to a ROOF would have hung it in the air.  Terrain only.
GROUND = ("gate_ground", "gate_road", "yard_ground", "shelf_ground", "qm_ground",
          "gate_paving", "shelf_paving", "qm_paving")


def down(x, y, top=45.0, accept=None):
    """First surface under (x, y).  Returns (z, name) or (None, None).
    `accept`: only these object names count; everything else is stepped past."""
    p = Vector((x, y, top))
    d = Vector((0, 0, -1))
    for _ in range(32):
        hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, p, d, distance=200.0)
        if not hit:
            return None, None
        nm = obj.name
        ok = (nm in accept) if accept else not nm.startswith(("walk_", "bar_"))
        if ok:
            return loc.z, nm
        p = loc + d * 0.02
    return None, None


def rim(x):
    return Terrain.rim(None, x)


def probe(path, res=(1008, 576), samples=28):
    """A DRAFT of the solved `gate` camera, in this session, off this blend.

    Same camera construction as cine_bake.build_cam and the same grade the
    shipped plate carries (AgX / Medium High Contrast / exposure 0.15, the one
    place it is written).  Draft resolution and samples, because the question is
    composition, not pixels — the shipped plate is the verdict and this is the
    thing that stops a shipped plate being spent on a guess.
    """
    import json as _json
    sol = _json.load(open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))
    c = [k for k in sol["cameras"] if k["id"] == "gate"][0]
    D = sol["defaults"]
    sc.view_settings.view_transform = D.get("view_transform", "AgX")
    sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
    sc.view_settings.exposure = D.get("exposure", 0.0)
    cd = bpy.data.cameras.new("probe_gate")
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(c["fov"])
    cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
    cam = bpy.data.objects.new("probe_gate", cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(c["pos"])
    cam.rotation_euler = (Vector(c["aim"]) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'METAL'
        cp.get_devices()
        for d in cp.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.filepath = path
    sc.render.film_transparent = False
    bpy.ops.render.render(write_still=True)
    print("PROBE %s  %dx%d @ %d spp" % (path, res[0], res[1], samples))


if NOFACE:
    o = bpy.data.objects.get(OBJ)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    if PROBE:
        probe(PROBE)
    print("--noface: BEFORE probe only; nothing built, nothing saved")
    raise SystemExit(0)


# ------------------------------------------------------------------ measure
print("MEASURING the two seams off the master (ray-cast, not assumed)")
cols = []
NCOL = int(math.ceil((X1 - X0) / DX))
for ci in range(NCOL + 1):
    x = X0 + (X1 - X0) * ci / NCOL      # lands exactly on both ends
    ry = rim(x)
    # THE LIP IS WHERE THE TIER STILL STANDS, not where rim() says it stops.
    # `rim()` is the authored lip and `gate_ground` skirts a little inside it on
    # some columns; the first draft sampled rim-0.35 blind and one column came
    # back at z = 6.97 — already 17 m down the old curtain — which built a
    # panel that ran UPHILL (-47 deg).  Walk inward until the tier is under us.
    ztop = ntop = None
    ytop = ry - LIP_BACK
    for k in range(6):
        yy = ry - LIP_BACK - 0.15 * k
        z, n = down(x, yy, accept=GROUND)
        if z is not None and z >= 22.5:
            ztop, ntop, ytop = z, n, yy
            break
    # THE BOTTOM SEAM IS SEARCHED NORTHWARD, not fixed at JOIN_Y (2026-08-02).
    # `yard_ground`'s crest is the bank this face is meant to land on and it exists
    # over x >= 1.0; WEST of that — the 4.4 m the ground sheet gained when GX0 went
    # to -3.22 so the entry road could leave the frame — there is no bank at all
    # (measured: down-rays at x -3.2..1.0 MISS from y 11 to 19 and then find
    # `riverbed` at z -3.9). Fixed at JOIN_Y this tool REFUSED those columns and
    # exited, which would have left the new west lip standing over exactly the
    # bottomless slot the file exists to close. So the seam walks north until it
    # meets a measured surface and welds there; nothing is assumed, the y it found
    # is reported per column, and west of the bank that surface is the river's own
    # bed, which is the honest answer to "what is under the end of the promontory".
    zbot = nbot = None
    ybot = JOIN_Y
    for k in range(int(round(8.0 / DY)) + 1):
        yy = JOIN_Y + DY * k
        z, n = down(x, yy, accept=GROUND + ("riverbed",))
        if z is not None:
            zbot, nbot, ybot = z, n, yy
            break
    cols.append(dict(x=round(x, 3), y0=round(ytop, 3), z0=ztop, n0=ntop,
                     y1=round(ybot, 3), z1=zbot, n1=nbot))
# THE TOE LINE MUST BE CONTINUOUS ACROSS COLUMNS.  Where the bottom seam jumps
# (yard_ground's crest at y=17.55 for x>=1.0, the riverbed ~0.7 m further north
# west of it) two neighbouring columns end at different y, the quad between them
# is skewed, and the coverage census found the gap it leaves: exactly one cell at
# (0.45, 17.55).  A max filter over +-2 columns pulls the seam out to the furthest
# of its neighbours and the height is RE-MEASURED there — the y moves, the z is
# still ray-cast, so nothing is welded to a number.
raw_y1 = [c["y1"] for c in cols]
for i, c in enumerate(cols):
    y = max(raw_y1[max(0, i - 2):i + 3])
    if y > c["y1"] + 1e-6:
        z, n = down(c["x"], y, accept=GROUND + ("riverbed",))
        if z is not None:
            c["y1"], c["z1"], c["n1"] = round(y, 3), z, n

bad = [c for c in cols if c["z0"] is None or c["z1"] is None]
if bad:
    print("SEAM MISS on %d columns — the face cannot be welded there:" % len(bad))
    for c in bad[:10]:
        print("   x=%.2f  top=%s  bot=%s" % (c["x"], c["z0"], c["z1"]))
    raise SystemExit(1)
print("   columns %d   top z %.2f..%.2f (%s)   bottom z %.2f..%.2f (%s)" % (
    len(cols),
    min(c["z0"] for c in cols), max(c["z0"] for c in cols),
    ", ".join(sorted({c["n0"] for c in cols})),
    min(c["z1"] for c in cols), max(c["z1"] for c in cols),
    ", ".join(sorted({c["n1"] for c in cols}))))
print("   bottom seam y %.2f..%.2f (JOIN_Y %.2f; columns that had to walk north: %d)"
      % (min(c["y1"] for c in cols), max(c["y1"] for c in cols), JOIN_Y,
         sum(1 for c in cols if c["y1"] > JOIN_Y + 1e-6)))

# ------------------------------------------------------------------ the shape
# Seven incommensurate octaves.  The frequencies share no rational ratio, so the
# field never repeats over the 20 m run; the angles keep any one octave from
# lining up with the slope's own fall line (a fall-line-aligned wave reads as
# fluting).  Amplitudes fall as ~0.63^k: enough relief to catch the 53 deg key
# at the brow, little enough that the toe still reads as talus.
OCT = [(0.41, 0.61, 0.40, 0.13), (0.73, 1.97, 0.29, 2.41),
       (1.19, 3.44, 0.23, 1.07), (1.93, 0.29, 0.165, 3.92),
       (3.11, 2.53, 0.108, 0.58), (5.03, 4.71, 0.068, 2.90),
       (8.17, 1.33, 0.043, 4.36)]
# Two RIDGED bands.  A pure sum of sines is smooth everywhere, and the first
# draft of this face rendered as putty for exactly that reason: the eye reads
# rock by its CREASES.  `(1-|sin|)**2` is C1 at the crest and sharp in the
# trough, so these cut gullies without adding a period the sines do not have.
RIDGE = [(1.07, 0.94, 0.40, 0.31), (0.61, 2.75, 0.30, 1.86)]
FISSURE = [(3.9, 0.42, 1.20), (8.6, 0.33, 1.00), (13.4, 0.47, 1.35),
           (18.1, 0.36, 0.90)]     # (x, half-width, depth)


def relief(x, y, u):
    """Rock, in metres of displacement along the surface normal's z.

    Tapered to zero at BOTH seams (u=0 the tier lip, u=1 the bank crest) so the
    face welds without a step, and strongest at u~0.45 where the brow is.

    The two lowest octaves are DELIBERATELY small.  The first draft ran them at
    0.95 / 0.60 m over a 20 m run — a period longer than the face is wide — and
    the probe came back as a row of smooth mounds.  The face's SHAPE is the
    profile's job; the octaves' job is texture.
    """
    t = math.sin(math.pi * max(0.0, min(1.0, u))) ** 0.75
    n = 0.0
    for f, a, amp, ph in OCT:
        n += amp * math.sin(f * (x * math.cos(a) + y * math.sin(a)) + ph)
    for f, a, amp, ph in RIDGE:
        s = math.sin(f * (x * math.cos(a) + y * math.sin(a)) + ph)
        n -= amp * (1.0 - abs(s)) ** 2
    # two strata biases at incommensurate pitch — they also crosscut the
    # material's own streaking, which is the reason the south wall wanted them
    n += 0.24 * math.sin(0.83 * y + 1.13) + 0.15 * math.sin(1.41 * y + 2.67)
    for fx, hw, dep in FISSURE:
        n -= dep * math.exp(-((x - fx) / hw) ** 2) * (0.35 + 0.65 * t)
    return n * t


def talus(u):
    """The toe piles up: +0.9 m at u~0.8, nothing at either seam.  A cliff that
    meets a bank with a sharp crease is a cut; a cliff that meets it with a
    swell is a slope."""
    return 0.9 * math.exp(-((u - 0.80) / 0.26) ** 2) * (1.0 - math.exp(-6.0 * u))


BROW = 0.45     # profile exponent; < 1 = the ground falls away AT the lip


def profile(z0, z1, u):
    """Steep brow, easing onto a talus bench.  `u**BROW` puts most of the drop
    in the first quarter of the run, which is what a rock face does and what a
    straight ramp does not.

    THE EXPONENT IS ALSO WHAT `shelf-west` COSTS, and that is why it is small.
    `shelf-west` stands at (13.0, 22.3, 25.1) — NORTH of this face and barely
    above the tier — so everything this face keeps high stands between that
    camera and the gate tier's edge, which is the thing that frame exists to
    show.  Measured on 1008x576/28 spp drafts: at 0.62 the face filled the
    lower-right third of shelf-west and buried the parapet, the lanterns and
    the timber understructure.  A SMALLER exponent is better in BOTH frames —
    the gate reads a lip that falls away, shelf-west reads a talus bench well
    below its own eyeline — so there is no trade here, only a wrong first
    guess.
    """
    return z0 + (z1 - z0) * (u ** BROW)


# ------------------------------------------------------------------ build
verts, faces = [], []
rows = []          # rows[i] = list of vertex indices for column i
for c in cols:
    x, y0, y1, z0, z1 = c["x"], c["y0"], c["y1"], c["z0"], c["z1"]
    span = y1 - y0
    n = max(3, int(round(span / DY)))
    idx = []
    for j in range(n + 1):
        u = j / n
        y = y0 + span * u
        z = profile(z0, z1, u) + talus(u) + relief(x, y, u)
        idx.append(len(verts))
        verts.append((x, y, z))
    c["n"] = n
    rows.append(idx)

for i in range(len(rows) - 1):
    a, b = rows[i], rows[i + 1]
    n = min(len(a), len(b)) - 1
    for j in range(n):
        faces.append((a[j], a[j + 1], b[j + 1], b[j]))

# end walls, so the sheet is a solid and not a piece of paper seen edge-on
for which, row in (("w", rows[0]), ("e", rows[-1])):
    low = []
    for vi in row:
        vx, vy, vz = verts[vi]
        low.append(len(verts))
        verts.append((vx, vy, vz - END_SKIRT))
    for j in range(len(row) - 1):
        if which == "w":
            faces.append((row[j], low[j], low[j + 1], row[j + 1]))
        else:
            faces.append((row[j], row[j + 1], low[j + 1], low[j]))

old = bpy.data.objects.get(OBJ)
if old:
    bpy.data.objects.remove(old, do_unlink=True)
me = bpy.data.meshes.new(OBJ)
me.from_pydata(verts, [], faces)
me.validate()
for p in me.polygons:
    p.use_smooth = True                      # AS BUILT 4
ob = bpy.data.objects.new(OBJ, me)

src = bpy.data.materials.get(SRC_MAT)
if src is None:
    raise SystemExit("missing source material %s" % SRC_MAT)
m = bpy.data.materials.get(MAT)
if m is None:
    m = src.copy()
    m.name = MAT
me.materials.append(m)

host = bpy.data.objects.get("gate_ground")
coll = host.users_collection[0] if host and host.users_collection else sc.collection
coll.objects.link(ob)

edges = 0.0
for e in me.edges:
    a, b = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
    edges += (a - b).length
mean_edge = edges / max(1, len(me.edges))
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
print("\nBUILT %s   %d verts  %d polys  mean edge %.3f m" % (OBJ, len(me.vertices), len(me.polygons), mean_edge))
print("   bbox  %s .. %s" % ([round(min(p[i] for p in bb), 2) for i in range(3)],
                             [round(max(p[i] for p in bb), 2) for i in range(3)]))
print("   material %s (copy of %s)" % (MAT, SRC_MAT))

# slope angles actually delivered, per column
angs = []
for c, row in zip(cols, rows):
    z0 = verts[row[0]][2]
    z1 = verts[row[-1]][2]
    dy = c["y1"] - c["y0"]
    angs.append(math.degrees(math.atan2(z0 - z1, dy)))
print("   mean fall %.1f deg   range %.1f..%.1f deg   run %.1f..%.1f m" % (
    sum(angs) / len(angs), min(angs), max(angs),
    min(c["y1"] - c["y0"] for c in cols), max(c["y1"] - c["y0"] for c in cols)))

# ------------------------------------------------------------------ the gate
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
miss, tot, missing = 0, 0, []
x = X0
while x <= X1 + 1e-6:
    y = rim(x) + 0.10
    while y <= JOIN_Y:
        hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, Vector((x, y, 45.0)), Vector((0, 0, -1)), distance=200.0)
        tot += 1
        if not hit:
            miss += 1
            missing.append((round(x, 2), round(y, 2)))
        y += 0.25
    x += 0.25
print("\nCOVERAGE GATE — down-rays over the face's own footprint after the build")
print("   cells %d   MISS %d (%.2f%%)" % (tot, miss, 100.0 * miss / max(1, tot)))
if miss:
    print("   FIRST 12 HOLES: %s" % missing[:12])

if REPORT:
    json.dump(dict(cols=[{k: v for k, v in c.items()} for c in cols],
                   verts=len(me.vertices), polys=len(me.polygons),
                   mean_edge=mean_edge, miss=miss, tot=tot), open(REPORT, "w"))
    print("SAVED %s" % REPORT)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED BLEND %s" % bpy.data.filepath)

if PROBE:
    probe(PROBE)
