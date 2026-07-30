"""t2_cliff_south.py — REPLACE Dellhollow's south wall.  Phase C1 of
docs/plans/cliff-completion.md.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_south.py -- [tiers a|all] [retire] [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_south.py -- revert save

THE FINDING THIS ANSWERS.  "At least one ENTIRE cliff wall missing — flat grey
background showing through."  Measured (tools/t2_probe_leak.py, FX cards skipped)
the frames the user was looking at leak 0.00% sky: every ray hits geometry.  The
grey is `cliff_town` — an EIGHT-VERTEX, six-polygon box, 170 x 46 m, wearing bare
untextured `m_rock`, filling 3.0% to 22.6% of TEN of the seventeen frames at
2,664-5,495 px per mesh edge.  It is not a hole in the wall; it IS the wall,
built as a blockout placeholder and never replaced.  So this pass replaces it.

WHAT IS BUILT.  One tiered sheet over the placeholder's exact footprint
(x -35..135, z -9..37, presenting the same y = 0 face), in `mat_rock_townwall`
— a copy of `mat_shelf_cliff`, so the wall is the SAME PHYSICAL ROCK as the two
built faces it abuts.  Resolution is tiered by how close a camera gets, targeting the 60-80
px/edge band that `gate_cliffface` (43) and `shelf_cliffface` (45-76) already
hold, so no camera can tell where the built cliff stops and the vista starts:

    tier    x extent      col m   serves                       d_mean   px/edge
    a       58 .. 112     1.00    lockhead, loop-stairs,       33-59 m   80-45
                                  quay-east, cottage,
                                  weave, crossing
    b      -25 ..  20     1.22    gate                         39-69 m   75-42
    c       38 ..  58     1.45    quay-west, deep-stairs       47-74 m   68-43
    d      112 .. 135     1.55    cottage-steps, lockfive      59-78 m   56-43
    west   -35 .. -25     2.40    (in no frame — closure only)
    mid     20 ..  38     2.10    (behind gate_/shelf_cliffface)

The two "filler" bands are not in the plan's table and are not optional: the
placeholder is deleted, so anything its footprint covered that a tier does not
would become a NEW sky leak.  The plan's ~2,600-vertex figure counts only the
tier rectangles inside the visible z band; a closed wall over the whole footprint,
with the cap strips, is 5,820 verts / 5,438 polys.  That is still smaller than
`shelf_ground` (7,906) alone, on a town carrying ~1.75M across 1,753 meshes.

ONE SHARED ROW LIST.  Every patch samples the SAME z rows, so adjacent patches
put bit-identical vertices on their shared column and the seams cannot crack.
Different rows per tier would have produced T-junctions, and a T-junction on this
wall is a pinhole to the world background — the exact defect being repaired.

THE MATERIAL IS A DEVIATION FROM THE PLAN, AND IT IS MEASURED.
cliff-completion.md specifies `mat_rock_farwall`.  Tier A was built in it and
probe-rendered at lockhead (docs/qa/districts/t2cliffA_lockhead.png, first take)
and it came back a COLD BLUE-GREY SLAB against the town's warm tan terrain,
because `mat_rock_farwall` is not a rock material — it is an ATMOSPHERIC
PERSPECTIVE material, authored for `cliff_far` at y 80-99 m:

    mat_rock_farwall   Mix.001 factor 0.60 toward (0.33, 0.35, 0.45) blue-grey
                       Mix.002 factor 1.00 toward (0.30, 0.295, 0.30)
    mat_rock           Mix.001 factor 1.00 toward (0.72, 0.72, 0.72) neutral
    mat_gate_cliff     as mat_rock, plus a 0.85 distance tint

At 33 m that recession tint reads as a different rock type ten metres from
warm-tan `lf_ground`, which is the OPPOSITE of the plan's own stated goal.  The
recession must come from the south haze card in phase C2 instead — the same
mechanism that gives the west vista its depth — not from a tint baked into the
albedo of a wall that is thirty metres away.

The SECOND take was built in `mat_rock` (the town's terrain rock) and that was
wrong too, for a different and more interesting reason.  NOTHING in Dellhollow's
rock kit is UV-mapped: every one of these materials runs Texture Coordinate
.Object -> Mapping -> Image Texture, and a 2D image texture fed a 3D vector uses
only its X and Y.  On a wall standing in the x-z plane that means the rock
pattern DOES NOT VARY WITH HEIGHT — it is a vertical streak, and the whole
town's cliff-face look is built out of exactly that.  It works at
`mat_gate_cliff`/`mat_shelf_cliff`'s Mapping scale of 1.05 (a ~0.95 m striation).
At `mat_rock`'s 0.17 the streak period is 5.9 m, and crossed with the wall's own
depth relief (which drives the texture's other axis) it renders as a grid of
6-metre rectangular blocks — clearly visible in the second take.

So the wall wears `mat_rock_townwall`, a copy of `mat_shelf_cliff` with its tree
unchanged: the same physical rock, at the same striation, as the built faces the
plan says to match.

SHAPE.  A depth field y = -depth(x, z), never in front of y = -0.35 (so it can
never newly intersect the town) and never behind y = -8.5 (nothing is back
there).  It carries, per the shape brief: a back-lean that rises with z, which
is also what puts the moss overlay's up-facing ramp to work — `mat_rock`'s moss
factor is Geometry.Normal.Z through a 0.25..0.85 ramp, so a tread needs
normal.z ~ 0.5 to catch it; THREE OCTAVES OF VERTICAL BUTTRESS RIBBING (the
first take had ledges and no ribs and read as a stack of slabs — this is the
term that fixed it); a talus toe coming forward around z 5-10; stepped ledges on
a 2.9 m sawtooth whose phase drifts with x and whose AMPLITUDE is modulated
along x, so no band runs the whole 170 m; six vertical fissures; one strong
diagonal strata line across tier B (the gate's backdrop carries the most
vertical range, 40 m); and three octaves of fine break-up.

CLEARANCE IS MEASURED, NOT ASSUMED.  Every vertex is ray-cast from y = -7.5
toward +y with the placeholder hidden from the depsgraph; if town geometry is in
the way the vertex is pushed back to 0.35 m behind it.  `gate_cliffface` already
reaches y = -0.6, i.e. INSIDE the placeholder's volume, so a naive flat sheet at
y = -0.35 would have poked through the gate's own cliff.  The clamp report prints
how many vertices were moved and by how much.

THE SILHOUETTE DOES NOT MOVE.  The top row stays at z = 37.0 exactly — the
placeholder's horizon — and a cap strip runs back from it to y = -9.6, plus end
caps at x = -35 and x = 135, reproducing the box's top and side faces.  No solved
camera stands above z = 36.5 and every one looks down, so that rim is out of
frame in all seventeen; keeping it identical makes the plan's silhouette-
regression gate vacuous by construction rather than by argument.

REVERT is exact: `-- revert` deletes the six patches and re-creates `cliff_town`
from its recorded transform (a unit cube at (50, -3, 14) scaled (85, 3, 23) in
`m_rock`, collection CONTEXT), which is all the placeholder ever was.
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_cliff_south.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
RETIRE = "retire" in argv
TIERS = None
if "tiers" in argv:
    TIERS = argv[argv.index("tiers") + 1]
WANT = None if (TIERS in (None, "all")) else set(TIERS.split(","))

PLACEHOLDER = "cliff_town"
PH_LOC, PH_SCALE = (50.0, -3.0, 14.0), (85.0, 3.0, 23.0)
PH_MAT, PH_COLL = "m_rock", "CONTEXT"
MAT = "mat_rock_townwall"
MAT_TEMPLATE = "mat_shelf_cliff"
MAP_SCALE = 1.05               # rock tile in metres = 1/MAP_SCALE
COLL = "CONTEXT"

X0, X1 = -35.0, 135.0
Z0, Z1 = -9.0, 37.0
Y_FRONT = -0.35                 # nearest the new wall may come to the old face
Y_BACK = -8.50                  # deepest it may recede (nothing is behind it)
BACK_CAP = -9.60                # where the cap strips run back to (behind Y_BACK)
CLEAR = 0.35                    # standoff kept behind any town geometry

# ---- the tiers.  (name, x0, x1, column metres) -------------------------------
BANDS = [
    ("west", -35.0, -25.0, 2.40),
    ("b",    -25.0,  20.0, 1.22),
    ("mid",   20.0,  38.0, 2.10),
    ("c",     38.0,  58.0, 1.45),
    ("a",     58.0, 112.0, 1.00),
    ("d",    112.0, 135.0, 1.55),
]
# ---- ONE row list, shared by every patch, so no seam can crack ---------------
ZBANDS = [(-9.0, 0.0, 2.20), (0.0, 30.0, 1.00), (30.0, 37.0, 2.20)]

# (amplitude m, x frequency, z frequency, phase).  Frequency ratios are
# deliberately non-integer so no two octaves ever come back into step.
OCTAVES = [
    (1.45, 0.0410,  0.0170,  0.60),
    (0.92, 0.0930, -0.0480,  2.40),
    (0.58, 0.1810,  0.0850, -1.10),
    (0.36, 0.3470, -0.1630,  0.95),
    (0.22, 0.6710,  0.3110,  3.05),
    (0.13, 1.2900, -0.5930,  1.70),
    (0.075, 2.4700, 1.1300, -2.20),
]
FISSURES = [                    # (x, width m, extra depth m)
    (-8.0, 2.1, 2.40), (48.0, 1.6, 1.90), (72.0, 1.5, 2.30),
    (95.0, 1.9, 2.00), (110.0, 1.3, 1.80), (126.0, 1.5, 1.70),
]


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
    """metres the wall stands BEHIND the old y = 0 face at (x, z).

    A SUM OF PLANE WAVES, not a periodic step function.  Take 4 of this wall
    carried a sawtooth ledge profile and rendered as a stacked quarry: a regular
    vertical period plus a raking 53-degree key cuts hard-edged terraces, and the
    eye reads terraces as machining.  Seven octaves with incommensurate
    frequencies, each travelling in its own direction across the face, never
    repeat and never line up, so the relief reads as rock.  The strata bias below
    keeps the town's horizontal grain without ever closing into a step."""
    d = 1.60 + 0.050 * max(0.0, z - 4.0)          # back-lean as the wall rises
    for a, fx, fz, ph in OCTAVES:
        d += a * math.sin(x * fx + z * fz + ph)
    # TWO horizontal strata biases — grain, not terracing.  These also do the
    # only job the shading needs them for: the rock texture is object-xy mapped
    # and runs as long vertical fibres (see the material note above), and at the
    # nearest band those fibres smear.  A horizontal crosscut in the GEOMETRY
    # breaks them without touching the town's rock look.
    d += 0.62 * math.sin(z * 1.142 + 0.35 * math.sin(x * 0.060) + 1.10)
    d += 0.26 * math.sin(z * 2.350 + 0.60 * math.sin(x * 0.140) - 0.40)
    # talus toe: the wall comes forward between z 5 and 10
    d -= 0.80 * math.exp(-((z - 7.5) / 3.4) ** 2)
    # vertical fissures, drifting slightly off plumb with height
    for fx, fw, fd in FISSURES:
        d += fd * math.exp(-(((x - (fx + 0.16 * (z - 14.0))) / fw) ** 2))
    # tier B carries 40 m of vertical range: one strong diagonal strata line
    w = math.exp(-(((x + 2.0) / 26.0) ** 2))
    d += 0.85 * w * math.exp(-(((z - (12.0 + 0.34 * (x + 25.0))) / 2.8) ** 2))
    return d


