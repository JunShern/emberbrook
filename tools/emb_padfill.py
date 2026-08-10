"""emb_padfill.py — EMBERBROOK'S AREA FLOORS ARE CUT WITH HOLES NOTHING STANDS IN.
This gives the paving back.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_padfill.py -- [save] [revert save] [--census]
        [--clear 0.28] [--minh 0.30] [--maxb 1.70] [--force]

A CARRIER, NEVER A REBUILD (CLAUDE.md's `gate_rimchop` rule; direct precedents
`emb_brookchop.py` and `emb_pavechop.py`).  It adds cells to `walk_lm_*` meshes and
touches nothing else.

=============================== WHAT WAS MEASURED ================================

`tools/emb_padstack.mjs --holes` (round 2) found **37.3 m2 of ENCLOSED holes in the
paving that nothing stands in** — 16.63 m2 in `walk_lm_gate-court` (8.3% of its own
area), 20.65 m2 in `walk_lm_square-plaza`, 0.63 m2 in `walk_lm_orchard` — and named
them as nine judge findings: square F40/F49/F50 ("severe geometry tearing and black
void seams"), pondlane F76/F88/F90 ("black hole voids", "sharp triangular holes"),
gatefield F114/F121 ("rectangular cutouts around the pillar bases"), arch F8.

WHY THEY ARE THERE.  `emb_blockout`'s area-floor loop drops a 0.45 m cell whose CENTRE
lands within 0.28 m of any landmark's `foot_rects_cut` rectangle — and that rectangle
is the MAP'S AUTHORED `bodysize`, not the thing the builder actually stands there.
Round 3 put every hole on the geometry of the DRESSED blend (this file's `--census`):

    hole                    area     what actually stands in it
    gate-court sigil       11.29 m2  two sigil plates, rim 1.84 m round, 0.32 m proud
    square well            10.64 m2  a 2.00 m well ring + two 0.17 m frames
    square notice/bell      8.75 m2  a 1.72 x 0.09 m BOARD and three 0.13-0.16 m posts
    gate-court trailhead     5.33 m2  a 0.50 x 1.90 step and two 1.50 x 0.22 m stiles
    square lamp-ring0        1.26 m2  ONE 0.13 x 0.13 m LAMP POST
    orchard lamp01           0.63 m2  ONE 0.13 x 0.13 m LAMP POST

**A 0.13 m POST CUTS 1.26 m2 OF PAVING — 74x ITS OWN PLAN AREA.**  `LAMPFEET` stamps a
0.68 x 0.68 m rectangle for a lamp whose post is 0.13 m; with the cut's 0.28 m pad and
the 0.45 m lattice that is a 1.24 m square quantised up.  And the well's cut is
`bodysize` 2.5 x 2.5 for a ring the builder makes 2.0 m round.

AND ONE OF THEM IS A STORY SITE.  There is no `walk_pad_sigil-plate-*`; the twin plates
of Chapter One's climax (`story.json` `ch1.sigils`) stand in an 11.29 m2 hole with no
walk record anywhere in it.

=================================== WHAT THIS DOES ===============================

Per `walk_lm_<id>` FAMILY (all of `walk_lm_x`, `walk_lm_x.001` …, which `emb_blockout`
emits as blocks of r/4 — see NAME_LM):

 1. Read the up-faces and recover the 0.45 m LATTICE they were emitted on.  The
    recovery ASSERTS: every cell centre must land within `--latol` of an integer
    lattice node or the family is refused by name.  (`emb_pavechop` welds and relaxes
    these meshes, so this carrier must run on RAW cells — see ORDER below.)
 2. Flood-fill the unpaved lattice from OUTSIDE the family's own bounds.  What does not
    drain is an ENCLOSED hole.  A bay open to the rim is not a hole and is left alone —
    that is what keeps every standoff at the area's own edge untouched.
 3. Refuse an enclosed cell if ANY OTHER walk mesh already has floor over it within
    0.60 m in z.  Adding paving under a road ribbon would be a new entry in
    `emb_padstack`'s stack census, which is the defect one lane over.
 4. Refuse an enclosed cell that a SOLID stands in.  The obstacle test is the oriented
    bounding box (the object's own `bound_box` through `matrix_world`, so a yawed stall
    is its own rectangle and not its AABB — that distinction is `foot_rects_cut`'s whole
    docstring), and the CELL'S CENTRE is tested against it at `--clear`, which is
    `emb_blockout`'s own rule verbatim.
      **AN OBSTACLE IS A THING YOU CANNOT STEP OVER, NOT A THING THAT IS THERE**, and
    this one threshold decides five holes.  A solid is an obstacle only if its TOP stands
    more than `--minh` (0.20 m) above the floor and its BOTTOM is below `--maxb` (1.70 m).
    So the gate court's own dressing — 1.34 m flagstones at +-0.05 m and the sigil plates'
    1.84 m rims topping out at +0.16 — is PAVING and does not hold the hole, while the
    festival dais (boards at +0.26..+0.33, i.e. a raised deck) and the market stalls
    (tables at +0.78) do, and a stall canopy at +1.82 and a notice-board roof at +2.00 are
    OVERHEAD and do not.  Measured cost of getting it wrong by 6 cm: at 0.30 m the dais's
    own 17.01 m2 hole was given back — 16.20 m2 of walk floor UNDER A DECK.
 5. Emit the survivors as cells identical in form to `emb_blockout`'s own — eight
    vertices at (cx +- CELL/2, cy +- CELL/2) x (z, z - 0.14), six quads, wound the same
    way — appended to the nearest block of the family, so the `.NNN` partition that
    decides which camera owns a cell is preserved.

WHAT IT DOES NOT DO.  It never removes floor and never moves a vertex that was already
there, so it cannot break a route; the walk network only grows.  It takes no view on the
holes it leaves: an occupied hole stays cut.

ORDER, AND IT IS ASSERTED.  `emb_pavechop` welds every area floor into one strip and
relaxes its plan silhouette, which destroys the lattice this file recovers — and the
holes' rims are boundary loops that pavechop has already chamfered.  So the sequence per
blend is `emb_pavechop -- revert save`, then this, then `emb_pavechop -- save`.  This
file ABORTS if any walk mesh still carries pavechop's `embpc` snapshot.

THE GENERATOR CARRIES THE SAME RULE.  `emb_blockout.py`'s area-floor loop prints the
enclosed-empty holes it is about to emit and shrinks `LAMPFEET`'s cut to the post it
actually builds.  It CANNOT make the whole decision: the dressing does not exist when it
runs, and half these holes are occupied only by `emb_dress_*`.  So the generator names
the defect and this carrier — which can see the finished town — closes it.

`revert save` restores exactly (the `embpf` snapshot holds each touched mesh's verts and
polys).  Not idempotent: a second run would re-flood a filled hole and find nothing, but
the snapshot check aborts anyway unless `--force`.
"""
import bpy, sys, os, json, math
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(REPO, "tools/blends/districts/emb_padfill.%s.json"
                        % os.path.splitext(os.path.basename(bpy.data.filepath or "unknown"))[0])

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
CENSUS = "census" in argv
FORCE = "--force" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


