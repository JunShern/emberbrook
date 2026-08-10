"""emb_millgable.py — THE WATERMILL'S GABLE IS ONE FLAT BOX, AND IT IS THE MOST-COMPLAINED
-ABOUT SURFACE IN EMBERBROOK.  This boards it and cuts it to the roof.

    Blender -b tools/blends/emberbrook-dressed.blend --python-exit-code 1 \
        -P tools/emb_millgable.py -- [save] [revert save] [--bw 0.24] [--relief 0.018]

A CARRIER, NEVER A REBUILD (CLAUDE.md's `gate_rimchop` rule).  The generator is
`tools/emb_dress.py`, whose mill builder emits the same geometry; that file carries the
matching change so a re-dress agrees, and this carries it onto the three blends that are
already built.  Nothing outside `emb_dress_mill_gable*` is touched.

=============================== WHAT WAS MEASURED ================================

Round 1 handed this over as round 2's #1 and could not name it: `emb_plate_object` put the
pixels 1.16-1.41 m in front of the nearest massing (`lm_watermill_body`), which is the
right answer to the wrong question — the collision bundle is the GRAY BLOCKOUT and the
thing making those pixels is dressing.  `tools/emb_ray_census.py` against the DRESSED
master, 870 rays through the judge's own bbox on `homerow` (uv 0.892,0.248,0.998,0.438):

    emb_dress_mill_gable+1 | emb_dress_boarding      642 (73.8%)   39.96..42.95 m
    emb_dress_mill_infill  | emb_dress_daub           83 ( 9.5%)
    eleven `..._sh-1_*` shingles                     ~11% between them

and the generator line is one box:

    box("emb_dress_mill_gable%+d" % sx2, HW(...), (0.18, hd + 0.8, RIDGE - EAVE), ...)

SO IT IS NOT UNTEXTURED — `emb_dress_boarding` carries a stretched noise grain and a bump.
IT IS UNARTICULATED, TWO WAYS, and both are visible in `docs/qa/emberbrook-redteam/`:

  * ONE FACE, ~6 x 2.9 m, WITH NO RELIEF AT ANY SCALE THE CAMERA CAN RESOLVE.  The only
    detail on it is a procedural noise at 1/26 m = 38 mm; `homerow` is fov 20 over 768
    rows at 42 m, i.e. **18.4 mm per plate pixel**, so that grain is a TWO-PIXEL feature
    and the denoiser takes it.  Everything around it that reads — the studs, the daub
    panels, the cedar shingles, the sawn log — carries GEOMETRY at 0.1-0.5 m.  A material
    cannot rescue a surface whose only frequency is at the sensor's Nyquist limit.
  * IT IS A RECTANGLE WHERE A GABLE IS A TRIANGLE.  The box's top edge is a straight
    horizontal line 0.30 m under the ridge, across the full depth of the mill, while the
    roof it is supposed to close slopes away on both sides — which is exactly why six
    independent naive looks called it "a large blank rectangular block", "placeholder
    geometry", "a flat beige block ... on the building wall".

WHAT THIS DOES.  Deletes each gable box and rebuilds it, IN THAT BOX'S OWN LOCAL FRAME
(read off its `matrix_world`, so no mill constant is duplicated here), as a run of vertical
boards `--bw` wide with alternating `--relief` in and out — a 0.24 m rhythm is 13 plate
pixels at this camera, against the noise's 2 — each board cut to the ROOF ITSELF: the top
of every board is found by casting UP against the mill's own `roofdeck` meshes, so the
gable closes the roof it actually has and needs no pitch constant.  A board that finds no
roof above it is REFUSED AND COUNTED, never given a guessed height.  Two barge-boards are
laid along the resulting silhouette.  Material is unchanged (`emb_dress_boarding`) — this
is a GEOMETRY finding and the fix is geometry.

`revert save` restores the original boxes exactly (verts + transform, from the `embmg`
snapshot on the scene).  Not idempotent by construction: a second run would board the
boards, so a blend already carrying the snapshot aborts unless `--force`.
"""
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
FORCE = "--force" in argv


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


BW = float(opt("--bw", "0.24"))
RELIEF = float(opt("--relief", "0.018"))
GAP = float(opt("--gap", "0.012"))
PROP = "embmg"
sc = bpy.context.scene

