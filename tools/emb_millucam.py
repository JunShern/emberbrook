"""emb_millucam.py — THE WATERMILL'S LUCAM IS THE GABLE'S TWIN: ONE FLAT BOX HANGING OFF
THE ROOF.  This boards it and gives it the loading door a hoist housing is FOR.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_millucam.py -- [save] [revert save] [--bw 0.24] [--relief 0.018]

A CARRIER, NEVER A REBUILD (CLAUDE.md's `gate_rimchop` rule).  Nothing outside
`emb_dress_mill_lucam*` is touched.

**THE MIRROR IS A CALL, NOT A COPY** (round 4, 2026-08-12).  Round 3 left this file's
members unmirrored in `emb_dress.py` and a re-dress DROPPED ALL 36 — measured, not
inferred: `emb_dress --region all --tier plate --key emberwake` against the shipped master
into a scratch `--out` produced a blend carrying `emb_dress_mill_lucamx*` **36 -> 0**, and
the `embml` snapshot with them.  Round 2's answer for the gable was to COPY the recipe into
the generator, and that copy has already drifted where it can be seen: the shipped blend
carries the carrier's **84** boards named `gableboard+1board00`, a fresh dress builds the
generator's **86** named `gableboard+1_00`.  Two tools, one object, two answers.

So the lucam is mirrored the other way round — `emb_dress.build_mill()` CALLS
`board_lucams()` below, on the box it has just built.  One recipe, two entry points, and
the `embml` snapshot is written by the FUNCTION, so a dressed blend is already stamped and
this file's own guard refuses to board the boards from either direction.  Everything
outside `if __name__ == "__main__"` must therefore stay import-safe: no argv, no side
effect at import.

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

PROP = "embml"
PREFIX = "emb_dress_mill_lucamx"          # every member this file builds
DEF_BW, DEF_RELIEF, DEF_GAP = 0.24, 0.018, 0.012


def revert_lucams(sc):
    """Delete every member named in the `embml` snapshot and drop the snapshot."""
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
    return n


def board_lucams(sc, bw=DEF_BW, relief=DEF_RELIEF, gap=DEF_GAP, force=False, by="carrier"):
    """Board every `emb_dress_mill_lucam` in `sc` and stamp the `embml` snapshot.

    THE ONE OWNER OF THIS RECIPE.  `emb_dress.build_mill()` calls this on the box it has
    just built, and the CLI below calls it on a blend that is already dressed — so a
    re-dress can never drop the members and the two paths can never drift, which is the
    thing round 2's copy-the-recipe answer for the gable could not promise.
    Returns the list of member names.
    """
    BW, RELIEF, GAP = bw, relief, gap
    # EVERY NUMBER BELOW IS READ OFF `matrix_world`, AND `matrix_world` IS A CACHE.  It is
    # recomputed by a depsgraph evaluation, not by assigning `location`/`scale`/
    # `rotation_euler` — which is exactly what `emb_dress.obj()` does.  MEASURED
    # 2026-08-12, the first run of the generator mirror: the lucam read
    # **1.00 x 1.00 x 1.00 at the origin** instead of 2.6 x 1.9 x 2.6, so the roof
    # centroid was the origin too and the run built 21 members with a 0.30 x 0.44 m
    # loading door and no assertion anywhere.  A CARRIER OPENS A SAVED BLEND AND NEVER
    # MEETS THIS; a generator calling the same code meets it on the first line.
    bpy.context.view_layer.update()
    assert force or not sc.get(PROP), (
        "this blend already carries the '%s' snapshot — this carrier is NOT idempotent "
        "(a second run would board the boards). Run `-- revert save` first." % PROP)

    LUCAMS = [o for o in sc.objects if o.name.startswith("emb_dress_mill_lucam")
              and not o.name.startswith(PREFIX)
              and not o.name.startswith("emb_dress_mill_lucamroof")]
    assert LUCAMS, ("no emb_dress_mill_lucam in this blend — an instrument that finds "
                    "nothing must prove it could have found something")

    # --- OUTWARD IS DERIVED, NEVER ASSUMED ------------------------------------
    rc, nrv = Vector((0, 0, 0)), 0
    for o in sc.objects:
        if o.type != 'MESH' or not o.name.startswith("emb_dress_mill_roofdeck"):
            continue
        M = o.matrix_world
        for v in o.data.vertices:
            rc += M @ v.co
            nrv += 1
    assert nrv, ("no emb_dress_mill_roofdeck* — outward is derived from the roof's "
                 "centroid and there is no roof to derive it from")
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
        # AND THE GUARD FOR IT, general rather than a magic size: an unparented object's
        # world matrix IS its own basis, so any disagreement means the cache is stale and
        # every dimension below is a lie.  A generator that refuses in silence leaves the
        # defect and the receipt both invisible — this one names the cause.
        assert g.parent is not None or max(
            abs(a - b) for ra, rb in zip(mw, g.matrix_basis) for a, b in zip(ra, rb)
        ) < 1e-6, (
            "%s: matrix_world disagrees with matrix_basis — the depsgraph is STALE and "
            "W/D/H would be read off an identity matrix. Call "
            "bpy.context.view_layer.update() after building it." % g.name)
        ex = Vector(mw.col[0][:3]); ey = Vector(mw.col[1][:3]); ez = Vector(mw.col[2][:3])
        W, D, H = ex.length, ey.length, ez.length
        ex.normalize(); ey.normalize(); ez.normalize()
        C = mw.translation.copy()
        OUT = ey if (C + ey - rc).length > (C - ey - rc).length else -ey
        mat = next((s.material for s in g.material_slots if s.material), None)
        coll = list(g.users_collection)
        print("  %-28s %.2f wide x %.2f deep x %.2f tall, outward (%.2f, %.2f, %.2f), "
              "mat %s" % (g.name, W, D, H, OUT.x, OUT.y, OUT.z,
                          mat.name if mat else None))

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

        # --- the outward face: boards, cut around the loading door ------------
        n = max(3, int(round(W / BW)))
        bw_ = W / n
        for i in range(n):
            u = -W / 2 + (i + 0.5) * bw_
            d = RELIEF * (1 if i % 2 else -1)
            if abs(u) < DW / 2:                     # over the door: from the lintel up
                z0, z1 = zl + 0.20, H / 2
            else:
                z0, z1 = -H / 2, H / 2
            h = z1 - z0
            if h <= 0.06:
                continue
            place("%sboardF%02d" % (PREFIX, i), u, D / 2 + BT / 2 + d, (z0 + z1) / 2,
                  bw_ - GAP, BT, h)

        # --- the two sides ----------------------------------------------------
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
        place("%ssill" % PREFIX, 0.0, D / 2 + 0.09, -H / 2 + SILL / 2, W + 0.10, 0.24,
              SILL, TIMBER)

        # --- corner posts -----------------------------------------------------
        for su in (-1, 1):
            for sv in (-1, 1):
                made.append(member("%spost%+d%+d" % (PREFIX, su, sv),
                                   C + ex * (su * (W / 2 + 0.02))
                                   + OUT * (sv * (D / 2 + 0.02)) + ez * 0.0,
                                   ex, OUT, ez, 0.15, 0.15, H + 0.04,
                                   TIMBER or mat).name)
                for c in bpy.data.objects[made[-1]].users_collection:
                    c.objects.unlink(bpy.data.objects[made[-1]])
                for c in coll:
                    c.objects.link(bpy.data.objects[made[-1]])

    # THE SNAPSHOT IS WRITTEN HERE AND NOWHERE ELSE, so a blend dressed with the mirror
    # is stamped exactly as a blend the CLI carried, and the guard above refuses a second
    # boarding from EITHER direction.  `by` records which door it came in at.
    sc[PROP] = json.dumps({"made": made, "bw": BW, "relief": RELIEF, "by": by})
    print("boarded %d lucam(s): %d members built (board pitch %.3f m, relief +-%.3f m, "
          "loading door %.2f x %.2f m), by=%s. THE CORE BOX IS KEPT."
          % (len(LUCAMS), len(made), BW, RELIEF, DW, DH, by))
    return made


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    SAVE = "save" in argv
    REVERT = "revert" in argv
    FORCE = "--force" in argv

    def opt(f, d):
        return argv[argv.index(f) + 1] if f in argv else d

    sc = bpy.context.scene
    if REVERT:
        revert_lucams(sc)
    else:
        board_lucams(sc, float(opt("--bw", str(DEF_BW))),
                     float(opt("--relief", str(DEF_RELIEF))),
                     float(opt("--gap", str(DEF_GAP))), force=FORCE, by="carrier")
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the blend)")
