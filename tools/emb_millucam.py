"""emb_millucam.py — THE WATERMILL'S LUCAM IS THE GABLE'S TWIN: ONE FLAT BOX HANGING OFF
THE ROOF.  This boards it and gives it the loading door a hoist housing is FOR.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_millucam.py -- [save] [revert save] [--bw 0.24] [--relief 0.018]

A CARRIER, NEVER A REBUILD (CLAUDE.md's `gate_rimchop` rule).  Nothing outside
`emb_dress_mill_lucam*` is touched.

**THE GENERATOR MIRROR IS OWED AND IS NOT WRITTEN** (round 3, 2026-08-10).  `emb_dress.py`
carried ANOTHER LANE'S uncommitted work for the whole of this window, and
`git commit -m … -- <pathspec>` commits the WORKING TREE, not the index — the trap that
published 309 lines of three lanes' in-progress edits on 2026-08-03.  So the mill builder
does NOT yet emit these members and a re-dress would silently drop them.  Round 2's gable
fix DID land in `emb_dress.py`; copy its shape (`GBW/GREL/GGAP` and the board loop) into
the `emb_dress_mill_lucam` line when that file is clean.

=============================== WHAT WAS MEASURED ================================

Round 2 handed this over as residual #2 and named it precisely: *"`emb_dress_mill_lucam`
is the gable's twin — the other `PLANK` box on the same mill, 2.6 x 1.9 x 2.6 m, and
homerow-after's F3/F7 ('an untextured box-like extension sits atop the roof beam').
Shipped plate: local sd 4.72 against a ring of 10.59 (2.2x flatter).  Same mechanism,
same material, same fix shape."*

Round 3 re-derived rather than inheriting, and TWO of the inherited words are wrong:

  * IT IS NOT UNTEXTURED AND IT IS NOT MISSING A MATERIAL.  `emb_dress_mill_lucam`
    carries `emb_dress_boarding` on an OBJECT-linked slot (`data.materials` is `[None]`
    for every `emb_dress` box — they share one template mesh, so reading the MESH's
    material list returns nothing on all of them and would look like the awning's literal
    finding).  It is the same below-Nyquist story the gable had: the only frequency on
    that material is 1/26 m = 38 mm, and homerow resolves 18.4 mm/px.
  * IT IS NOT ONLY A TEXTURE PROBLEM.  Cropped out of the shipped plate at world
    x 45.28..48.31, y 59.65..62.80, z 8.36..10.96 (509 x 450 px of a 2688 x 1536 frame,
    i.e. 5.5% of the frame width) it is a plain pale-tan carton with THREE FLAT FACES and
    one unbroken silhouette, hung on a roof of textured shingles and dark rafters.  It is
    the most obviously synthetic object in `homerow`.

A LUCAM IS A HOIST HOUSING.  The thing that makes one read is not grain, it is the
LOADING DOOR the sack comes out of — `emb_dress_mill_hoistbeam`, `_pulley`, `_rope` and
`_hoistsack` already hang off it and there was nothing for them to come out of.

=================================== WHAT THIS DOES ===============================

In the lucam box's OWN LOCAL FRAME, read off its `matrix_world` so no mill constant is
duplicated here (millgable's rule), and with OUTWARD derived as the local y that points
away from the roof deck's own centroid — never assumed:

  * vertical boards at `--bw` (0.24 m = 13 plate pixels at homerow, against the noise's 2)
    with alternating `+-relief`, on the outward face and both sides;
  * a LOADING DOOR in the middle of the outward face — two leaves, a mullion, a lintel
    over and a bressummer sill under, the door RECESSED into the box and the boards above
    it shortened to sit on the lintel;
  * four corner posts.

THE CORE BOX IS KEPT, NOT DELETED.  The boards stand proud of it, so the 0.012 m gaps
between them are shadow lines against a surface that is still there — deleting the box
would open the housing.  That is also what makes `revert` a plain delete of the members.

WHAT IT DELIBERATELY DOES NOT DO.  It adds no rake and no stepped edge.  Round 2's gable
fix stepped 0.119 m per board with nothing capping the rake and baked a lit SAWTOOTH on
`square` while every receipt was green; a lucam is a rectangular box, so there is no rake
to cap — and the plate is still looked at after the build, because that is the only
instrument that caught it.

`revert save` deletes every member (the `embml` snapshot names them).  Not idempotent: a
second run would board the boards, so a blend already carrying the snapshot aborts unless
`--force`.
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
FORCE = "--force" in argv


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


BW = float(opt("--bw", "0.24"))
RELIEF = float(opt("--relief", "0.018"))
GAP = float(opt("--gap", "0.012"))
PROP = "embml"
PREFIX = "emb_dress_mill_lucamx"          # every member this file builds
sc = bpy.context.scene

# ------------------------------------------------------------------- revert ---
if REVERT:
    st = sc.get(PROP)
    assert st, "this blend carries no '%s' snapshot — nothing to revert" % PROP
    st = json.loads(st)
    n = 0
    for nm in st["made"]:
        o = bpy.data.objects.get(nm)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
    del sc[PROP]
    print("reverted: removed %d of %d lucam member(s)" % (n, len(st["made"])))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

assert FORCE or not sc.get(PROP), (
    "this blend already carries the '%s' snapshot — this carrier is NOT idempotent "
    "(a second run would board the boards). Run `-- revert save` first." % PROP)

LUCAMS = [o for o in sc.objects if o.name.startswith("emb_dress_mill_lucam")
          and not o.name.startswith(PREFIX)
          and not o.name.startswith("emb_dress_mill_lucamroof")]
assert LUCAMS, ("no emb_dress_mill_lucam in this blend — an instrument that finds "
                "nothing must prove it could have found something")

# --- OUTWARD IS DERIVED, NEVER ASSUMED ---------------------------------------
rc, nrv = Vector((0, 0, 0)), 0
for o in sc.objects:
    if o.type != 'MESH' or not o.name.startswith("emb_dress_mill_roofdeck"):
        continue
    M = o.matrix_world
    for v in o.data.vertices:
        rc += M @ v.co
        nrv += 1
assert nrv, ("no emb_dress_mill_roofdeck* — outward is derived from the roof's centroid "
             "and there is no roof to derive it from")
rc /= nrv
print("roof centroid (%.2f, %.2f, %.2f) over %d verts" % (rc.x, rc.y, rc.z, nrv))

TIMBER = bpy.data.materials.get("mat_timber_dark")
made = []


def member(name, ctr, ax, ay, az, sx, sy, sz, mat):
    """One box in the lucam's own axes.  `ax/ay/az` are unit vectors; `s*` are sizes."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    b = bpy.context.active_object
    b.name = name
    b.matrix_world = type(bpy.context.object.matrix_world)((
        (ax.x * sx, ay.x * sy, az.x * sz, ctr.x),
        (ax.y * sx, ay.y * sy, az.y * sz, ctr.y),
        (ax.z * sx, ay.z * sy, az.z * sz, ctr.z),
        (0.0, 0.0, 0.0, 1.0)))
    if mat:
        b.data.materials.append(mat)
    return b