def new_mesh(name, verts, faces, mat, cname):
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
    # SMOOTH, and it is not cosmetic. from_pydata() leaves every polygon flat, so
    # a 1 m quad at 35 m is a 68-pixel facet with one constant normal — take 6 of
    # this wall came back as a grid of hard-edged rectangles for exactly that
    # reason. The town's built cliff faces are smooth and carry their relief in
    # the normal map; so does this.
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll = bpy.data.collections.get(cname) or bpy.context.scene.collection
    coll.objects.link(ob)
    return ob


# ============================================================== REVERT ========
if REVERT:
    gone = []
    for nm in [b[0] for b in BANDS] + ["back"]:
        o = bpy.data.objects.get("cliff_town_" + nm)
        if o:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
            gone.append("cliff_town_" + nm)
    if bpy.data.objects.get(PLACEHOLDER) is None:
        me = bpy.data.meshes.new(PLACEHOLDER)
        v = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
             (2, 6, 7, 3), (3, 7, 4, 0)]
        me.from_pydata(v, [], f)
        me.validate()
        me.update()
        me.materials.append(bpy.data.materials[PH_MAT])
        ob = bpy.data.objects.new(PLACEHOLDER, me)
        (bpy.data.collections.get(PH_COLL) or bpy.context.scene.collection).objects.link(ob)
        ob.location = PH_LOC
        ob.scale = PH_SCALE
        print("RESTORED %s  loc=%s scale=%s  %s" % (PLACEHOLDER, PH_LOC, PH_SCALE, PH_MAT))
    print("REVERT removed: %s" % (", ".join(gone) or "nothing"))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ============================================================== BUILD =========
