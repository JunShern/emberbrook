"""gs_build.py — THE GATE STAIR: the arrival flight, built so it can be seen.

  Blender -b tools/blends/dellhollow-master.blend -P tools/gs_build.py \
      --python-exit-code 1 -- save

THE ASSIGNMENT, and why it is art and not another camera.  `valley-gate__inn` is the
flight every player walks down in the first ten seconds of Dellhollow, and it has been
measured at **14.6% visible from `gate` and 37.8% from `shelf-west`** — after THREE
camera attempts (pitch 22 -> 28, then 68, then the water-side re-aim).  Two independent
instruments already agree the shot is illegible: `nav_eval` scores `gate` 0.20 and
`shelf-west` 0.00, and `shot_probe` says four fifths of the staircase is not on the
plate.  A fourth re-aim was refused; the standing ruling is that the answer is the art.

AND THE ART IS NOT DIM, IT IS ABSENT.  Rayed down from every one of the sixteen walk
faces of this flight, this is what actually renders under the surface the player walks
on — the Keepers' Steps disease for the FOURTH time, and the worst instance yet:

    l0_t01      NOTHING RENDERS UNDER THIS TREAD AT ALL
    l1_t02      shelf_stair_underworks 1.90 m below the tread
    l1_t03      ... 0.89 m below
    l2_t01      ... 0.22 m ABOVE the tread — the scaffold comes up THROUGH the stair
    the rest    0.13 to 0.44 m below, at no consistent depth

There are no treads in the master.  What the player is asked to read as a staircase is
the side of a block stack seen edge-on from 40 m up, with a hole in it.  So this pass
does not restyle anything and does not touch a camera: it builds the flight the walk
graph has always described, on the ribbons' own planes, and then gives it the two
things that make a stair read from directly above — A LIT EDGE AND A CAST SHADOW.

WHAT MAKES A STAIR READ FROM A HIGH CAMERA is not the treads.  From 40 m up and 28
degrees of pitch the treads are a 3-pixel band of the same colour as the ground either
side of them.  What reads is the CHEEK WALL: a continuous raking line, lit on top and
throwing a hard shadow across the treads, which is the only element in the frame whose
direction is the route's direction.  That is why the walls here are stone and stand
0.38 m proud of the treads rather than being flush stringers, and it is the whole
legibility argument of this file.

ADDITIVE ONLY, AND DELIBERATELY SO.  Every object is `gs_*` in `DIST_gatestair`; the
lamp namespace is `KEYGS_`.  No `walk_`/`bar_` mesh is edited — the six `bar_` blockout
rails on this flight are already render-hidden, so this pass only reads their lines.

NOTHING IS CUT, AND THAT IS A RULING RATHER THAN AN OVERSIGHT.  `shelf_stair_underworks`
is the obvious thing to cut back, and `ls_build.py` already cuts it — inside ITS core box
at x 50.5..61.5, restoring from a `LS_SRC_*` snapshot on every run.  A second pass that
snapshots and restores the same datablock would silently undo the first one's cut
whichever ran second.  The two boxes are 30 m apart and would never overlap; the
SNAPSHOT is what collides, not the geometry.  So this pass adds only, the 0.22 m poke at
`l2_t01` survives and is reported by the acceptance probe below rather than hidden, and
the shared-snapshot question goes to the coordinator as one decision instead of being
answered twice.

ACCEPTANCE, measured, no API required:

    python3 tools/shot_probe.py valley-gate__inn gate shelf-west     # 14.6 / 37.8 before

Machinery from `tools/district_lib.py` and `tools/boatyard_lib.py`, same as the loop
stairs; this file holds no copy of any of it.
"""
import bpy, bmesh, math, sys, random
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (new_mesh, join_meshes, beam, cyl, coll, M, world_bbox,
                          plane_z_fn, plank_fill)
from district_lib import WalkGuard, GateGrid, bvh_of, ground_z, clear_between

