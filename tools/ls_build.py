"""ls_build.py — THE LOOP STAIRS, simplified to what the walk network actually says.

  Blender -b tools/blends/dellhollow-master.blend -P tools/ls_build.py \
      --python-exit-code 1 -- save

USER RULING, live play:

    "the visible model for the loop stairs shot is extremely confusing and does not
     match the actual walkable surface overlay... the walkable surface overlay seems
     sensible, but the rendered model does not... simplify this scene quite a lot to
     make it just look like a clear single staircase."

THE USER IS DESCRIBING A MEASURABLE FACT, and it is the Keepers' Steps disease for
the third time.  The `loop-stairs` camera owns two edges — `shelf-homes__quay-deck`
and `shelf-homes__market-stalls` — and between them the walk network is a perfectly
sensible double descent: 44 meshes, two flights of five/six treads leaving the same
little yard at z 19.07, each turning through two 2 x 2 m landings and dropping to
the quay deck and the market at z 14.07.  EVERY ONE OF THOSE FACES IS
`hide_render = True`, and there are NO TREADS IN THE MASTER AT ALL.  What renders
instead is the stairs' UNDER-STRUCTURE — `qm_stair_underworks` and
`shelf_stair_underworks` — a stack of chunky blocks, plus paving planes at wildly
inconsistent depths below the surface the player is actually walking on:

    walk_e_shelf-homes__quay-deck_l1_t03    art 1.94 m below the tread
    walk_e_shelf-homes__quay-deck_l1_t04    art 1.56 m below
    walk_e_shelf-homes__market-stalls_l1_t05  art 1.53 m below
    walk_e_shelf-homes__market-stalls_l0_t02  NOTHING under it at all
    walk_e_shelf-homes__market-stalls_l1_t01  art 0.23 m ABOVE it
    walk_e_shelf-homes__quay-deck_l1_t01      art 0.26 m ABOVE it

Two of them have the scaffold coming UP THROUGH the stair.  So the player walks up
an invisible flight, past blocks that cross it, over voids two metres deep.  "Does
not match the walkable surface overlay" is exactly right, and the fix is not to
restyle anything — it is to build the staircase that the walk graph has always
described, on the ribbons' own planes, and let the blocks become the masonry it
stands on instead of the subject of the shot.

ADDITIVE ONLY.  Every object is `ls_*` in `DIST_loopstairs`; the lamp namespace is
`KEYLS_`.  No `walk_`/`bar_` mesh is edited — the ten `bar_` blockout rails on these
two flights are ALREADY render-hidden (unlike the crossing's, which were the whole
problem there), so this pass only reads their lines.

THE PLINTH (`-- plinth`) IS BUILT, MEASURED, AND NOT YET CORRECT — 2026-07-31.
The banked follow-up was "replace the block stack inside x 50.5..61.5 y 6.5..14.5
with one stepped plinth following the two ribbons".  §0a/0b/0c do exactly that: the
solid is planned per walk face, the cut mask is the plinth's OWN plan (never a box),
and the three accepted geometry_audit offenders go with the mass they are bedded in.
It is OFF by default because it does not yet clear its own acceptance test, and the
test is the one thing here worth keeping:

    probe every tread centre, ray down, and NOTHING may be found above it.

Four formulations were measured against that and all four failed in the same place:
lofted-per-leg put three treads' stone 6-42 cm proud (a leg's treads do not lie on
the straight line between its ends — THE FLIGHT IS A LOOP); per-face solids clipped
at their own front edge came out shifted exactly one tread down the flight (the walk
quads OVERLAP, so a face reaches past its neighbour's centre); midpoint tiling fixed
the along-flight case and left the cross-flight one (the two flights leave one yard
and interleave within 0.10 m in plan at 0.3-0.9 m of height separation); and a
ribbon clamp that ducks a step under whatever crosses it either sinks the whole
plinth to the waterline (the grown footprint samples the quay deck five metres down
and reads it as a tread) or, capped, puts the stone back through the boards.

THE FINDING, so the next pass does not re-derive it: a per-face solid cannot bound
these footprints.  The walk faces are large, overlapping, and loop, so no clipping
rule on a face's own neighbours bounds it.  The plinth wants a RASTER: sample the
two ribbons on a fine XY grid, take the LOWEST ribbon within a 1.1 m window at each
cell, and lift the mass from that height field — then "no stone above any tread" is
true by construction instead of by clipping, and the interleave zone resolves itself.
Every constant below (RECESS/POUT/PCLEAR/PBED/PMIN/PDUCK/PWIN) was measured and is
reusable as-is.  The master was never saved during any of this.

Machinery from `tools/district_lib.py`: the walk-face model, the corridor guard, ray
founding, and `GateGrid` — the reproduction of master_walk_qa's own sample grid that
the crossing pass had to work out the hard way.  This file holds no copy of any of it.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (stable_hash, REPO, new_mesh, join_meshes, obox, beam, cyl, coll, M,
                          world_bbox, plane_z_fn, plank_fill, point_in_poly,
                          dist_poly2, offset_poly, clip_halfplane)
from district_lib import WalkGuard, GateGrid, bvh_of, ground_z, clear_between

SAVE = "save" in sys.argv
# THE PLINTH IS OFF BY DEFAULT AND THAT IS A MEASUREMENT, NOT A PREFERENCE.
# See "THE COMPLETION" below: the per-face solid is built and re-runnable, and it is
# not correct yet. Without this flag the pass does exactly what it shipped doing.
PLINTH_ON = "plinth" in sys.argv
COLL = "DIST_loopstairs"
PREFIX = "ls_"
LAMPNS = "KEYLS_"
DROP = 0.030
RAIL_H = 1.05                    # a handrail is 1.05 m over what you walk on
REGION = (46.0, 64.0, 5.0, 17.0)
# THE FLIGHTS ARE READ FROM THE CAMERA FILE, NOT NAMED HERE. This tool shipped with
# ("walk_e_shelf-homes__quay-deck_", "walk_e_shelf-homes__market-stalls_") hardcoded.
# When map stamp c046f51 re-origined the quay flight onto the loop landing, that
# constant silently pointed at a WITHDRAWN ribbon — the timber would have been dressed
# onto a staircase that no longer exists, and nothing in the pipeline would have said
# so. That is the same class of miss as the defect this whole pass was fixing, so the
# constant is gone: the camera file states what this shot owns, and this asks it.
import json as _json
_CAMS = _json.load(open(REPO + "/public/townmap/dellhollow.cameras.json"))
_LS = next(c for c in _CAMS["cameras"] if c["id"] == "loop-stairs")
FLIGHTS = tuple("walk_e_%s_" % e.split("@")[0] for e in _LS["owns"]["edges"])
PADS = tuple("walk_pad_%s" % l for l in _LS["owns"]["landmarks"])
print("  FLIGHTS from the camera file:", FLIGHTS)
print("  PADS    from the camera file:", PADS)
rng = random.Random(20260801)


def log(kind, what, why=""):
    print("  %-9s %-26s %s" % (kind, what, why))


print("=" * 80)
print("THE LOOP STAIRS — the flight the walk graph has always described")
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


# The quay-market tier's own families, by name, so nothing procedural is added.
# THE FLIGHTS ARE TIMBER, AND THAT IS THE LEGIBILITY DECISION, NOT A TASTE ONE.
# Laid in mat_qm_stone the treads are the same material as the masonry they sit on,
# so the first record shot showed a stone stair dissolving into a stone block stack —
# the exact confusion the user reported, merely tidier. Timber over stone is how the
# eye separates the route from the structure, and it is what the rest of this town
# does everywhere a walkway crosses rock.
MSTONE = derive("mat_rock", "mat_qm_stone", scale=2.05, tint=(0.50, 0.51, 0.56))
MDECK = derive("mat_deck", "mat_qm_deck", scale=1.55, tint=(0.62, 0.55, 0.44))
MTD = M("mat_timber_dark")

# ------------------------------------------------- idempotent clear, guarded
coll(COLL)
target = [o for o in bpy.data.objects if o.name.startswith((PREFIX, "veg_" + PREFIX, LAMPNS))]
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

GBVH = bvh_of(lambda n: n.startswith(("qm_stair_underworks", "shelf_stair_underworks",
                                      "qm_paving", "shelf_paving", "qm_ground",
                                      "shelf_ground", "qm_revetment", "qm_deck_frame",
                                      "qm_planking")))
KBVH = bvh_of(lambda n: n.startswith(("shelf_home", "shelf_armor_shop", "shelf_clutter",
                                      "shelf_parapet", "qm_stall", "qm_clutter",
                                      "qm_notice_board", "qm_rail", "veg_")))

npost = nrake = nfail = 0


def art_z(x, y, from_z, depth=4.0):
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
            return h[1].z
        org = h[1] + d * 0.002
    return None


def found(x, y, ztop, r=0.09, post_max=4.0, rake_max=2.2):
    """Carry a point down to real structure — post, then raking strut, then NOTHING,
    counted rather than faked.  A leg is a solid like any other and is put to the
    gate before it is built."""
    global npost, nrake, nfail
    if GG.blocked(x - 0.14, x + 0.14, y - 0.14, y + 0.14, -1e4, ztop):
        nfail += 1
        return []
    g = ground_z(GBVH, x, y, from_z=ztop - 0.02, depth=post_max + 1.0)
    if g is not None and 0.20 < ztop - g <= post_max \
            and clear_between(KBVH, (x, y, g), (x, y, ztop)):
        npost += 1
        p = cyl("ls_leg", (x, y, g - 0.02), (x, y, ztop), r, 8, MTD, COLL)
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
                p = cyl("ls_rake", (x, y, ztop), (x + dx, y + dy, gg - 0.02), r * 0.85,
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
    """One flight, grouped the way the walk graph already names it: legs of treads
    keyed by their `_t` stem (highest tread first), plus the landings between them.
    Read in two places — the plinth plans on it and the treads are laid on it — and
    the two MUST see the same flight or the stone and the boards disagree."""
    faces = up_faces(prefix)
    treads = [(n, p) for n, p in faces if "_t" in n.split("__")[-1]]
    lands = [(n, p) for n, p in faces if "landing" in n]
    legs = {}
    for n, p in treads:
        legs.setdefault(n.split("_t")[0], []).append((n, p))
    for k in legs:
        legs[k].sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
    return faces, treads, lands, legs


def axes(poly):
    c = sum(poly, Vector((0, 0, 0))) / len(poly)
    best, D = 0.0, Vector((1, 0, 0))
    for i in range(len(poly)):
        e = poly[(i + 1) % len(poly)] - poly[i]
        e.z = 0
        if e.length > best:
            best, D = e.length, e.normalized()
    P = Vector((-D.y, D.x, 0))
    return (c, D, P,
            max((q - c).dot(D) for q in poly),
            max(abs((q - c).dot(P)) for q in poly))


# =========================================================================
# 0. THE CONTRADICTING GEOMETRY — cut, with a snapshot so it can come back
# =========================================================================
# MEASURED BEFORE CUTTING ANYTHING.  Inside the shot's core box there are 1026
# faces of `qm_stair_underworks` and 12 of `shelf_stair_underworks`.  918 + 11 of
# them sit MORE than 0.45 m below the walk ribbons: that is the masonry the stairs
# genuinely stand on, it is not the problem, and it stays.  99 + 1 rise INTO or
# THROUGH the surface the player walks on — including the two places the census
# caught with the scaffold 0.23 m and 0.26 m ABOVE the tread.  Those hundred faces
# are the "does not match the walkable surface overlay", and they are what is cut.
#
# NOT DELETED, SNAPSHOTTED.  A deletion pass that cannot be re-run is a pass that
# cannot be corrected: the first run stashes each mesh whole as `LS_SRC_<name>` with
# a fake user, and every run afterwards RESTORES from that snapshot before cutting
# again.  So the cut is idempotent, the threshold can be retuned, and reverting is
# assigning the snapshot back.
#
# THE COMPLETION, 2026-07-31.  The first pass cut the hundred faces that stood IN
# the walk surface and left the 918 + 11 below it, and said so out loud: "the
# remaining block mass still competes with the flights... RECOMMENDATION: replace
# the block stack inside x 50.5..61.5 y 6.5..14.5 with one stepped plinth following
# the two ribbons."  That is §0b/§0c below.  The mass is not merely cut back now,
# it is REPLACED: the plinth carries both flights on the treads' own planes, so the
# stone under the stair is the stair's own stone and the timber has nothing left to
# be driven through.  The three accepted geometry_audit offenders were all of that
# form (ls_frame and ls_treads inside `qm_stair_underworks`), so they go with it.
CORE = (50.5, 61.5, 6.5, 14.5, 13.5, 21.0)
CUT_BELOW = 0.45
RECESS = 0.30      # the plinth's top sits this far under the walk plane...
POUT = 0.02        # ...and this far out past the tread edge: a nosing, not a ledge.
                   # MEASURED, not chosen: at 0.35 a step's stone overhangs the OTHER
                   # flight's treads where the two cross, and the ribbon clamp below then
                   # ducks every step in the town by its full allowance. The nosing has to
                   # be smaller than the gap between the flights, and 0.10 is.
PCLEAR = 0.12      # ...and the old mass is cut CLEAR of it by this much, never to
                   # it: a plinth that merely abuts the stack it replaces is a new
                   # intersection where three were removed.  Zero overlap is the
                   # only reading of "cleared" the audit and the eye both accept.
PBED = 0.40        # bedded this far into whatever carries it
PMIN = 0.55        # ...and never thinner than this, or it reads as a kerb
PDUCK = 0.75       # ...and may duck this far to stay under a crossing tread
PWIN = 1.10        # ...but only a ribbon THIS CLOSE below it constrains it at all.
                   # The window is the whole rule. Without it a step's grown footprint
                   # samples the quay deck five metres down, reads it as a tread it is
                   # standing proud of, and the entire plinth sinks to the waterline —
                   # measured, twice. A stair legitimately FLIES OVER a lower tier; what
                   # it may never do is stand over the flight beside it, and those are
                   # 0.3 to 0.9 m apart. 1.10 separates the two cases with room to spare.

# The ground the plinth STANDS ON is the tier's own bench and its surfaces — never
# the block stack it replaces, or it would found itself on the thing being cut.
PBVH = bvh_of(lambda n: n.startswith(("qm_ground", "qm_paving", "qm_planking",
                                      "qm_revetment", "qm_deck_frame",
                                      "shelf_ground")))

rib = []
for _o in bpy.data.objects:
    if _o.type != 'MESH' or not _o.name.startswith(
            FLIGHTS + PADS + ("walk_lm_quay-deck", "walk_lm_market-stalls")):
        continue
    _Mx = _o.matrix_world
    _N = _Mx.to_3x3().inverted().transposed()
    for _p in _o.data.polygons:
        if (_N @ _p.normal).normalized().z <= 0.5:
            continue
        _poly = [_Mx @ _o.data.vertices[_i].co for _i in _p.vertices]
        rib.append((_poly, plane_z_fn(_poly)))


def ribbon_z(x, y):
    best = None
    for poly, fn in rib:
        if point_in_poly(x, y, poly):
            z = fn(x, y)
            if best is None or z > best:
                best = z
    return best


# =========================================================================
# 0a. THE PLINTH, PLANNED — its solid is designed before anything is cut
# =========================================================================
# The cut mask is the plinth's OWN plan, not a box: a box takes out the tier's
# substructure wherever the box happens to reach, and only the footprint the
# plinth gives back is ours to remove.  So the solid is planned first, the mask
# falls out of it, and every face removed has stone put back over it.
PPLANS, PSOLIDS = [], []


def _prism(plan, ztop, zbot):
    """One step: the plan polygon carried down to the bench.  A vertical prism and
    not a lofted flight, because THE FLIGHT IS A LOOP — that is the shot's name —
    and a leg's treads do not lie on the straight line between its ends.  Projecting
    them onto one was measured putting three treads' stone 6 to 42 cm ABOVE the
    boards it carries.  Each step is planned on its OWN face, which is the same rule
    the treads are laid by."""
    n = len(plan)
    V = [Vector((p.x, p.y, zbot)) for p in plan] + [Vector((p.x, p.y, ztop)) for p in plan]
    F = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    F.append(list(range(n - 1, -1, -1)))
    F.append(list(range(n, 2 * n)))
    return V, F


def _base_at(px, py, ztop):
    """Where the plinth lands.  A station that finds no bench is carried to a
    minimum thickness rather than to a guessed depth."""
    g = ground_z(PBVH, px, py, from_z=ztop + 1.2, depth=30.0)
    b = (ztop - PMIN) if g is None else min(g - PBED, ztop - PMIN)
    return min(b, ztop - PMIN)


def _step_plan(poly, c, prv, nxt, grow):
    """A step's footprint: its own face grown for a nosing, then cut to the CELL it
    owns — halfway to the tread above it and halfway to the tread below.

    THE CUT IS AT THE MIDPOINTS, NOT AT THE FACE'S OWN EDGES, and that is measured.
    The walk faces of a flight OVERLAP: a tread quad reaches well past the next
    tread's centre, so a step clipped at its own front edge still roofs its
    neighbour — the plinth came out shifted exactly one tread down the flight, every
    step standing 6 to 50 cm over the boards below it. Halving the gap between
    centres tiles the flight instead, and a tiling cannot overlap.
    """
    plan = offset_poly(poly, grow)
    for ref, other in ((nxt, prv), (prv, nxt)):
        if ref is None and other is None:
            continue
        if ref is not None:
            dv = Vector((ref.x - c.x, ref.y - c.y, 0))
            if dv.length < 1e-6:
                continue
            dv.normalize()
            d = c.x * dv.x + c.y * dv.y + 0.5 * Vector((ref.x - c.x, ref.y - c.y, 0)).dot(dv)
        else:
            dv = Vector((c.x - other.x, c.y - other.y, 0))
            if dv.length < 1e-6:
                continue
            dv.normalize()
            d = c.x * dv.x + c.y * dv.y + max((q - c).dot(dv) for q in poly) + 0.02
        plan = clip_halfplane(plan, dv.x, dv.y, d)
        if len(plan) < 3:
            return plan
    return plan


def _plan_solid(plan, ztop, tag):
    """Carry one step's footprint down to the bench — under EVERY ribbon over it.
    THE FLIGHTS CROSS.  Both leave the same little yard, so a step planned on its
    own face still reaches out under its neighbour's: measured, the market flight's
    stone stood 42 cm over the quay flight's boards, which is the 0.23 m and 0.26 m
    scaffold-above-the-tread census entry rebuilt in new stone.  The face that
    planned a step does not get the last word on its height; the lowest walk plane
    anywhere over its footprint does."""
    if len(plan) < 3:
        return False
    cen = sum(plan, Vector((0, 0, 0))) / len(plan)
    probes = [p.lerp(cen, k) for p in plan for k in (0.0, 0.30)] + [cen]
    for i in range(len(plan)):
        probes += [plan[i].lerp(plan[(i + 1) % len(plan)], 0.5)]
    lo = ztop
    for q in probes:
        r = ribbon_z(q.x, q.y)
        if r is not None and r > ztop + RECESS - PWIN:
            lo = min(lo, r - RECESS)
    # ...but a step that would have to duck further than this is not passing under
    # a tread, it is somewhere it does not belong.  Counted, never silently sunk.
    global nduck
    if lo < ztop - 1e-6:
        nduck += 1
    ztop = max(lo, ztop - PDUCK)
    b = min(_base_at(p.x, p.y, ztop) for p in plan)
    PSOLIDS.append(_prism(plan, ztop, b))
    PPLANS.append(([Vector((p.x, p.y, 0.0)) for p in plan], b))
    return True


nplstep = npland = nduck = 0
for pref in (FLIGHTS if PLINTH_ON else ()):
    _f, _t, _lands, _legs = flight_legs(pref)
    for legname, items in sorted(_legs.items()):
        cs = [sum(p, Vector((0, 0, 0))) / len(p) for _n, p in items]
        zs = []
        for i, (_nm, poly) in enumerate(items):
            c = cs[i]
            nxt = cs[i + 1] if i + 1 < len(cs) else None
            prv = cs[i - 1] if i > 0 else None
            # the nosing grows as the flight descends: a masonry base batters out
            # under its own weight, and it also keeps consecutive steps' side walls
            # off each other's planes, where they would z-fight.
            if _plan_solid(_step_plan(poly, c, prv, nxt, POUT + 0.004 * i),
                           c.z - RECESS, _nm):
                nplstep += 1
                zs.append(c.z - RECESS)
        log("PLAN", legname.split("__")[-1], "%d steps, top z %.2f..%.2f"
            % (len(zs), min(zs), max(zs)) if zs else "no step planned")
    for nm, poly in _lands:
        c = sum(poly, Vector((0, 0, 0))) / len(poly)
        if _plan_solid(offset_poly(poly, POUT), c.z - RECESS, nm):
            npland += 1
log("PLAN", "%d steps + %d landings" % (nplstep, npland),
    "one mass on the two ribbons; %d of them ducked under a crossing ribbon; its "
    "plan is now the cut mask" % nduck)

ncut = 0
for nm in ("qm_stair_underworks", "shelf_stair_underworks"):
    o = bpy.data.objects.get(nm)
    if o is None:
        log("MISSING", nm, "nothing to cut")
        continue
    snap = bpy.data.meshes.get("LS_SRC_" + nm)
    if snap is None:
        snap = o.data.copy()
        snap.name = "LS_SRC_" + nm
        snap.use_fake_user = True
        log("SNAPSHOT", "LS_SRC_" + nm, "%d faces stashed before any cut"
            % len(snap.polygons))
    else:
        old = o.data
        o.data = snap.copy()
        o.data.name = nm + "_mesh"
        if old.users == 0:
            bpy.data.meshes.remove(old)
    Mx = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    doomed = []
    nover = nmask = 0
    for f in bm.faces:
        c = Mx @ f.calc_center_median()
        if not (CORE[0] <= c.x <= CORE[1] and CORE[2] <= c.y <= CORE[3]
                and CORE[4] <= c.z <= CORE[5]):
            continue
        r = ribbon_z(c.x, c.y)
        if r is not None and c.z > r - CUT_BELOW:
            doomed.append(f)
            nover += 1
            continue
        # ...and everything the plinth is about to stand in.  PCLEAR is the whole
        # point: the mask is the plinth's plan GROWN, so what survives never
        # touches the new stone and the audit has no pair left to report.
        for plan, b in PPLANS:
            if c.z < b - 0.05:
                continue
            if dist_poly2(c.x, c.y, plan) <= PCLEAR:
                doomed.append(f)
                nmask += 1
                break
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context='FACES')
        ncut += len(doomed)
    bm.to_mesh(o.data)
    bm.free()
    log("CUT", nm, "%d faces removed (of %d): %d stood in or over the walk surface, "
        "%d were the block stack the plinth replaces"
        % (len(doomed), len(snap.polygons), nover, nmask))
log("CUT", "%d faces total" % ncut,
    "every one of them stood in, over, or where the stair's own stone now goes")

# =========================================================================
# 0c. THE PLINTH, BUILT — one mass, the stair's own stone
# =========================================================================
_pp = []
for k, (V, F) in enumerate(PSOLIDS):
    _pp.append(new_mesh("ls_pl_%02d" % k, V, F, MSTONE, COLL))
PLINTH = join_meshes([p for p in _pp if p], "ls_plinth", COLL) if _pp else None
if PLINTH:
    _bm = bmesh.new()
    _bm.from_mesh(PLINTH.data)
    bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces)
    _bm.to_mesh(PLINTH.data)
    _bm.free()
    PLINTH.data.update()
    _b = world_bbox(PLINTH)
    log("BUILD", "ls_plinth", "%d verts, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f — the "
        "block stack is now the staircase's own stepped mass"
        % (len(PLINTH.data.vertices), *_b))
bpy.context.view_layer.update()

# The founding BVH was built over the world as it was BEFORE the cut, and legs put
# down against it would be founded on stone that is no longer there and driven
# through stone that now is. It is rebuilt on what the master actually holds.
if PLINTH_ON:
    GBVH = bvh_of(lambda n: n.startswith(("qm_stair_underworks", "shelf_stair_underworks",
                                          "qm_paving", "shelf_paving", "qm_ground",
                                          "shelf_ground", "qm_revetment", "qm_deck_frame",
                                          "qm_planking", "ls_plinth")))

# =========================================================================
# 1. THE TREADS AND LANDINGS — one board per face, on that face's own plane
# =========================================================================
# NO RISERS.  Measured on the Keepers' Steps and true again here: a riser closing
# the front of each tread stands over the BACK of the tread below, these treads
# overlap by only centimetres, so the lower face is not buried and the gate rays it.
# An open-riser flight on stone underworks is what a waterside stair is anyway.
tparts, fparts = [], []
ntread = nland = 0
for pref in FLIGHTS:
    faces, treads, lands, legs = flight_legs(pref)
    log("READ", pref.split("__")[-1].rstrip("_"),
        "%d treads in %d flights + %d landings, z %.2f..%.2f"
        % (len(treads), len(legs), len(lands),
           min(q.z for _n, pl in faces for q in pl),
           max(q.z for _n, pl in faces for q in pl)))

    for legname, items in sorted(legs.items()):
        items.sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
        c0 = sum(items[0][1], Vector((0, 0, 0))) / 4
        c1 = sum(items[-1][1], Vector((0, 0, 0))) / 4
        Dv = Vector((c1.x - c0.x, c1.y - c0.y, 0))
        Dv = Dv.normalized() if Dv.length > 1e-6 else Vector((1, 0, 0))
        Pv = Vector((-Dv.y, Dv.x, 0))
        for k, (nm, poly) in enumerate(items):
            zfn = plane_z_fn(poly)
            # A TREAD IS ONLY AS THICK AS THE GAP UNDER IT.  A flat 0.13 m board hung
            # 30 mm under the walk plane bores into `qm_stair_underworks` wherever the
            # masonry comes up to within 0.16 m — the audit read inside_frac 0.111 at
            # 0.22 m depth on the first cut. The gap is measured per face and the
            # board is cut to fit it, which is also what a stone stair does.
            cc = sum(poly, Vector((0, 0, 0))) / len(poly)
            gap = art_z(cc.x, cc.y, cc.z + 0.5, 3.0)
            th = 0.13 if gap is None else max(0.035, min(0.13, (cc.z - gap) - DROP - 0.02))

            def ok(px, py, pz, _th=th):
                if GG.blocked(px - 0.13, px + 0.13, py - 0.13, py + 0.13,
                              pz - _th - 0.02, pz):
                    return False
                # ...and nothing is laid through a lantern post or a stall
                return KBVH is None or KBVH.find_nearest(
                    Vector((px, py, pz - _th / 2)), 0.30)[0] is None

            V, F = plank_fill(poly, math.atan2(Pv.y, Pv.x), w=0.30, gap=0.012,
                              thick=th, drop=DROP, zfn=zfn,
                              seed=k * 7 + stable_hash(legname) % 101, keep=ok)
            if F:
                tparts.append(new_mesh("ls_tread", V, F, MDECK, COLL))
                ntread += 1
        # NO FRAME WHERE THE MASONRY IS ALREADY THE FRAME.  `qm_stair_underworks` is
        # the stairs' under-structure — that is literally its name — and where it
        # comes up to within 0.5 m of the ribbon the tread is already bedded on it.
        # Building stringers and legs there drove timber through stone: inside_frac
        # 0.387 at 0.24 m depth, against a region baseline of ZERO offenders. A
        # flight gets a frame only where it is genuinely spanning air.
        gaps = []
        for _n, pl in items:
            _c = sum(pl, Vector((0, 0, 0))) / len(pl)
            _g = art_z(_c.x, _c.y, _c.z + 0.5, 3.0)
            gaps.append(3.0 if _g is None else _c.z - _g)
        if sum(gaps) / max(1, len(gaps)) < 0.50:
            log("SKIP", legname.split("__")[-1], "masonry carries this flight "
                "(mean gap %.2f m) — no stringers, no legs" % (sum(gaps) / len(gaps)))
            continue
        hw = max(abs((q - (sum(pl, Vector((0, 0, 0))) / 4)).dot(Pv))
                 for _n, pl in items for q in pl)
        for side in (+1, -1):
            a = c0 + Pv * (side * (hw - 0.14))
            b = c1 + Pv * (side * (hw - 0.14))
            a.z = c0.z - 0.32
            b.z = c1.z - 0.32
            if GG.clear_seg(a, b, 0.10) and clear_between(GBVH, a, b, 0.14):
                st = beam("ls_stringer", a, b, 0.13, 0.30, MTD, COLL)
                if st:
                    fparts.append(st)
            for q in (a, b):
                fparts += found(q.x, q.y, q.z - 0.12)

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
                Vector((px, py, pz - _th / 2)), 0.30)[0] is None

        V, F = plank_fill(poly, math.pi / 4, w=0.32, gap=0.012, thick=thl, drop=DROP,
                          zfn=zfn, seed=nland * 13 + 3, keep=okl)
        if F:
            tparts.append(new_mesh("ls_landing", V, F, MDECK, COLL))
            nland += 1
        if gap is not None and (cc.z - gap) < 0.50:
            continue                       # the landing is bedded; it needs no legs
        xs = [q.x for q in poly]
        ys = [q.y for q in poly]
        for (lx, ly) in ((min(xs) + 0.30, min(ys) + 0.30), (max(xs) - 0.30, min(ys) + 0.30),
                         (min(xs) + 0.30, max(ys) - 0.30), (max(xs) - 0.30, max(ys) - 0.30)):
            fparts += found(lx, ly, zfn(lx, ly) - 0.26, r=0.085)

TREADS = join_meshes([p for p in tparts if p], "ls_treads", COLL) if tparts else None
log("BUILD", "ls_treads", "%d tread runs + %d landings, each laid on its OWN face's "
    "plane %.0f mm under it — not one height here is authored" % (ntread, nland, DROP * 1000))

# =========================================================================
# 2. THE RAILS — on the ten blockouts' own lines, which are already hidden
# =========================================================================
BARS = [o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("bar_e_shelf-homes__")]
rparts = []
nrp = nrb = nrskip = 0
for o in sorted(BARS, key=lambda o: o.name):
    b = world_bbox(o)
    edge = "walk_" + o.name[len("bar_"):].split("_l")[0]
    fax = [axes(pl) for _n, pl in up_faces(edge)]
    dx, dy = b[1] - b[0], b[3] - b[2]
    if max(dx, dy) >= 3.0 * max(1e-6, min(dx, dy)):
        if dx >= dy:
            a0 = Vector((b[0] + 0.09, (b[2] + b[3]) / 2, b[5]))
            a1 = Vector((b[1] - 0.09, (b[2] + b[3]) / 2, b[5]))
        else:
            a0 = Vector(((b[0] + b[1]) / 2, b[2] + 0.09, b[5]))
            a1 = Vector(((b[0] + b[1]) / 2, b[3] - 0.09, b[5]))
    else:
        # a squarish bbox is a DIAGONAL rail; pick the diagonal that agrees with the
        # flight's own direction (the crossing pass's finding)
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
        toward = None
        if fax:
            c_, D_, P_, L_, hw_ = min(fax, key=lambda a: abs((q - a[0]).dot(a[2]))
                                      + max(0.0, abs((q - a[0]).dot(a[1])) - a[3]))
            toward = P_ * (1.0 if (q - c_).dot(P_) < 0 else -1.0)
        cand = [0.0] if toward is None else \
            [-i * 0.06 for i in range(1, 12)] + [i * 0.06 for i in range(1, 12)]
        placed = None
        for step in cand:
            p2 = q if not step else q + toward * step
            f = art_z(p2.x, p2.y, b[5] + 0.40, (b[5] - b[4]) + 1.4)
            if f is None:
                continue
            if not GG.clear_pt(p2.x, p2.y, 0.055, f - 0.12, f + RAIL_H + 0.06):
                continue
            placed = (p2, f)
            break
        if placed is None:
            nrskip += 1
            continue
        p2, f = placed
        pts.append(Vector((p2.x, p2.y, f)))
        rparts.append(obox("ls_rp", p2.x, p2.y, f + 0.002 + RAIL_H / 2,
                           0.090, 0.090, RAIL_H, mat=MTD, cname=COLL))
        nrp += 1
    for u, v in zip(pts, pts[1:]):
        if (v - u).length > 2.9:
            continue
        for dz, w, h in ((0.0, 0.080, 0.070), (-0.47, 0.055, 0.048)):
            a_ = u + Vector((0, 0, RAIL_H + dz))
            b_ = v + Vector((0, 0, RAIL_H + dz))
            if not GG.clear_seg(a_, b_, max(w, h) / 2):
                continue
            bm = beam("ls_rl", a_, b_, w, h, MTD, COLL)
            if bm:
                rparts.append(bm)
                nrb += 1

FRAME = join_meshes([p for p in fparts if p], "ls_frame", COLL) if fparts else None
RAIL = join_meshes([p for p in rparts if p], "ls_rail", COLL) if rparts else None
log("BUILD", "ls_rail / ls_frame", "%d posts + %d rail runs on the lines of %d "
    "blockouts (%d stations had no visible floor or no clear gate and were skipped); "
    "stringers + %d legs and %d raking struts, %d stations found nothing and were "
    "left unbuilt" % (nrp, nrb, len(BARS), nrskip, npost, nrake, nfail))

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
    print("THE LOOP STAIRS — %d objects, %d verts, bounds x %.2f..%.2f y %.2f..%.2f "
          "z %.2f..%.2f" % (len(mine), nv, *bb))
    print("=" * 80)
    for o in sorted(mine, key=lambda o: o.name):
        b = world_bbox(o)
        print("  %-20s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
              % (o.name, len(o.data.vertices), b[0], b[1], b[2], b[3], b[4], b[5]))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