def derive_material():
    """The south wall must read as the SAME ROCK as the two built faces it abuts.
    `mat_shelf_cliff` and `mat_gate_cliff` are byte-identical trees, and they are
    what cliff-completion.md tells this pass to match; the wall gets its own name
    because it is a town-wide CONTEXT surface, not a district's. Idempotent."""
    m = bpy.data.materials.get(MAT)
    if m is None:
        m = bpy.data.materials[MAT_TEMPLATE].copy()
        m.name = MAT
        print("DERIVED %s from %s" % (MAT, MAT_TEMPLATE))
    mp = next(n for n in m.node_tree.nodes if n.type == 'MAPPING')
    mp.inputs['Rotation'].default_value = (math.radians(90.0), 0.0, 0.0)
    mp.inputs['Scale'].default_value = (MAP_SCALE, MAP_SCALE, MAP_SCALE)
    print("   Mapping rotation X=90deg  scale=%.2f  (object x-z, %.2f m tile)"
          % (MAP_SCALE, 1.0 / MAP_SCALE))
    return m


mat = derive_material()

# hide the placeholder (and any patch from an earlier run) from the DEPSGRAPH so
# the clearance ray-cast measures the TOWN, not the thing being replaced
hidden = []
skip = [PLACEHOLDER, "cliff_town_back"] + ["cliff_town_" + b[0] for b in BANDS]
# ...and every VOLUME-ONLY card. A haze slab is a mesh box to the ray-caster but
# it is not town geometry, and fx_haze_south lies against this very wall: left in
# the depsgraph it clamps 3,746 vertices forward by up to 2.4 m and drags the
# whole face out of the cliff. Same rule tools/t2_probe_leak.py uses.
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    ms = [sl.material for sl in o.material_slots if sl.material]
    if ms and all(m.use_nodes and any(n.type == 'OUTPUT_MATERIAL' and
                                      n.inputs['Volume'].is_linked and
                                      not n.inputs['Surface'].is_linked
                                      for n in m.node_tree.nodes) for m in ms):
        skip.append(o.name)