CELLS_OUT = opt("--cells-out", None)
CELLS_IN = opt("--cells-in", None)
CLEAR = float(opt("--clear", "0.28"))
MINH = float(opt("--minh", "0.20"))
MAXB = float(opt("--maxb", "1.70"))
LATOL = float(opt("--latol", "0.03"))
CELL = 0.45                    # emb_blockout's own number
THICK = 0.14                   # emb_blockout's own skirt
ZNEAR = 0.60                   # "another walk surface is over this cell"
PROP = "embpf"
UP_DOT = 0.5

sc = bpy.context.scene

# ================================================================ REVERT ======
if REVERT:
    n = 0
    for o in list(sc.objects):
        if o.type != 'MESH' or not o.get(PROP):
            continue
        st = json.loads(o[PROP])
        me = o.data
        mats = [s.material for s in o.material_slots if s.material]
        me.clear_geometry()
        me.from_pydata([tuple(v) for v in st["verts"]], [], [tuple(p) for p in st["polys"]])
        me.validate()
        me.update()
        me.materials.clear()
        for m in mats:
            me.materials.append(m)
        del o[PROP]
        n += 1
    print("reverted %d area floor(s)" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the blend)")
    sys.exit(0)

WALK = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith("walk_")]
assert WALK, "no walk_* meshes in this blend"
held = [o.name for o in WALK if o.get("embpc")]
assert FORCE or not held, (
    "%d walk mesh(es) carry emb_pavechop's 'embpc' snapshot. This carrier recovers the "
    "0.45 m LATTICE the area floors were emitted on, and pavechop has welded and relaxed "
    "it away. Run `-P tools/emb_pavechop.py -- revert save` first, then this, then "
    "pavechop again.\n  %s" % (len(held), ", ".join(held[:6])))