# ------------------------------------------------------------------- revert ---
if REVERT:
    st = sc.get(PROP)
    assert st, "this blend carries no '%s' snapshot — nothing to revert" % PROP
    st = json.loads(st)
    for nm in list(bpy.data.objects.keys()):
        if nm.startswith("emb_dress_mill_gableboard") or nm.startswith("emb_dress_mill_gablebarge"):
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    from mathutils import Matrix
    coll = sc.collection.children.get(st["coll"]) or sc.collection
    for nm, rec in st["gables"].items():
        if nm in bpy.data.objects:
            continue
        me = bpy.data.meshes.new(nm)
        me.from_pydata([tuple(v) for v in rec["verts"]], [], [tuple(p) for p in rec["polys"]])
        me.validate(); me.update()
        for m in rec["mats"]:
            me.materials.append(bpy.data.materials[m])
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        mw = rec["mw"]
        ob.matrix_world = Matrix((mw[0:4], mw[4:8], mw[8:12], mw[12:16]))
    del sc[PROP]
    print("reverted %d gable(s)" % len(st["gables"]))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

assert FORCE or not sc.get(PROP), (
    "this blend already carries the '%s' snapshot — this carrier is NOT idempotent "
    "(a second run would board the boards). Run `-- revert save` first." % PROP)

GABLES = [o for o in sc.objects if o.name.startswith("emb_dress_mill_gable")
          and not o.name.startswith("emb_dress_mill_gableboard")
          and not o.name.startswith("emb_dress_mill_gablebarge")]
assert GABLES, ("no emb_dress_mill_gable* in this blend — an instrument that finds "
                "nothing must prove it could have found something")

# ------------------------------------------------- the roof, as its own geometry ---
rv, rp = [], []
nroof = 0
for o in sc.objects:
    if o.type != 'MESH' or not o.name.startswith("emb_dress_mill_roofdeck"):
        continue
    M = o.matrix_world
    base = len(rv)
    rv.extend([M @ v.co for v in o.data.vertices])
    rp.extend([[base + i for i in p.vertices] for p in o.data.polygons])
    nroof += 1
assert rp, ("no emb_dress_mill_roofdeck* geometry — the board heights are derived from "
            "the roof and there is no roof to derive them from")
ROOF = BVHTree.FromPolygons(rv, rp, all_triangles=False)
RCTR = Vector((sum(v.x for v in rv) / len(rv), sum(v.y for v in rv) / len(rv),
               sum(v.z for v in rv) / len(rv)))
print("roof BVH: %d deck meshes / %d polys, horizontal centroid (%.2f, %.2f)"
      % (nroof, len(rp), RCTR.x, RCTR.y))

UP = Vector((0, 0, 1))
snap = {"coll": (GABLES[0].users_collection[0].name
                 if GABLES[0].users_collection else sc.collection.name),
        "gables": {}}
made = refused = 0