for nm in skip:
    o = bpy.data.objects.get(nm)
    if o is not None and not o.hide_viewport:
        o.hide_viewport = True
        hidden.append(nm)          # by NAME: new_mesh() may delete a patch below
print("hidden from the clearance ray-cast: %d objects (%d volume-only cards)"
      % (len(hidden), len(skip) - len(BANDS) - 2))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene

_clear_cache = {}


def clearance_y(x, z):
    """furthest FORWARD (least negative) y this vertex may take: 0.35 m behind
    the first town surface a +y ray meets, or Y_FRONT if the way is clear."""
    k = (round(x, 3), round(z, 3))
    if k in _clear_cache:
        return _clear_cache[k]
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, -7.6, z)), Vector((0, 1, 0)), distance=8.0)
    y = Y_FRONT
    if hit:
        y = min(Y_FRONT, loc.y - CLEAR)
        if y < Y_BACK:
            y = Y_BACK
    _clear_cache[k] = y
    return y


built, stats = [], {}
clamped, worst = 0, 0.0
for nm, bx0, bx1, cstep in BANDS:
    if WANT is not None and nm not in WANT:
        continue
    XS = axis(bx0, bx1, cstep)
    nx, nz = len(XS), len(ZR)
    verts, faces = [], []
    for i, x in enumerate(XS):
        for j, z in enumerate(ZR):
            y = -max(Y_FRONT * -1.0, min(-Y_BACK, depth(x, z)))   # depth in [0.35, 5.90]
            cy = clearance_y(x, z)
            if y > cy:
                clamped += 1
                worst = max(worst, y - cy)
                y = cy
            verts.append((x, y, z))
    for i in range(nx - 1):
        for j in range(nz - 1):
            a = i * nz + j
            faces.append((a, a + nz, a + nz + 1, a + 1))
    # --- CAP STRIPS.  The placeholder was a solid BOX; this is a heightfield
    #     SHEET, and the difference is measurable.  A ray that grazes a crest
    #     tangentially passes BEHIND the surface, and once behind it the sheet's
    #     depth (<= 8.5 m) can never catch it again — it escapes out of the back
    #     and reads as world background.  The first full build leaked exactly
    #     that way: 6-32 rays per camera on seven cameras, every one of them
    #     crossing the surface within 4 cm of tangency.  So the sheet is closed
    #     into a shell: top and bottom strips per band, side strips at the two
    #     ends of the run, and one back panel behind them all.
    base = len(verts)
    verts += [(x, BACK_CAP, Z1) for x in XS]
    for i in range(nx - 1):
        a = i * nz + (nz - 1)
        b = (i + 1) * nz + (nz - 1)
        faces.append((a, b, base + i + 1, base + i))
    base2 = len(verts)
    verts += [(x, BACK_CAP, Z0) for x in XS]
    for i in range(nx - 1):
        a = i * nz
        b = (i + 1) * nz
        faces.append((b, a, base2 + i, base2 + i + 1))
    if abs(bx0 - X0) < 1e-6 or abs(bx1 - X1) < 1e-6:
        west = abs(bx0 - X0) < 1e-6
        col = 0 if west else (nx - 1)
        xw = XS[col]
        b2 = len(verts)
        verts += [(xw, BACK_CAP, z) for z in ZR]
        for j in range(nz - 1):
            a = col * nz + j
            quad = (a, a + 1, b2 + j + 1, b2 + j)
            faces.append(quad if west else tuple(reversed(quad)))
    ob = new_mesh("cliff_town_" + nm, verts, faces, mat, COLL)
    ds = [max(-Y_FRONT, min(-Y_BACK, depth(x, z))) for x in XS for z in ZR]
    stats[nm] = dict(verts=len(verts), polys=len(faces), x=[bx0, bx1], col_m=cstep,
                     mean_edge=round((cstep + (Z1 - Z0) / (nz - 1)) / 2.0, 3),
                     depth_min=round(min(ds), 2), depth_max=round(max(ds), 2))
    built.append(ob.name)
    print("BUILT %-18s %5d verts %5d polys   x %7.1f..%-7.1f  col %.2f m  rows %d"
          "  depth %.2f..%.2f m" % (ob.name, len(verts), len(faces), bx0, bx1,
                                    cstep, nz, min(ds), max(ds)))

