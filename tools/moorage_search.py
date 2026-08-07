# moorage_search.py — RING/CLEARANCE SEARCH for the weave-huts -> moorage flight
# (Bet 2 iteration 9 authored this in a scratchpad; 2026-08-07 brought it into the
# repo WITH THE ORACLE IT WAS MISSING.  A search whose oracles do not cover a
# corridor will sever that corridor again, silently, every time it is re-run.)
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
#       --python-exit-code 1 -P tools/moorage_search.py -- selftest
#   ... -- search           # the full sweep (writes moorage_search_results.json)
#
# The double switchback keeps generating pivot pathologies (r12, r20, r29, PT-049,
# §9.2's lip, and iteration 9's self-roofing landing at every width tried).  The
# ratified simplify shape (pilot precedent): wide-amplitude hairpins, grades <= 0.58,
# width 2.0.  Candidate geometry is town_blockout's OWN — the CURRENT generator:
# width-scaled pivot split, asymmetric landing extension, width-scaled LAND_LONG —
# so what is scored is what would be built.
#
# Oracles, each a rejection:
#   roof     — a tread roofing a guarded walk box (dy 0.50..1.50 over its top)
#   art      — non-walk art in the leg's body corridor (BVH ray up 1.70 / in-tread)
#   self     — the flight roofing ITSELF: any landing sample under a tread of its own
#              edge at dy in (0.63, 2.0], or a tread of one leg over another leg's
#              tread at plan-overlap with dy < 2.0
#   westarm  — THE ONE THAT WAS MISSING (2026-08-07).  The moorage's WEST BOARDWALK
#              must still join the west store to the pier with the candidate flight
#              standing in it.  The corridor is lattices at 0.15 m over the map's own
#              westlink rects; each cell's floor is measured off the WALK RECORDS (the
#              only thing WALKLOCK lets a foot catch in a del-* scene); the body window
#              is play3d's own [fy + STEP_UP + 0.02, fy + BODY_H]; a cell is blocked
#              when any tread or landing SLAB of the candidate enters that window with
#              the body's 0.30 m half-width added in plan (blocked() tests a BOX).  The
#              candidate is REJECTED unless the clear cells still flood-fill from the
#              west store rect to the pier rect.
#
#              WHY: the westlink rects (moorage_westlink.py, 2026-08-05) were shaped by
#              an occupancy scan of the body window under the OLD l2 line.  Iteration 9
#              re-searched wp2 and widened the edge 1.4 -> 2.0, and the new treads landed
#              on exactly the corridor that scan had chosen to dodge — t05 at 2.25..2.39
#              and t06 at 1.89..2.03 inside the [1.92, 2.55] window over the 1.25 deck,
#              1.00 m and 0.64 m of headroom against BODY_H 1.30.  The west waterfront
#              went back to being a one-way 92-cell island and reach_probe said no-path.
#              A FOOTPRINT SOLVED AGAINST A FLIGHT IS INVALIDATED WHEN THAT FLIGHT IS
#              RE-SEARCHED, and until this oracle existed nothing in the pipeline said so.
import bpy, math, json, sys, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = ("selftest" if "selftest" in argv else
        "detail" if "detail" in argv else "search")
DETAIL = [[float(v) for v in a.split(",")] for a in argv if a.count(",") == 3]
# the candidate dumps are megabytes of raw sweep and belong in scratch, not in git:
# the NUMBERS that matter are in the DAYLOG and on the map edge, and re-running the
# sweep is 13 seconds.
import tempfile
OUT = os.path.join(tempfile.gettempdir(), "moorage_search")

PIVOT_OFF, PIVOT_KNEE, PIVOT_SPAN, FOOT_TRIM = 1.20, 80.0, 70.0, 0.25
LAND_LONG, LAND_CROSS = 0.90, 1.40
WIDTH = 2.0
STEP_UP, BODY_H, BODY_R = 0.63, 1.30, 0.30

def pivot_split(prev, w, nxt, asym=False, width=1.4):
    a = Vector((w.x - prev.x, w.y - prev.y, 0)); d = Vector((nxt.x - w.x, nxt.y - w.y, 0))
    if a.length < 1e-6 or d.length < 1e-6: return w, w
    a.normalize(); d.normalize()
    th = math.degrees(math.acos(max(-1.0, min(1.0, a.dot(d)))))
    off = PIVOT_OFF * max(1.0, width / 1.4) * max(0.0, min(1.0, (th - PIVOT_KNEE) / PIVOT_SPAN))
    if off < 1e-3: return w, w
    s = -a; m = (s + d)
    if m.length < 1e-6: return w, w
    m.normalize(); n = s - m * s.dot(m)
    if n.length < 1e-6: return w, w
    n.normalize()
    if asym: return w, w - n * (2 * off)
    return w + n * off, w - n * off