heldme = [o.name for o in WALK if o.get(PROP)]
assert FORCE or not heldme, (
    "%d mesh(es) already carry the '%s' snapshot — run `-- revert save` first"
    % (len(heldme), PROP))

print("=" * 78)
print("emb padfill — give back the enclosed paving holes nothing stands in")
print("blend %s" % bpy.data.filepath)
print("clear %.2f m   obstacle top >= floor+%.2f and bottom <= floor+%.2f   cell %.2f m"
      % (CLEAR, MINH, MAXB, CELL))
print("=" * 78)


# --------------------------------------------------------- geometry helpers --
def rings_of(o, me):
    """(top face indices) — HIGHER MEAN Z WINS, because `emb_blockout`'s `box()` winds
    these inside out exactly as the water sheets are.  Verbatim in intent from
    emb_pavechop.rings_of, which is the file that established the fact."""
    M = o.matrix_world
    N = M.to_3x3().inverted().transposed()
    plus, minus = [], []
    for p in me.polygons:
        nz = (N @ p.normal).normalized().z
        if nz > UP_DOT:
            plus.append(p.index)
        elif nz < -UP_DOT:
            minus.append(p.index)

    def meanz(idxs):
        if not idxs:
            return -1e9
        vs = [v for i in idxs for v in me.polygons[i].vertices]
        return sum((M @ me.vertices[v].co).z for v in vs) / len(vs)

    return plus if meanz(plus) > meanz(minus) else minus


def hull(pts):
    """Monotone-chain convex hull of 2D points."""
    P = sorted(set((round(x, 5), round(y, 5)) for x, y in pts))
    if len(P) < 3:
        return P

    def half(pp):
        out = []
        for p in pp:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    return half(P)[:-1] + half(P[::-1])[:-1]


def near_poly(px, py, poly, r):
    """Is (px,py) inside a convex polygon, or within `r` of it?

    THE TEST IS THE CELL'S CENTRE, NOT ITS SQUARE, because that is `emb_blockout`'s own
    rule verbatim — *"a cell is kept or dropped by its CENTRE, so the cut's margin has to
    be half a cell"* — and testing the whole 0.45 m square expanded by `r` silently adds
    another 0.225 m of standoff.  Measured cost of getting this wrong: the well's 2.0 m
    ring held 6.28 m2 of a 10.73 m2 hole instead of 5.1.
    """
    n = len(poly)
    if n < 3:
        return any(math.hypot(px - q[0], py - q[1]) <= r for q in poly)
    pos = neg = False                 # winding-agnostic: inside iff all cross products agree
    d2 = 1e18
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        c = ex * (py - ay) - ey * (px - ax)
        if c > 1e-12:
            pos = True
        elif c < -1e-12:
            neg = True
        L2 = ex * ex + ey * ey
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * ex + (py - ay) * ey) / L2))
        qx, qy = ax + ex * t, ay + ey * t
        d2 = min(d2, (px - qx) ** 2 + (py - qy) ** 2)
    return (not (pos and neg)) or d2 <= r * r


# ------------------------------------------------------- the walk height field --
# Every OTHER walk mesh's up-faces, on a coarse plan grid, so "is there already floor
# over this cell" is one lookup.  Rule 3 above.
WGRID = {}
WG = 0.15
for o in WALK:
    me = o.data
    M = o.matrix_world
    for pi in rings_of(o, me):
        vs = [M @ me.vertices[v].co for v in me.polygons[pi].vertices]
        x0 = min(v.x for v in vs); x1 = max(v.x for v in vs)
        y0 = min(v.y for v in vs); y1 = max(v.y for v in vs)
        z = max(v.z for v in vs)
        for i in range(int(math.floor(x0 / WG)), int(math.floor(x1 / WG)) + 1):
            for j in range(int(math.floor(y0 / WG)), int(math.floor(y1 / WG)) + 1):
                cx, cy = (i + 0.5) * WG, (j + 0.5) * WG
                if not (x0 - 1e-9 <= cx <= x1 + 1e-9 and y0 - 1e-9 <= cy <= y1 + 1e-9):
                    continue
                WGRID.setdefault((i, j), []).append((o.name, z))