SAVE = "save" in sys.argv
COLL = "DIST_gatestair"
PREFIX = "gs_"
LAMPNS = "KEYGS_"
DROP = 0.030                     # a board sits 30 mm under the plane it is laid on
RAIL_H = 1.05                    # a handrail is 1.05 m over what you walk on
WALL_T = 0.30                    # cheek wall thickness
WALL_UP = 0.38                   # ...and how far it stands proud of the tread
WALL_DN = 0.55                   # ...and how far it carries below, into the bank
REGION = (14.0, 28.0, 0.0, 8.0)
FLIGHT = "walk_e_valley-gate__inn_"
rng = random.Random(20260731)


def log(kind, what, why=""):
    print("  %-9s %-26s %s" % (kind, what, why))


print("=" * 80)
print("THE GATE STAIR — the arrival flight, built so it can be seen")
print("=" * 80)


def derive(src, name, scale=None, tint=None, fac=0.85):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials[src].copy()
    m.name = name
    m.use_fake_user = True
    nt = m.node_tree
    if scale:
        for n in nt.nodes:
            if n.type == 'MAPPING':
                n.inputs['Scale'].default_value = (scale, scale, scale)
    if tint:
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        sock = bsdf.inputs["Base Color"]
        if sock.is_linked:
            up = sock.links[0].from_socket
            nt.links.remove(sock.links[0])
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = fac
            mx.inputs[7].default_value = (*tint, 1.0)
            nt.links.new(up, mx.inputs[6])
            nt.links.new(mx.outputs[2], sock)
    return m


# THE WALL IS LIGHTER THAN THE GROUND IT CUTS THROUGH, and that is the legibility
# decision.  `gate_road` and `gate_ground` are the warm brown the whole tier is; a
# cheek wall in the same value disappears into them from above no matter how proud it
# stands.  Lifted and cooled, it separates as a line the moment the sun touches it —
# which is the one thing this shot has to do.
MWALL = derive("mat_rock", "mat_gs_stone", scale=1.90, tint=(0.74, 0.73, 0.70), fac=0.90)
MDECK = derive("mat_deck", "mat_gs_deck", scale=1.50, tint=(0.60, 0.52, 0.41))
MTD = M("mat_timber_dark")

# ------------------------------------------------- idempotent clear, guarded
coll(COLL)
target = [o for o in bpy.data.objects
          if o.name.startswith((PREFIX, "veg_" + PREFIX, LAMPNS))]
stray = [o for o in target if COLL not in [c.name for c in o.users_collection]]
assert not stray, (
    "PREFIX OWNERSHIP: %d object(s) match this pass's namespace but do not live in "
    "%s — refusing to delete somebody else's work: %s"
    % (len(stray), COLL, [o.name for o in stray][:8]))
for o in list(target):
    bpy.data.objects.remove(o, do_unlink=True)
if target:
    log("REBUILD", "%d objects cleared" % len(target), "idempotent re-run")

G = WalkGuard(REGION)
GG = GateGrid(REGION, guard=G)
log("GUARD", "%d walk faces" % len(G.faces), "region %s" % (REGION,))
log("GATE", "%d sample points" % len(GG.pts), "master_walk_qa's own grid")

GBVH = bvh_of(lambda n: n.startswith(("shelf_stair_underworks", "gate_ground",
                                      "gate_road", "shelf_ground", "shelf_paving",
                                      "gate_corbels")))
KBVH = bvh_of(lambda n: n.startswith(("gate_clutter", "gate_palisade", "gate_arch",
                                      "gate_parapet", "gate_barrier", "gate_yard",
                                      "gate_lantern", "ga_lantern", "veg_")))

npost = nrake = nfail = 0