def plan_trim(a, b, t):
    v = Vector((b.x - a.x, b.y - a.y, 0)); L = v.length
    if L <= t + 0.6: return b
    return b - v.normalized() * t

# ---- the fixed ends (map) -------------------------------------------------------
HEAD = Vector((71.45, 24.0, 7.83))
WP1  = Vector((76.2, 25.6, 5.6))
FOOT = Vector((76.2, 28.1, 1.25))    # ratified 2026-08-04: landing = moorage deck top
MOOR = Vector((76.09, 27.0, 1.0))

# ---- roof oracle: walk boxes the flight may not roof ----------------------------
ROOF_GUARD = []
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    n = o.name
    if not (n.startswith("walk_e_moorage__lock-five") or
            n.startswith("walk_e_moorage__tenant-shack") or
            n.startswith("walk_e_lockfive") or
            n == "walk_lm_moorage" or n == "walk_pad_tenant-shack" or
            n == "walk_pad_moorage"):
        continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    ROOF_GUARD.append((n, min(p.x for p in bb), max(p.x for p in bb),
                       min(p.y for p in bb), max(p.y for p in bb),
                       max(p.z for p in bb)))
print("roof-guard boxes:", len(ROOF_GUARD))

# ---- art oracle: BVH of every non-walk/bar triangle in the region ---------------
REG = (69.0, 88.0, 20.0, 34.0)
verts, tris = [], []
nsrc = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    n = o.name
    if n.startswith(("walk_", "bar_", "WRD_SRC_", "LKC_SRC_", "CLC_SRC_", "GSC_SRC_",
                     "PHC_SRC_", "LKC_", "lm_")):
        continue
    # the flight's own current art re-derives with the new line: exclude by NAME
    # (the lg_wv_rail lesson: never exclude by zone).
    if n.startswith(("wv_stair_", "lf_stair_", "cx_mr_", "cx_rail")):
        continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    if max(p.x for p in bb) < REG[0] or min(p.x for p in bb) > REG[1]: continue
    if max(p.y for p in bb) < REG[2] or min(p.y for p in bb) > REG[3]: continue
    me = o.evaluated_get(dg).to_mesh()
    mw = o.matrix_world
    keep = {}
    for p in me.polygons:
        ws = [mw @ me.vertices[i].co for i in p.vertices]
        if max(w.x for w in ws) < REG[0] - 1 or min(w.x for w in ws) > REG[1] + 1: continue
        if max(w.y for w in ws) < REG[2] - 1 or min(w.y for w in ws) > REG[3] + 1: continue
        idx = []
        for i, w in zip(p.vertices, ws):
            k = (o.name, i)
            if k not in keep:
                keep[k] = len(verts); verts.append(w.copy())
            idx.append(keep[k])
        for i in range(1, len(idx) - 1):
            tris.append((idx[0], idx[i], idx[i + 1]))
    o.evaluated_get(dg).to_mesh_clear()
    nsrc += 1
print("BVH: %d source objects, %d tris" % (nsrc, len(tris)))
BVH = BVHTree.FromPolygons(verts, tris)

# =================================================================================
# THE WEST-ARM CLEARANCE ORACLE (2026-08-07)
# =================================================================================
# The corridor is the map's own moorage footprint: the WEST STORE rect, the four
# westlink rects, and the PIER rect the flight lands on.  The corridor is a lattice;
# a candidate is judged on whether the west store still reaches the pier.
MAPJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "public", "townmap", "dellhollow.map.json")))
_MOOR_LM = [l for l in MAPJ["landmarks"] if l["id"] == "moorage"][0]
FP = _MOOR_LM["footprint"]
WEST_STORE = FP[1]                 # [70.9, 71.9, 26.2, 29.2]  the pit that started this
PIER       = FP[2]                 # [75.09, 76.89, 27.0, 31.3] the flight's own landing
LINK       = FP[3:7]               # the four 2026-08-05 westlink planks
CORRIDOR   = [WEST_STORE] + LINK + [PIER]
LAT = 0.15