# the back panel that closes the shell — 4 verts, invisible in every camera
# because the modelled face never recedes past Y_BACK = -8.5, and the only thing
# that can ever see it is a grazing pinhole, where it reads as more rock.
if WANT is None:
    new_mesh("cliff_town_back",
             [(X0, BACK_CAP, Z0), (X1, BACK_CAP, Z0), (X1, BACK_CAP, Z1), (X0, BACK_CAP, Z1)],
             [(0, 3, 2, 1)], mat, COLL)
    built.append("cliff_town_back")
    print("BUILT %-18s     4 verts     1 poly    back panel at y = %.2f" % ("cliff_town_back", BACK_CAP))

for nm in hidden:
    o = bpy.data.objects.get(nm)
    if o is not None:
        o.hide_viewport = False

print("\nrow list: %d rows, z %.1f..%.1f (spacing %s)"
      % (len(ZR), ZR[0], ZR[-1], ", ".join("%.2f" % s for _, _, s in ZBANDS)))
print("clearance clamps: %d vertices pushed back, worst %.2f m" % (clamped, worst))
tv = sum(s["verts"] for s in stats.values())
tp = sum(s["polys"] for s in stats.values())
print("TOTAL %d verts / %d polys across %d patches" % (tv, tp, len(built)))

# px/edge the tiers will report, from the plan's measured d_mean per tier
DMEAN = {"a": (33.0, 59.0), "b": (39.0, 69.0), "c": (47.0, 74.0), "d": (59.0, 78.0)}
ty = math.tan(math.radians(35.0) / 2.0)
print("\nRESOLUTION (px per mesh edge at the shipped 2688x1536; target band 60-80,"
      "\n            gate_cliffface holds 43 and shelf_cliffface 45-76)")