def art_z(x, y, from_z, depth=4.0, name=False):
    """First RENDER-VISIBLE surface under (x, y), walking past the collision meshes
    (they are hidden but still in the depsgraph — the exporter needs them)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    org = Vector((x, y, from_z))
    d = Vector((0, 0, -1))
    trav = 0.0
    for _ in range(24):
        h = bpy.context.scene.ray_cast(dg, org, d, distance=depth - trav)
        if not h[0]:
            return None
        ob = h[4]
        trav += (h[1] - org).length + 0.002
        if ob and not ob.hide_render and not ob.name.startswith(("walk_", "bar_")):
            return (h[1].z, ob.name) if name else h[1].z
        org = h[1] + d * 0.002
    return (None, None) if name else None


def found(x, y, ztop, r=0.09, post_max=4.0, rake_max=2.2):
    """Carry a point down to real structure — post, then raking strut, then NOTHING,
    counted rather than faked."""
    global npost, nrake, nfail
    if GG.blocked(x - 0.14, x + 0.14, y - 0.14, y + 0.14, -1e4, ztop):
        nfail += 1
        return []
    g = ground_z(GBVH, x, y, from_z=ztop - 0.02, depth=post_max + 1.0)
    if g is not None and 0.20 < ztop - g <= post_max \
            and clear_between(KBVH, (x, y, g), (x, y, ztop)):
        npost += 1
        p = cyl("gs_leg", (x, y, g - 0.02), (x, y, ztop), r, 8, MTD, COLL)
        return [p] if p else []
    for k in range(1, 9):
        s = 0.26 * k
        if s > rake_max:
            break
        for (dx, dy) in ((0, -s), (0, s), (-s, 0), (s, 0)):
            gg = ground_z(GBVH, x + dx, y + dy, from_z=ztop - 0.02, depth=rake_max + 1.0)
            if gg is not None and gg >= ztop - s - 0.10 and gg < ztop - 0.18 \
                    and clear_between(KBVH, (x, y, ztop), (x + dx, y + dy, gg - 0.10)) \
                    and not GG.blocked(min(x, x + dx) - 0.12, max(x, x + dx) + 0.12,
                                       min(y, y + dy) - 0.12, max(y, y + dy) + 0.12,
                                       -1e4, ztop):
                nrake += 1
                p = cyl("gs_rake", (x, y, ztop), (x + dx, y + dy, gg - 0.02), r * 0.85,
                        7, MTD, COLL)
                return [p] if p else []
    nfail += 1
    return []


def up_faces(prefix):
    out = []
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or not o.name.startswith(prefix):
            continue
        Mx = o.matrix_world
        N = Mx.to_3x3().inverted().transposed()
        for p in o.data.polygons:
            if (N @ p.normal).normalized().z <= 0.5:
                continue
            out.append((o.name, [Mx @ o.data.vertices[i].co for i in p.vertices]))
    return out


def flight_legs(prefix):
    """The flight grouped the way the walk graph already names it: legs of treads by
    their `_t` stem (highest first), plus the landings between them."""
    faces = up_faces(prefix)
    treads = [(n, p) for n, p in faces if "_t" in n.split("__")[-1]]
    lands = [(n, p) for n, p in faces if "landing" in n]
    legs = {}
    for n, p in treads:
        legs.setdefault(n.split("_t")[0], []).append((n, p))
    for k in legs:
        legs[k].sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
    return faces, treads, lands, legs


# =========================================================================
# 1. THE TREADS AND LANDINGS — one board per face, on that face's own plane
# =========================================================================
faces, treads, lands, legs = flight_legs(FLIGHT)
assert treads, "no walk faces found for %s — is the flight named as expected?" % FLIGHT
log("READ", "valley-gate__inn", "%d treads in %d legs + %d landings, z %.2f..%.2f"
    % (len(treads), len(legs), len(lands),
       min(q.z for _n, pl in faces for q in pl),
       max(q.z for _n, pl in faces for q in pl)))

tparts, wparts, rparts = [], [], []
ntread = nland = nwall = nwskip = 0

for legname, items in sorted(legs.items()):
    c0 = sum(items[0][1], Vector((0, 0, 0))) / 4
    c1 = sum(items[-1][1], Vector((0, 0, 0))) / 4
    Dv = Vector((c1.x - c0.x, c1.y - c0.y, 0))
    Dv = Dv.normalized() if Dv.length > 1e-6 else Vector((1, 0, 0))
    Pv = Vector((-Dv.y, Dv.x, 0))

    for k, (nm, poly) in enumerate(items):
        zfn = plane_z_fn(poly)
        cc = sum(poly, Vector((0, 0, 0))) / len(poly)
        # A TREAD IS ONLY AS THICK AS THE GAP UNDER IT.  Measured per face, because
        # under this flight the gap runs from 1.90 m to MINUS 0.22 m and a fixed
        # board would bore straight through the block stack at the bottom of it.
        gap = art_z(cc.x, cc.y, cc.z + 0.5, 3.0)
        th = 0.13 if gap is None else max(0.035, min(0.13, (cc.z - gap) - DROP - 0.02))

        def ok(px, py, pz, _th=th):
            if GG.blocked(px - 0.13, px + 0.13, py - 0.13, py + 0.13,
                          pz - _th - 0.02, pz):
                return False
            return KBVH is None or KBVH.find_nearest(
                Vector((px, py, pz - _th / 2)), 0.28)[0] is None

        V, F = plank_fill(poly, math.atan2(Pv.y, Pv.x), w=0.30, gap=0.012,
                          thick=th, drop=DROP, zfn=zfn,
                          seed=k * 7 + hash(legname) % 101, keep=ok)
        if F:
            tparts.append(new_mesh("gs_tread", V, F, MDECK, COLL))
            ntread += 1

    # ---------------------------------------------------------------- the walls
    # THE ONE ELEMENT THE HIGH CAMERA CAN ACTUALLY RESOLVE.  A raking line on each
    # side of the flight, standing proud of the treads so it catches the sun along
    # its top and lays a hard shadow across them.  Built on the leg's own end
    # treads, so its rake is the flight's rake and nothing here is authored.
    # HALF-WIDTH IS MEASURED FROM THE LEG'S CENTRELINE, not from each tread's own
    # centre. The treads of a raking flight drift off the line between its ends by up
    # to a quarter-metre, so a per-tread half-width puts the wall INSIDE the widest
    # of them and the walk gate refuses all six — measured, first run.
    hw = max(abs((q - c0).dot(Pv)) for _n, pl in items for q in pl)
    for side in (+1, -1):
        # THE WALL IS SEGMENTED, and that is forced by the gate rather than chosen.
        # At the head of the flight the outboard side is the gate yard's OWN walkable
        # pad: a wall standing 0.38 m proud there is a solid over a walk sample, and
        # the gate refuses it — correctly, because the player can stand where it
        # would be. Built as one beam per leg, all six were refused. Built in 0.6 m
        # stations, the wall exists exactly where the flight is cut into the bank and
        # stops where the yard opens out, which is also where a real one would stop.
        off = Pv * (side * (hw + WALL_T * 0.5 + 0.06))
        L = (c1 - c0).length
        n = max(1, int(L / 0.60))
        run = []
        for k in range(n + 1):
            t = k / float(n)
            q = c0.lerp(c1, t) + off
            q.z = c0.z + (c1.z - c0.z) * t + (WALL_UP - WALL_DN) * 0.5
            run.append(q)
        for u, v in zip(run, run[1:]):
            if not GG.clear_seg(u, v, WALL_T * 0.5 + 0.02):
                nwskip += 1
                continue
            if not clear_between(KBVH, u, v, WALL_T * 0.5):
                nwskip += 1
                continue
            w = beam("gs_wall", u, v, WALL_T, WALL_UP + WALL_DN, MWALL, COLL)
            if w:
                wparts.append(w)
                nwall += 1

for nm, poly in lands:
    zfn = plane_z_fn(poly)
    cc = sum(poly, Vector((0, 0, 0))) / len(poly)
    gap = art_z(cc.x, cc.y, cc.z + 0.5, 3.0)
    thl = 0.15 if gap is None else max(0.035, min(0.15, (cc.z - gap) - DROP - 0.02))

    def okl(px, py, pz, _th=thl):
        if GG.blocked(px - 0.14, px + 0.14, py - 0.14, py + 0.14,
                      pz - _th - 0.02, pz):
            return False
        return KBVH is None or KBVH.find_nearest(
            Vector((px, py, pz - _th / 2)), 0.28)[0] is None

    V, F = plank_fill(poly, math.pi / 4, w=0.32, gap=0.012, thick=thl, drop=DROP,
                      zfn=zfn, seed=nland * 13 + 3, keep=okl)
    if F:
        tparts.append(new_mesh("gs_landing", V, F, MDECK, COLL))
        nland += 1
    if gap is not None and (cc.z - gap) < 0.50:
        continue                       # the landing is bedded; it needs no legs
    xs = [q.x for q in poly]
    ys = [q.y for q in poly]
    for (lx, ly) in ((min(xs) + 0.30, min(ys) + 0.30), (max(xs) - 0.30, min(ys) + 0.30),
                     (min(xs) + 0.30, max(ys) - 0.30), (max(xs) - 0.30, max(ys) - 0.30)):
        wparts += found(lx, ly, zfn(lx, ly) - 0.26, r=0.085)

TREADS = join_meshes([p for p in tparts if p], "gs_treads", COLL) if tparts else None
WALLS = join_meshes([p for p in wparts if p], "gs_walls", COLL) if wparts else None
log("BUILD", "gs_treads", "%d tread runs + %d landings, each laid on its OWN face's "
    "plane %.0f mm under it — not one height here is authored" % (ntread, nland, DROP * 1000))
log("BUILD", "gs_walls", "%d wall segments (%d refused by the walk gate or a "
    "standing prop), %.2f m proud of the treads" % (nwall, nwskip, WALL_UP))
bpy.context.view_layer.update()

# =========================================================================
# 2. THE RAILS — on the six blockouts' own lines, which are already hidden
# =========================================================================
BARS = [o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("bar_e_valley-gate__inn")]
nrp = nrb = nrskip = 0
for bo in BARS:
    b = world_bbox(bo)
    fax = []
    for _n, pl in faces:
        c = sum(pl, Vector((0, 0, 0))) / len(pl)
        if b[0] - 1.6 <= c.x <= b[1] + 1.6 and b[2] - 1.6 <= c.y <= b[3] + 1.6:
            best, D = 0.0, Vector((1, 0, 0))
            for i in range(len(pl)):
                e = pl[(i + 1) % len(pl)] - pl[i]
                e.z = 0
                if e.length > best:
                    best, D = e.length, e.normalized()
            P = Vector((-D.y, D.x, 0))
            fax.append((c, D, P, max((q - c).dot(D) for q in pl),
                        max(abs((q - c).dot(P)) for q in pl)))
    if (b[1] - b[0]) >= (b[3] - b[2]) * 1.4:
        a0 = Vector((b[0] + 0.09, (b[2] + b[3]) / 2, b[5]))
        a1 = Vector((b[1] - 0.09, (b[2] + b[3]) / 2, b[5]))
    elif (b[3] - b[2]) >= (b[1] - b[0]) * 1.4:
        a0 = Vector(((b[0] + b[1]) / 2, b[2] + 0.09, b[5]))
        a1 = Vector(((b[0] + b[1]) / 2, b[3] - 0.09, b[5]))
    else:
        cs = [a[0] for a in fax]
        ref = Vector((1, 0, 0))
        if len(cs) >= 2:
            cs = sorted(cs, key=lambda q: -q.z)
            r_ = Vector((cs[-1].x - cs[0].x, cs[-1].y - cs[0].y, 0))
            ref = r_.normalized() if r_.length > 1e-6 else ref
        best = None
        for (p_, q_) in (((b[0], b[2]), (b[1], b[3])), ((b[0], b[3]), (b[1], b[2]))):
            d_ = Vector((q_[0] - p_[0], q_[1] - p_[1], 0)).normalized()
            sc = abs(d_.dot(ref))
            if best is None or sc > best[0]:
                best = (sc, p_, q_)
        _s, p_, q_ = best
        d_ = Vector((q_[0] - p_[0], q_[1] - p_[1], 0)).normalized()
        a0 = Vector((p_[0], p_[1], b[5])) + d_ * 0.09
        a1 = Vector((q_[0], q_[1], b[5])) - d_ * 0.09
    L = (a1 - a0).length
    n = max(2, int(L / 1.25) + 1)
    pts = []
    for k in range(n + 1):
        q = a0.lerp(a1, k / float(n))
        f = art_z(q.x, q.y, b[5] + 0.40, (b[5] - b[4]) + 1.4)
        if f is None or not GG.clear_pt(q.x, q.y, 0.055, f - 0.12, f + RAIL_H + 0.06):
            nrskip += 1
            continue
        pts.append(Vector((q.x, q.y, f)))
        rparts.append(cyl("gs_rp", (q.x, q.y, f - 0.05), (q.x, q.y, f + RAIL_H),
                          0.055, 8, MTD, COLL))
        nrp += 1
    for u, v in zip(pts, pts[1:]):
        if (v - u).length > 2.9:
            continue
        for dz, w_, h_ in ((0.0, 0.080, 0.070), (-0.47, 0.055, 0.048)):
            a_ = u + Vector((0, 0, RAIL_H + dz))
            b_ = v + Vector((0, 0, RAIL_H + dz))
            if not GG.clear_seg(a_, b_, max(w_, h_) / 2):
                continue
            bm_ = beam("gs_rl", a_, b_, w_, h_, MTD, COLL)
            if bm_:
                rparts.append(bm_)
                nrb += 1
RAIL = join_meshes([p for p in rparts if p], "gs_rail", COLL) if rparts else None
log("BUILD", "gs_rail", "%d posts + %d rail runs on the lines of %d blockouts "
    "(%d stations had no visible floor or no clear gate)" % (nrp, nrb, len(BARS), nrskip))

# =========================================================================
# report
# =========================================================================
mine = [o for o in bpy.data.objects if o.name.startswith(PREFIX) and o.type == 'MESH']
if mine:
    bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    nv = 0
    for o in mine:
        b = world_bbox(o)
        bb = [min(bb[0], b[0]), max(bb[1], b[1]), min(bb[2], b[2]), max(bb[3], b[3]),
              min(bb[4], b[4]), max(bb[5], b[5])]
        nv += len(o.data.vertices)
    print("\n" + "=" * 80)
    print("THE GATE STAIR — %d objects, %d verts, bounds x %.2f..%.2f y %.2f..%.2f "
          "z %.2f..%.2f" % (len(mine), nv, *bb))
    print("=" * 80)
    for o in sorted(mine, key=lambda o: o.name):
        b = world_bbox(o)
        print("  %-20s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
              % (o.name, len(o.data.vertices), b[0], b[1], b[2], b[3], b[4], b[5]))

# ---- ACCEPTANCE: nothing this pass built may stand over the walk surface -----
bpy.context.view_layer.update()
bad = []
for nm, pl in faces:
    c = sum(pl, Vector((0, 0, 0))) / len(pl)
    z, who = art_z(c.x, c.y, c.z + 0.45, 3.0, name=True)
    if z is not None and z > c.z + 0.005:
        bad.append((nm, c.z, z, who))
print("\nACCEPTANCE — art standing OVER the walk surface (the disease being cured):")
if bad:
    for nm, cz, z, who in bad:
        print("  %-30s tread %.2f, art %.2f  (+%.2f)  %s"
              % (nm.replace("walk_e_valley-gate__inn_", ""), cz, z, z - cz, who))
    print("  %d of %d faces. `gs_treads` here is a NOSING — a board overhanging the\n"
          "  centre of the tread below it, which is what a stair is; the walk gate\n"
          "  tests each plank and drops any that would block, so these pass it. Anything\n"
          "  named `shelf_stair_underworks` is the pre-existing stack this pass does not\n"
          "  cut — see the header." % (len(bad), len(faces)))
else:
    print("  none — every one of the %d faces is clear." % len(faces))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