for g in LUCAMS:
    mw = g.matrix_world.copy()
    ex = Vector(mw.col[0][:3]); ey = Vector(mw.col[1][:3]); ez = Vector(mw.col[2][:3])
    W, D, H = ex.length, ey.length, ez.length
    ex.normalize(); ey.normalize(); ez.normalize()
    C = mw.translation.copy()
    OUT = ey if (C + ey - rc).length > (C - ey - rc).length else -ey
    mat = next((s.material for s in g.material_slots if s.material), None)
    coll = list(g.users_collection)
    print("  %-28s %.2f wide x %.2f deep x %.2f tall, outward (%.2f, %.2f, %.2f), mat %s"
          % (g.name, W, D, H, OUT.x, OUT.y, OUT.z, mat.name if mat else None))

    BT = 0.06                                   # board thickness, proud of the core
    SILL = 0.22                                 # bressummer depth (from the box foot)
    DW = min(1.30, W - 0.70)                    # loading-door leaf span
    DH = min(1.66, H - SILL - 0.34)             # door height above the sill
    zs = -H / 2 + SILL                          # sill top, local
    zl = zs + DH                                # lintel underside, local

    def place(name, u, v, w, su, sv, sw, m=None):
        made.append(member(name, C + ex * u + OUT * v + ez * w, ex, OUT, ez,
                           su, sv, sw, m or mat).name)
        for c in bpy.data.objects[made[-1]].users_collection:
            c.objects.unlink(bpy.data.objects[made[-1]])
        for c in coll:
            c.objects.link(bpy.data.objects[made[-1]])

    # --- the outward face: boards, cut around the loading door ----------------
    n = max(3, int(round(W / BW)))
    bw = W / n
    for i in range(n):
        u = -W / 2 + (i + 0.5) * bw
        d = RELIEF * (1 if i % 2 else -1)
        if abs(u) < DW / 2:                     # over the door: from the lintel up
            z0, z1 = zl + 0.20, H / 2
        else:
            z0, z1 = -H / 2, H / 2
        h = z1 - z0
        if h <= 0.06:
            continue
        place("%sboardF%02d" % (PREFIX, i), u, D / 2 + BT / 2 + d, (z0 + z1) / 2,
              bw - GAP, BT, h)

    # --- the two sides --------------------------------------------------------
    m = max(2, int(round(D / BW)))
    dw = D / m
    for side in (-1, 1):
        for i in range(m):
            v = -D / 2 + (i + 0.5) * dw
            d = RELIEF * (1 if i % 2 else -1)
            made.append(member("%sboardS%+d%02d" % (PREFIX, side, i),
                               C + ex * (side * (W / 2 + BT / 2 + d)) + OUT * v,
                               ex, OUT, ez, BT, dw - GAP, H, mat).name)
            for c in bpy.data.objects[made[-1]].users_collection:
                c.objects.unlink(bpy.data.objects[made[-1]])
            for c in coll:
                c.objects.link(bpy.data.objects[made[-1]])

    # --- the loading door: two leaves recessed into the box, mullion, lintel, sill --
    leaf = (DW - 0.06) / 2
    for k in (-1, 1):
        place("%sdoor%+d" % (PREFIX, k), k * (leaf + 0.06) / 2, D / 2 - 0.05,
              zs + DH / 2, leaf, 0.10, DH)
    place("%smullion" % PREFIX, 0.0, D / 2 + 0.02, zs + DH / 2, 0.07, 0.10, DH)
    place("%slintel" % PREFIX, 0.0, D / 2 + 0.08, zl + 0.10, W + 0.10, 0.22, 0.20,
          TIMBER)
    place("%ssill" % PREFIX, 0.0, D / 2 + 0.09, -H / 2 + SILL / 2, W + 0.10, 0.24, SILL,
          TIMBER)

    # --- corner posts ---------------------------------------------------------
    for su in (-1, 1):
        for sv in (-1, 1):
            made.append(member("%spost%+d%+d" % (PREFIX, su, sv),
                               C + ex * (su * (W / 2 + 0.02)) + OUT * (sv * (D / 2 + 0.02))
                               + ez * 0.0, ex, OUT, ez, 0.15, 0.15, H + 0.04, TIMBER or mat).name)
            for c in bpy.data.objects[made[-1]].users_collection:
                c.objects.unlink(bpy.data.objects[made[-1]])
            for c in coll:
                c.objects.link(bpy.data.objects[made[-1]])

sc[PROP] = json.dumps({"made": made, "bw": BW, "relief": RELIEF})
print("boarded %d lucam(s): %d members built (board pitch %.3f m, relief +-%.3f m, "
      "loading door %.2f x %.2f m). THE CORE BOX IS KEPT."
      % (len(LUCAMS), len(made), BW, RELIEF, DW, DH))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