for g in GABLES:
    mw = g.matrix_world.copy()
    snap["gables"][g.name] = dict(
        mw=[c for r in mw for c in r],
        verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in g.data.vertices],
        polys=[list(p.vertices) for p in g.data.polygons],
        mats=[s.material.name for s in g.material_slots if s.material])
    mat = next((s.material for s in g.material_slots if s.material), None)
    coll = list(g.users_collection)
    # local axes and extents, straight off the object's own transform
    ex = Vector(mw.col[0][:3]); ey = Vector(mw.col[1][:3]); ez = Vector(mw.col[2][:3])
    T, L, H = ex.length, ey.length, ez.length
    ex.normalize(); ey.normalize(); ez.normalize()
    ctr = mw.translation.copy()
    z0 = (ctr - ez * (H / 2)).z                      # the gable's foot, world z
    n = max(3, int(round(L / BW)))
    bw = L / n
    print("  %-30s  %.2f thick x %.2f long x %.2f tall  -> %d boards of %.3f m"
          % (g.name, T, L, H, n, bw))

    tops = []
    for i in range(n):
        t = -L / 2 + (i + 0.5) * bw
        p = ctr + ey * t
        # THE GABLE STANDS OUTSIDE ITS OWN ROOF, MEASURED: the box sits at local x
        # +-(hw/2 + 1.0) and `roofdeck` spans only +-(hw + 1.5)/2 = +-(hw/2 + 0.75), so a
        # straight-up cast from the gable misses the deck by 0.25 m and the first run of
        # this carrier asserted on all 42 boards.  That assertion is the finding: the
        # panel is 0.25 m PROUD of the roof it is supposed to close.  The height is
        # therefore taken on the roof's own plane, sampled one step in toward the deck's
        # horizontal centroid — the slope is a function of y alone, so stepping in x
        # changes nothing but whether there is deck to hit.
        hit = None
        for inw in (0.0, 0.45, 0.90):
            q = p + (RCTR - p).normalized() * inw if inw else p
            hit = ROOF.ray_cast(Vector((q.x, q.y, z0 - 0.20)), UP, 40.0)
            if hit[0] is not None:
                break
        if hit[0] is None:
            refused += 1
            tops.append(None)
            continue
        tops.append(hit[0].z - 0.06)                 # under the deck, never through it
    ok = [z for z in tops if z is not None]
    assert ok, "no board on %s found the roof above it" % g.name

    for i, ztop in enumerate(tops):
        if ztop is None:
            continue
        t = -L / 2 + (i + 0.5) * bw
        h = ztop - z0
        if h <= 0.05:
            refused += 1
            continue
        d = RELIEF * (1 if i % 2 else -1)
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        b = bpy.context.active_object
        b.name = "%sboard%02d" % (g.name.replace("gable", "gableboard"), i)
        # the gable stands upright, so world z is set directly and the two horizontal
        # axes keep the box's own orientation — no euler is reconstructed anywhere here.
        b.matrix_world = type(mw)((
            (ex.x * T, ey.x * (bw - GAP), ez.x * h, (ctr + ey * t + ex * d).x),
            (ex.y * T, ey.y * (bw - GAP), ez.y * h, (ctr + ey * t + ex * d).y),
            (ex.z * T, ey.z * (bw - GAP), ez.z * h, z0 + h / 2),
            (0.0, 0.0, 0.0, 1.0)))
        if mat:
            b.data.materials.append(mat)
        for c in b.users_collection:
            c.objects.unlink(b)
        for c in coll:
            c.objects.link(b)
        made += 1

    # A BARGE-BOARD THAT DOES NOT CAP THE RAKE IS A DECORATION, AND THE RAKE IS A STAIRCASE.
    # MEASURED (2026-08-10, the first shipped bake): from `square` the mill is 26-39 m away
    # and the gable is seen nearly EDGE-ON, so what that camera sees is the gable's TOP EDGE
    # as a line — and the board tops step by (RIDGE-EAVE)/(hd/2+OVER) x bw = 0.119 m per
    # board, which is ~10 plate pixels there.  The first cut put the barge OUTBOARD
    # (`ex * (T/2 + 0.05)`, 0.10 m thick), beside the rake instead of over it, so the plate
    # came back with a lit SAWTOOTH along the beam — a hard geometric serration on a lit
    # edge, which is exactly the "jagged / blocky-step" language round 1 took from 8 to 0.
    # ONLY THE PICTURE SAID SO: the carrier's own receipt (88 members, 0 refused) was green,
    # the homerow A/B looked right, and the draft A/B ranked `square` FIRST at 3.379% without
    # saying why.  The barge now straddles the gable's own plane and is wider than one step,
    # so the rake reads as one line at every angle.
    for side, rng in (("L", range(0, n // 2)), ("R", range(n - n // 2, n))):
        pts = [(i, tops[i]) for i in rng if tops[i] is not None]
        if len(pts) < 2:
            continue
        (i0, z1), (i1, z2) = pts[0], pts[-1]
        t0 = -L / 2 + (i0 + 0.5) * bw
        t1 = -L / 2 + (i1 + 0.5) * bw
        run = abs(t1 - t0)
        rise = z2 - z1
        ln = math.hypot(run, rise)
        ang = math.atan2(rise, (t1 - t0)) if abs(t1 - t0) > 1e-9 else 0.0
        # straddle the gable's OWN plane (ex offset 0) and be thicker than the boards, so
        # the barge wraps the rake on both faces instead of standing beside it
        mid = ctr + ey * ((t0 + t1) / 2)
        step = abs(rise) / max(1, len(pts) - 1)          # the rake's own stair, per board
        wide = max(0.24, step * 1.9)                     # cover a whole step and then some
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        b = bpy.context.active_object
        b.name = "%sbarge%s" % (g.name.replace("gable", "gablebarge"), side)
        ea = ey * math.cos(ang) + Vector((0, 0, 1)) * math.sin(ang)
        eb = Vector((0, 0, 1)) * math.cos(ang) - ey * math.sin(ang)
        thick = T + 2 * RELIEF + 0.06
        b.matrix_world = type(mw)((
            (ex.x * thick, ea.x * (ln + bw), eb.x * wide, mid.x),
            (ex.y * thick, ea.y * (ln + bw), eb.y * wide, mid.y),
            (ex.z * thick, ea.z * (ln + bw), eb.z * wide, (z1 + z2) / 2 - wide * 0.18),
            (0.0, 0.0, 0.0, 1.0)))
        if mat:
            b.data.materials.append(mat)
        for c in b.users_collection:
            c.objects.unlink(b)
        for c in coll:
            c.objects.link(b)
        made += 1

for g in list(GABLES):
    bpy.data.objects.remove(g, do_unlink=True)

sc[PROP] = json.dumps(snap)
print("boarded %d gable(s): %d members built, %d boards REFUSED (no roof above them, or "
      "shorter than 0.05 m) — board pitch %.3f m, relief +-%.3f m, gap %.3f m"
      % (len(snap["gables"]), made, refused, BW, RELIEF, GAP))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