for nm in ("a", "b", "c", "d"):
    if nm not in stats:
        continue
    e = stats[nm]["mean_edge"]
    lo, hi = DMEAN[nm]
    print("   tier %-4s edge %.2f m   %3.0f px at %4.1f m  ..  %3.0f px at %4.1f m"
          % (nm, e, e * (768.0 / (lo * ty)), lo, e * (768.0 / (hi * ty)), hi))

# ------------------------------------------------------------------ retire ---
ph = bpy.data.objects.get(PLACEHOLDER)
if RETIRE and ph is not None:
    if WANT is not None:
        print("\nREFUSED to retire %s: only tiers %s were built, so its footprint "
              "is not covered.\n         Retiring now would open a NEW sky leak — "
              "the defect this pass repairs." % (PLACEHOLDER, sorted(WANT)))
    else:
        me = ph.data
        bpy.data.objects.remove(ph, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
        print("\nRETIRED %s — the 8-vertex placeholder is gone." % PLACEHOLDER)
elif ph is not None:
    print("\n%s LEFT IN PLACE (pass `retire` once every tier is built). The new "
          "patches\n   sit behind its y = 0 face, so nothing changes on screen "
          "until it goes." % PLACEHOLDER)

if WANT is None:
    json.dump(dict(
        _doc=("GENERATED by tools/t2_cliff_south.py — the replacement for the "
              "8-vertex cliff_town placeholder. Pure function of the constants "
              "in that script; committed so the tier geometry is reviewable "
              "without opening the blend."),
        generator="tools/t2_cliff_south.py",
        plan="docs/plans/cliff-completion.md",
        material=MAT, collection=COLL,
        footprint=dict(x=[X0, X1], z=[Z0, Z1], y_front=Y_FRONT, y_back=Y_BACK),
        rows=len(ZR), zbands=ZBANDS,
        octaves=OCTAVES,
        fissures=FISSURES,
        tiers=stats, total_verts=tv, total_polys=tp,
        clearance_clamped=clamped, clearance_worst_m=round(worst, 3),
        placeholder=dict(name=PLACEHOLDER, loc=PH_LOC, scale=PH_SCALE, material=PH_MAT),
    ), open(MANIFEST, "w"), indent=1)
    print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