# Floors come from the WALK RECORDS ONLY.  In a WALKLOCK scene (/^del-/) that is the
# only thing a foot may catch — grounding on art is how a spawn search lies (the
# 2026-08-06 arrivals lesson).  The flight's OWN records are excluded: they re-derive
# with the candidate line and must not be counted as this corridor's floor.
_FLIGHT = ("walk_e_weave-huts__moorage", "bar_e_weave-huts__moorage")
_WALKBOX = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("walk_"): continue
    if o.name.startswith(_FLIGHT): continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    _WALKBOX.append((min(p.x for p in bb), max(p.x for p in bb),
                     min(p.y for p in bb), max(p.y for p in bb),
                     max(p.z for p in bb)))

def _cells():
    """(i, j, x, y, fy) for every corridor lattice cell that has a walk floor in the
    deck band [0.80, 1.70].  i/j are lattice indices so the fill is a plain grid."""
    out = {}
    for (x0, x1, y0, y1) in CORRIDOR:
        i = int(math.floor(x0 / LAT)) + 1
        while i * LAT <= x1:
            j = int(math.floor(y0 / LAT)) + 1
            while j * LAT <= y1:
                x, y = i * LAT, j * LAT
                if (i, j) not in out:
                    best = None
                    for (bx0, bx1, by0, by1, top) in _WALKBOX:
                        if bx0 <= x <= bx1 and by0 <= y <= by1 and 0.80 <= top <= 1.70:
                            if best is None or top > best: best = top
                    if best is not None:
                        out[(i, j)] = (x, y, best)
                j += 1
            i += 1
    return out

CELLS = _cells()
def _in(rect, x, y): return rect[0] <= x <= rect[1] and rect[2] <= y <= rect[3]
SEED = [k for k, (x, y, f) in CELLS.items() if _in(WEST_STORE, x, y)]
GOAL = set(k for k, (x, y, f) in CELLS.items() if _in(PIER, x, y))
print("west-arm corridor: %d cells with a walk floor (seed %d in the west store, "
      "goal %d on the pier)" % (len(CELLS), len(SEED), len(GOAL)))

def _obb(cx, cy, cz, lx, ly, lz, ang):
    """town_blockout's cube: centre, dimensions, rotation about Z."""
    return (cx, cy, cz, lx / 2, ly / 2, lz / 2, math.cos(-ang), math.sin(-ang))

def _obb_hits(b, x, y, z0, z1):
    """Does slab `b` enter [z0, z1] at plan point (x, y) grown by BODY_R?"""
    cx, cy, cz, hx, hy, hz, c, s = b
    if cz + hz <= z0 or cz - hz >= z1: return False
    dx, dy = x - cx, y - cy
    lx = dx * c - dy * s
    ly = dx * s + dy * c
    return abs(lx) <= hx + BODY_R and abs(ly) <= hy + BODY_R