# ----------------------------------------------------------------- families --
FAMS = {}
for o in WALK:
    if not o.name.startswith("walk_lm_"):
        continue
    fam = o.name.split(".")[0]
    FAMS.setdefault(fam, []).append(o)
for f in FAMS:
    FAMS[f].sort(key=lambda o: o.name)

SKIP_OBS = ("walk_", "water_", "emb_ground", "emb_dress_far", "emb_sky", "emb_backdrop",
            "emb_veg", "veg_", "grass_", "emb_dress_grass", "emb_dress_leaf")

report = {"blend": bpy.data.filepath, "clear": CLEAR, "minh": MINH, "maxb": MAXB,
          "families": []}
TOTAL_ADD = 0.0
TOTAL_HOLE = 0.0
TOUCHED = {}
PLAN = {}          # fam -> [(cx, cy, z), …] — THE decision, made once
FAMCELLS = {}      # fam -> {(i,j): (obj, z, cx, cy)}

for fam in sorted(FAMS):
    objs = FAMS[fam]
    # --- cells, and the lattice they were emitted on -------------------------
    cells = {}                                  # (i,j) -> (obj, z, cx, cy)
    raw = []
    for o in objs:
        me = o.data
        M = o.matrix_world
        for pi in rings_of(o, me):
            vs = [M @ me.vertices[v].co for v in me.polygons[pi].vertices]
            cx = sum(v.x for v in vs) / len(vs)
            cy = sum(v.y for v in vs) / len(vs)
            zz = max(v.z for v in vs)
            raw.append((o, cx, cy, zz))
    if not raw:
        continue
    ox = min(r[1] for r in raw)
    oy = min(r[2] for r in raw)
    bad = 0
    for o, cx, cy, zz in raw:
        fi, fj = (cx - ox) / CELL, (cy - oy) / CELL
        i, j = round(fi), round(fj)
        if abs(fi - i) > LATOL / CELL or abs(fj - j) > LATOL / CELL:
            bad += 1
            continue
        cells[(i, j)] = (o, zz, ox + i * CELL, oy + j * CELL)
    if bad:
        print("  %-24s REFUSED — %d of %d cells are off the %.2f m lattice (>%.3f m); "
              "this family was not emitted as plain blockout cells"
              % (fam, bad, len(raw), CELL, LATOL))
        continue
    if len(cells) < 8:
        continue

    zs = sorted(c[1] for c in cells.values())
    zmed = zs[len(zs) // 2]
    FAMCELLS[fam] = cells

    # --- enclosed holes ------------------------------------------------------
    i0 = min(k[0] for k in cells) - 1; i1 = max(k[0] for k in cells) + 1
    j0 = min(k[1] for k in cells) - 1; j1 = max(k[1] for k in cells) + 1
    outside = set()
    stack = [(i0, j0)]
    outside.add((i0, j0))
    while stack:
        a, b = stack.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (a + da, b + db)
            if n[0] < i0 or n[0] > i1 or n[1] < j0 or n[1] > j1:
                continue
            if n in outside or n in cells:
                continue
            outside.add(n)
            stack.append(n)
    holes = []
    seen = set()
    for a in range(i0, i1 + 1):
        for b in range(j0, j1 + 1):
            k = (a, b)
            if k in cells or k in outside or k in seen:
                continue
            comp = []
            st = [k]
            seen.add(k)
            while st:
                c = st.pop()
                comp.append(c)
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (c[0] + da, c[1] + db)
                    if n in cells or n in outside or n in seen:
                        continue
                    if n[0] < i0 or n[0] > i1 or n[1] < j0 or n[1] > j1:
                        continue
                    seen.add(n)
                    st.append(n)
            holes.append(comp)
    if not holes:
        print("  %-24s %4d cells, no enclosed hole" % (fam, len(cells)))
        continue

    # --- obstacles near this family -----------------------------------------
    hx0 = ox + (min(c[0] for h in holes for c in h) - 1) * CELL
    hx1 = ox + (max(c[0] for h in holes for c in h) + 1) * CELL
    hy0 = oy + (min(c[1] for h in holes for c in h) - 1) * CELL
    hy1 = oy + (max(c[1] for h in holes for c in h) + 1) * CELL
    obs = []
    for o in sc.objects:
        if o.type != 'MESH' or o.name.startswith(SKIP_OBS):
            continue
        cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if not cs:
            continue
        bz0 = min(c.z for c in cs); bz1 = max(c.z for c in cs)
        if bz1 < zmed + MINH or bz0 > zmed + MAXB:
            continue
        bx0 = min(c.x for c in cs); bx1 = max(c.x for c in cs)
        by0 = min(c.y for c in cs); by1 = max(c.y for c in cs)
        if bx1 < hx0 - 2 or bx0 > hx1 + 2 or by1 < hy0 - 2 or by0 > hy1 + 2:
            continue
        if (bx1 - bx0) * (by1 - by0) > 400:
            continue                                    # a skirt, not a footprint
        obs.append((o.name, hull([(c.x, c.y) for c in cs]), bx0, bx1, by0, by1))

    famrec = {"fam": fam, "cells": len(cells), "z": zmed, "holes": [], "added": 0}
    for comp in sorted(holes, key=lambda c: -len(c)):
        area = len(comp) * CELL * CELL
        add, blocked_by = [], {}
        for (a, b) in comp:
            cx, cy = ox + a * CELL, oy + b * CELL
            # rule 3 — another walk surface already covers this cell's own CENTRE.  The
            # sample is the centre and nothing wider: a hole cell touches paved cells on
            # every side by construction, so a 0.45 m-wide sample reports the family's
            # own neighbours and refuses every hole in town (measured: it did).
            covered = None
            for nm, z in WGRID.get((int(math.floor(cx / WG)), int(math.floor(cy / WG))), ()):
                if nm.split(".")[0] != fam and abs(z - zmed) < ZNEAR:
                    covered = nm
            if covered:
                blocked_by[covered] = blocked_by.get(covered, 0) + 1
                continue
            # rule 4 — a solid stands in it
            hit = None
            for nm, poly, bx0, bx1, by0, by1 in obs:
                if (bx1 < cx - CLEAR or bx0 > cx + CLEAR
                        or by1 < cy - CLEAR or by0 > cy + CLEAR):
                    continue
                if near_poly(cx, cy, poly, CLEAR):
                    hit = nm
                    break
            if hit:
                blocked_by[hit] = blocked_by.get(hit, 0) + 1
                continue
            add.append((a, b, cx, cy))
        top = sorted(blocked_by.items(), key=lambda t: -t[1])[:3]
        famrec["holes"].append({"m2": area, "give": len(add) * CELL * CELL,
                                "blockers": [[t[0], t[1] * CELL * CELL] for t in top]})
        TOTAL_HOLE += area
        if not add:
            print("    %-22s hole %6.2f m2 -> 0.00 given back; held by %s"
                  % (fam, area, ", ".join("%s (%.2f m2)" % (t[0], t[1] * CELL * CELL)
                                          for t in top) or "nothing (refused)"))
            continue
        print("    %-22s hole %6.2f m2 -> %6.2f m2 GIVEN BACK (%d cells); held by %s"
              % (fam, area, len(add) * CELL * CELL, len(add),
                 ", ".join("%s (%.2f m2)" % (t[0], t[1] * CELL * CELL) for t in top)
                 or "nothing"))
        PLAN.setdefault(fam, []).extend([(cx, cy, zmed) for (a, b, cx, cy) in add])
    report["families"].append(famrec)

# ============ ONE DECISION, THREE BLENDS ======================================
# The walk network in `emberbrook-master`, `-dressed` and `-realtime` MUST stay identical
# — `emb_padstack` reads `emb-cine` and `emb-townwalk` as the same 222 nodes / 24,349
# floor faces, and `walk_engine_gate` compares the FILE against the ENGINE across both
# bundles.  But the obstacle census is NOT the same in the three: the gray master has no
# `emb_dress_notice_board`, no market crates and no bunting posts.  So the decision is
# made ONCE against the blend that can see the whole town (`--cells-out`, run on
# `-dressed`) and REPLAYED verbatim onto the others (`--cells-in`).  Deriving it per blend
# would ship three different walk networks with every gate green.
if CELLS_OUT:
    with open(CELLS_OUT, "w") as f:
        json.dump({"cell": CELL, "thick": THICK, "clear": CLEAR, "minh": MINH,
                   "maxb": MAXB, "from": bpy.data.filepath,
                   "plan": {k: [list(p) for p in v] for k, v in PLAN.items()}}, f, indent=1)
    print("cell list -> %s (%d cells over %d families)"
          % (CELLS_OUT, sum(len(v) for v in PLAN.values()), len(PLAN)))

if CELLS_IN:
    src = json.load(open(CELLS_IN))
    assert abs(src["cell"] - CELL) < 1e-9 and abs(src["thick"] - THICK) < 1e-9, \
        "cell list was built at a different cell/thickness"
    mine = sum(len(v) for v in PLAN.values())
    theirs = sum(len(v) for v in src["plan"].values())
    print("REPLAY %s: %d cells (this blend's own census would have said %d)"
          % (os.path.basename(CELLS_IN), theirs, mine))
    PLAN = {k: [tuple(p) for p in v] for k, v in src["plan"].items()}

# ------------------------------------------------------------------- emit ----
if not CENSUS:
    for fam in sorted(PLAN):
        cells = FAMCELLS.get(fam)
        assert cells, "cell list names family %r, which this blend does not have" % fam
        for (cx, cy, zmed) in PLAN[fam]:
            best, bd = None, 1e18
            for (ka, kb), (o, zz, kx, ky) in cells.items():
                d = (kx - cx) ** 2 + (ky - cy) ** 2
                if d < bd:
                    bd, best = d, o
            assert bd < (3 * CELL) ** 2, \
                "no %s block within %.2f m of (%.2f, %.2f)" % (fam, 3 * CELL, cx, cy)
            me = best.data
            if best.name not in TOUCHED:
                TOUCHED[best.name] = {
                    "verts": [tuple(v.co) for v in me.vertices],
                    "polys": [tuple(p.vertices) for p in me.polygons]}
            Minv = best.matrix_world.inverted()
            base = len(me.vertices)
            nv = []
            for dz in (0.0, -THICK):
                for dx, dy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
                    nv.append(tuple(Minv @ Vector((cx + dx * CELL, cy + dy * CELL,
                                                   zmed + dz))))
            nf = [(base, base + 3, base + 2, base + 1),
                  (base + 4, base + 5, base + 6, base + 7),
                  (base, base + 1, base + 5, base + 4),
                  (base + 1, base + 2, base + 6, base + 5),
                  (base + 2, base + 3, base + 7, base + 6),
                  (base + 3, base, base + 4, base + 7)]
            vs = [tuple(v.co) for v in me.vertices] + nv
            ps = [tuple(p.vertices) for p in me.polygons] + nf
            mats = [s.material for s in best.material_slots if s.material]
            me.clear_geometry()
            me.from_pydata(vs, [], ps)
            me.validate()
            me.update()
            me.materials.clear()
            for m in mats:
                me.materials.append(m)
            TOTAL_ADD += CELL * CELL

print("-" * 78)
print("enclosed holes %6.2f m2 · GIVEN BACK %6.2f m2 (%d cells) over %d mesh(es)"
      % (TOTAL_HOLE, TOTAL_ADD, int(round(TOTAL_ADD / (CELL * CELL))), len(TOUCHED)))
report["holeM2"] = TOTAL_HOLE
report["addM2"] = TOTAL_ADD
report["touched"] = sorted(TOUCHED)

if CENSUS:
    print("(census only — nothing written)")
    sys.exit(0)

for nm, st in TOUCHED.items():
    bpy.data.objects[nm][PROP] = json.dumps(st)

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
with open(MANIFEST, "w") as f:
    json.dump(report, f, indent=1)
print("manifest %s" % MANIFEST)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