def slabs_of(legs, landings):
    """Every SOLID the built flight puts in the air: treads (stairs_leg) + landing
    slabs (the stairs branch of town_blockout).  Rails are deliberately NOT here —
    lay_stair_rails already clips them against walk_lm_*/walk_pad_* pads, and the
    corridor is walk_lm_moorage."""
    out = []
    for (a, b) in legs:
        v = b - a
        hl = Vector((v.x, v.y, 0)).length
        rise = b.z - a.z
        if hl < 1e-6: continue
        n = max(1, math.ceil(abs(rise) / 0.4))
        ang = math.atan2(v.y, v.x)
        for t in range(n):
            p0 = a + v * (t / n); p1 = a + v * ((t + 1) / n)
            z = min(p0.z, p1.z) + abs(rise / n)
            out.append((("t%02d" % t),
                        _obb((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, z,
                             max(hl / n, 0.35), WIDTH, 0.14, ang)))
    for (c, u, lx, ly, z) in landings:
        out.append(("landing", _obb(c.x, c.y, z - 0.08, lx, ly, 0.16,
                                    math.atan2(u.y, u.x))))
    return out

def west_arm(legs, landings, verbose=False):
    """REJECT unless the west store still reaches the pier under this flight.
    Returns (ok, n_blocked, min_headroom, worst_name, n_reached)."""
    slabs = slabs_of(legs, landings)
    # plan AABB per slab, so most cells are rejected without any box maths
    boxes = []
    for (nm, b) in slabs:
        cx, cy, cz, hx, hy, hz, c, s = b
        r = math.hypot(hx, hy) + BODY_R
        boxes.append((nm, b, cx - r, cx + r, cy - r, cy + r, cz - hz, cz + hz))
    free, blocked = {}, 0
    minhead, worst = 9.9, None
    for k, (x, y, fy) in CELLS.items():
        z0, z1 = fy + STEP_UP + 0.02, fy + BODY_H
        hit = None
        for (nm, b, ax0, ax1, ay0, ay1, bz0, bz1) in boxes:
            if x < ax0 or x > ax1 or y < ay0 or y > ay1: continue
            if bz1 <= z0 or bz0 >= z1: continue
            if _obb_hits(b, x, y, z0, z1):
                hit = nm
                h = bz0 - (fy + 0.02)          # headroom a body has under it
                if h < minhead: minhead, worst = h, nm
                break
        if hit is None: free[k] = (x, y, fy)
        else: blocked += 1
    # flood fill, 8-connected, honouring the step rule in BOTH directions
    seen = set(s for s in SEED if s in free)
    stack = list(seen)
    while stack:
        (i, j) = stack.pop()
        fy = free[(i, j)][2]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0: continue
                q = (i + di, j + dj)
                if q in seen or q not in free: continue
                if abs(free[q][2] - fy) > STEP_UP: continue
                seen.add(q); stack.append(q)
    ok = bool(seen & GOAL)
    if verbose:
        print("    west-arm: %d/%d cells clear, fill reached %d, pier cells reached %d"
              % (len(free), len(CELLS), len(seen), len(seen & GOAL)))
        print("    tightest slab over the corridor: %s at %.2f m of headroom "
              "(BODY_H %.2f)" % (worst, minhead, BODY_H))
    return ok, blocked, minhead, worst, len(seen & GOAL)

# =================================================================================

def corridor_hits(a, b, w):
    v = b - a
    hl = Vector((v.x, v.y, 0)).length
    if hl < 1e-6: return 0, []
    n = max(2, int(hl / 0.30))
    side = Vector((v.y, -v.x, 0)).normalized()
    hits = []; ns = 0
    for k in range(n + 1):
        p = a + v * (k / n)
        for c in (-w / 2 + 0.15, -w / 4, 0.0, w / 4, w / 2 - 0.15):
            q = p + side * c
            ns += 1
            hit = BVH.ray_cast(Vector((q.x, q.y, q.z + 0.25)), Vector((0, 0, 1)), 1.70)
            if hit[0] is not None:
                hits.append((round(q.x, 2), round(q.y, 2), round(q.z, 2), round(hit[0].z, 2)))
            hit2 = BVH.ray_cast(Vector((q.x, q.y, q.z + 0.25)), Vector((0, 0, -1)), 0.32)
            if hit2[0] is not None and hit2[0].z > q.z + 0.02:
                hits.append((round(q.x, 2), round(q.y, 2), round(q.z, 2), 'in-tread'))
    return ns, hits

def roof_violations(a, b):
    v = b - a
    hl = Vector((v.x, v.y, 0)).length
    if hl < 1e-6: return []
    n = max(2, int(hl / 0.20))
    bad = []
    for k in range(n + 1):
        p = a + v * (k / n)
        for (nm, x0, x1, y0, y1, top) in ROOF_GUARD:
            if x0 - WIDTH / 2 - 0.42 <= p.x <= x1 + WIDTH / 2 + 0.42 and \
               y0 - WIDTH / 2 - 0.42 <= p.y <= y1 + WIDTH / 2 + 0.42:
                dy = p.z - top
                if 0.50 <= dy <= 1.50:
                    bad.append((nm, round(p.x, 2), round(p.y, 2), round(dy, 2)))
    return bad

def leg_samples(a, b, w, step=0.25):
    v = b - a
    hl = Vector((v.x, v.y, 0)).length
    if hl < 1e-6: return []
    n = max(2, int(hl / step))
    side = Vector((v.y, -v.x, 0)).normalized()
    out = []
    for k in range(n + 1):
        p = a + v * (k / n)
        for c in (-w / 2 + 0.12, 0.0, w / 2 - 0.12):
            q = p + side * c
            out.append((q.x, q.y, p.z))
    return out

def self_roof(legs, landings):
    bad = []
    for (c, u, lx, ly, z) in landings:
        P = Vector((-u.y, u.x, 0))
        i = -lx / 2 + 0.1
        while i <= lx / 2 - 0.1 + 1e-9:
            j = -ly / 2 + 0.1
            while j <= ly / 2 - 0.1 + 1e-9:
                q = c + u * i + P * j
                for (s, f) in legs:
                    v = f - s
                    hl2 = Vector((v.x, v.y, 0)).length_squared
                    if hl2 < 1e-9: continue
                    t = max(0.0, min(1.0, ((q.x - s.x) * v.x + (q.y - s.y) * v.y) / hl2))
                    p = s + v * t
                    dplan = Vector((q.x - p.x, q.y - p.y, 0)).length
                    if dplan <= WIDTH / 2 - 0.05:
                        dy = p.z - z
                        if STEP_UP < dy <= 2.0:
                            bad.append(('land-under-leg', round(q.x, 2), round(q.y, 2),
                                        round(dy, 2)))
                j += 0.25
            i += 0.25
    for ai, (s1, f1) in enumerate(legs):
        for (x, y, z) in leg_samples(s1, f1, WIDTH):
            for bi, (s2, f2) in enumerate(legs):
                if bi == ai: continue
                v = f2 - s2
                hl2 = Vector((v.x, v.y, 0)).length_squared
                if hl2 < 1e-9: continue
                t = max(0.0, min(1.0, ((x - s2.x) * v.x + (y - s2.y) * v.y) / hl2))
                p = s2 + v * t
                dplan = Vector((x - p.x, y - p.y, 0)).length
                if dplan <= WIDTH / 2 - 0.05:
                    dy = p.z - z
                    if STEP_UP < dy <= 2.0:
                        bad.append(('leg-over-leg', round(x, 2), round(y, 2), round(dy, 2)))
    return bad


def build_line(wps, foot):
    """town_blockout's v2 geometry for pts = [HEAD, *wps, foot, MOOR]."""
    pts = [HEAD.copy()] + [w.copy() for w in wps] + [foot.copy(), MOOR.copy()]
    ends = [(pts[0], pts[0])]
    for i in range(1, len(pts) - 1):
        ends.append(pivot_split(pts[i - 1], pts[i], pts[i + 1], asym=(i == 1), width=WIDTH))
    ends.append((pts[-1], pts[-1]))
    legs = []
    for i in range(len(pts) - 1):
        s, f = ends[i][1], ends[i + 1][0]
        if i + 1 < len(pts) - 1 and f.z < s.z: f = plan_trim(s, f, FOOT_TRIM)
        elif i > 0 and s.z < f.z:              s = plan_trim(f, s, FOOT_TRIM)
        legs.append((s, f))
    landings = []
    for i in range(1, len(pts) - 1):
        A, Dp = ends[i]
        sep = Vector((Dp.x - A.x, Dp.y - A.y, 0))
        if sep.length > 1e-6:
            up_A = pts[i - 1].z >= pts[i + 1].z
            ext_a = 0.15 if up_A else LAND_CROSS / 2
            ext_d = LAND_CROSS / 2 if up_A else 0.15
            u = sep.normalized()
            lx = sep.length + ext_a + ext_d
            c = Vector(((A.x + Dp.x) / 2, (A.y + Dp.y) / 2, pts[i].z)) + \
                u * ((ext_d - ext_a) / 2)
            landings.append((c, u, lx, LAND_LONG * max(1.0, WIDTH / 1.4), pts[i].z))
        else:
            w = Vector((pts[i + 1].x - pts[i - 1].x, pts[i + 1].y - pts[i - 1].y, 0)).normalized()
            u = Vector((-w.y, w.x, 0))
            landings.append((Vector((pts[i].x, pts[i].y, pts[i].z)), u,
                             LAND_CROSS, LAND_LONG * max(1.0, WIDTH / 1.4), pts[i].z))
    return legs, landings


def judge(wps, foot, verbose=False):
    legs, landings = build_line(wps, foot)
    grades = []
    for (s, f) in legs:
        run = Vector((f.x - s.x, f.y - s.y, 0)).length
        rise = abs(f.z - s.z)
        g = rise / run if run > 1e-6 else 9
        grades.append(round(g, 2))
        if rise > 0.8 and run < 1.6: return None, grades, legs, landings
        if rise > 0.5 and g > 0.58:  return None, grades, legs, landings
    wa = west_arm(legs, landings, verbose=verbose)
    roofs, arts, head_art, foot_art = [], [], 0, 0
    for li, (s, f) in enumerate(legs):
        # THE MERGE LEG IS NOT A FLIGHT (2026-08-07).  The last leg runs from the foot
        # waypoint onto the landmark's own `pos`, so it lies ON the moorage deck for its
        # whole length and every `in-tread` hit under it is that deck's planking.  The
        # 2026-08-06 search had FOOT 1.1 m from MOOR and caught this with a 2.2 m radius;
        # a searched foot further out along the pier makes that radius wrong, not the
        # class.  Counted separately as foot_art and receipted by the drives.
        merge = (li == len(legs) - 1)
        for r in roof_violations(s, f):
            # THE OWN-PAD JOIN (pilot precedent): a line landing ON the moorage pad is
            # over that pad's airspace for its last stretch by construction.  The
            # west-arm oracle above is what makes this exemption safe — before it, this
            # `continue` was the hole the severance walked through.
            if r[0] in ("walk_lm_moorage", "walk_pad_moorage"): continue
            roofs.append(r)
        _, h = corridor_hits(s, f, WIDTH)
        for hh in h:
            dh = Vector((hh[0] - HEAD.x, hh[1] - HEAD.y, 0)).length
            df = Vector((hh[0] - foot.x, hh[1] - foot.y, 0)).length
            if dh < 2.0: head_art += 1
            elif hh[3] == 'in-tread' and (merge or df < 2.2): foot_art += 1
            else: arts.append(hh)
    selfr = self_roof(legs, landings)
    return {"grades": grades, "roof": len(roofs), "roof_sample": roofs[:2],
            "art": len(arts), "art_sample": arts[:4], "head_art": head_art,
            "foot_art": foot_art, "self": len(selfr), "self_sample": selfr[:3],
            "westarm_ok": wa[0], "westarm_blocked": wa[1],
            "westarm_head": round(wa[2], 2), "westarm_worst": wa[3],
            "westarm_goal": wa[4]}, grades, legs, landings


# =================================================================================
if MODE == "selftest":
    # THE ORACLE'S OWN TEST, in three cases.  A gate that measures its own drawing
    # cannot measure its own build — so the oracle is proved against the two flights
    # whose corridor verdict is ALREADY MEASURED in the engine.
    print("\n== A. NO FLIGHT AT ALL (can the instrument find the corridor?)")
    ok = west_arm([], [], verbose=True)
    print("   VERDICT %s (expected CONNECTED)" % ("CONNECTED" if ok[0] else "SEVERED"))

    print("\n== B. THE SHIPPED it.9 LINE wp2 [70.1, 29.4, 4.1] "
          "(engine says SEVERED: reach_probe no-path, 92-cell island)")
    r, g, legs, lands = judge([WP1, Vector((70.1, 29.4, 4.1))], FOOT, verbose=True)
    print("   grades %s | westarm_ok=%s blocked=%d" % (g, r["westarm_ok"], r["westarm_blocked"]))
    print("   VERDICT %s (expected SEVERED)" % ("CONNECTED" if r["westarm_ok"] else "SEVERED"))

    print("\n== C. THE PRE-it.9 LINE wp2 [72.6, 26.9, 3.3] at width 1.4 "
          "(the line the 2026-08-05 westlink rects were scanned under)")
    # the grade gate is bypassed here on purpose: that line was retired FOR its
    # geometry, and what is under test is only the corridor verdict.
    W = WIDTH
    globals()['WIDTH'] = 1.4
    legs2, lands2 = build_line([WP1, Vector((72.6, 26.9, 3.3))], FOOT)
    ok2 = west_arm(legs2, lands2, verbose=True)
    globals()['WIDTH'] = W
    print("   VERDICT %s (expected CONNECTED)" % ("CONNECTED" if ok2[0] else "SEVERED"))
    sys.exit(0)

if MODE == "detail":
    # WHERE the blocked cells fall matters more than how many: 30 cells lost on the
    # 4.3 x 1.8 m pier is nothing and 8 lost on a 1.1 m plank can be the whole corridor.
    RECTN = ["west-store", "link1", "link2", "link3", "link4", "pier"]
    for d in DETAIL:
        wp = Vector((d[0], d[1], d[2])); foot = Vector((FOOT.x, d[3], FOOT.z))
        res, grades, legs, landings = judge([WP1, wp], foot)
        if res is None:
            print("wp %s foot_y %.1f  REJECTED on grade %s" % (d[:3], d[3], grades)); continue
        slabs = slabs_of(legs, landings)
        per = {n: [0, 0] for n in RECTN}
        for k, (x, y, fy) in CELLS.items():
            z0, z1 = fy + STEP_UP + 0.02, fy + BODY_H
            bad = any(_obb_hits(b, x, y, z0, z1) for (nm, b) in slabs)
            for n, r in zip(RECTN, CORRIDOR):
                if _in(r, x, y):
                    per[n][1] += 1
                    if bad: per[n][0] += 1
        print("wp %s foot_y %.1f  grades %s  blocked %d  goal %d  head %.2f" %
              (d[:3], d[3], grades, res["westarm_blocked"], res["westarm_goal"],
               res["westarm_head"]))
        print("   " + "  ".join("%s %d/%d" % (n, per[n][0], per[n][1]) for n in RECTN))
    sys.exit(0)

# ---- the sweep ------------------------------------------------------------------
# COARSE finds the basin, FINE proves it is a basin and not a needle (iteration 9's
# clean-neighborhood robustness, at its own 0.25 m step).
FINE = "fine" in argv
GRID = ((68.35, 0.25, 8), (30.15, 0.25, 8), (3.5, 0.15, 8), (30.35, 0.25, 6)) if FINE \
    else ((68.6, 0.5, 15), (26.9, 0.5, 11), (3.2, 0.3, 7), (28.1, 0.5, 7))
results = []
stage = {"grade": 0, "westarm": 0, "roof": 0, "self": 0, "art": 0}
for xi in range(GRID[0][2]):
    for yi in range(GRID[1][2]):
        for zi in range(GRID[2][2]):
            wp = Vector((GRID[0][0] + GRID[0][1] * xi, GRID[1][0] + GRID[1][1] * yi,
                         GRID[2][0] + GRID[2][1] * zi))
            for fy in range(GRID[3][2]):
                foot = Vector((FOOT.x, GRID[3][0] + GRID[3][1] * fy, FOOT.z))
                res, grades, legs, landings = judge([WP1, wp], foot)
                if res is None:
                    stage["grade"] += 1
                    continue
                if not res["westarm_ok"]:
                    stage["westarm"] += 1
                    continue
                if res["roof"]: stage["roof"] += 1
                if res["self"]: stage["self"] += 1
                if res["art"]:  stage["art"] += 1
                res["wp"] = [round(wp.x, 2), round(wp.y, 2), round(wp.z, 2)]
                res["foot"] = [round(foot.x, 2), round(foot.y, 2), round(foot.z, 2)]
                results.append(res)

clean = [r for r in results if r["roof"] == 0 and r["art"] == 0 and r["self"] == 0]
print("REJECTED — grade %d | west-arm %d" % (stage["grade"], stage["westarm"]))
print("SURVIVED the west-arm oracle:", len(results), "| CLEAN of roof+art+self:", len(clean))
# robustness: prefer a candidate whose 0.5 m neighbours are also clean, then the
# gentlest last leg (iteration 9's own ranking)
CK = set((r["wp"][0], r["wp"][1], r["wp"][2], r["foot"][1]) for r in clean)
DX, DY, DZ = GRID[0][1], GRID[1][1], GRID[2][1]
def nbrs(r):
    x, y, z = r["wp"]; f = r["foot"][1]
    n = 0
    for dx in (-DX, 0, DX):
        for dy in (-DY, 0, DY):
            for dz in (-DZ, 0, DZ):
                if (round(x + dx, 2), round(y + dy, 2), round(z + dz, 2), f) in CK: n += 1
    return n
for r in clean: r["nbrs"] = nbrs(r)
clean.sort(key=lambda r: (-r["nbrs"], max(r["grades"][1:])))
for r in clean[:14]: print(json.dumps(r))
if not clean:
    for r in sorted(results, key=lambda r: r["roof"] + r["art"] + r["self"])[:14]:
        print(json.dumps(r))
os.makedirs(OUT, exist_ok=True)
FN = os.path.join(OUT, "search-results-fine.json" if FINE else "search-results.json")
json.dump({"clean": clean, "all": results, "rejected": stage}, open(FN, "w"))
print("wrote", FN)
