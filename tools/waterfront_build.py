"""waterfront_build.py — detail the Waterfront district IN THE MASTER.

  Blender -b tools/blends/dellhollow-master.blend -P tools/waterfront_build.py
  (append `save` to the argv to write the blend back)

Parcel `p-waterfront`  x 25.5..63.6  y 19.5..32.5  z -0.5..4.5
Members: winch-foot, fish-dock, deep-stairs-foot.

What the district inherits
--------------------------
East of the Boatyard's seam weld the town is walk ribbons over VOID: `seam_bank`
deliberately plunges to the river bed at x=40.1 (it ends as a rock spur), and
from there to Lock Five there is no ground, no cliff and no structure at all —
the boardwalk, the deep stairs' lower flights and the stilt clusters above them
float.  So the district is built in the order a real one would be: ground first,
then the deck the walk graph already describes, then the three landmarks, then
the working clutter.

Contract
--------
* `walk_*` / `bar_*` are canonical topology: never moved, never edited.  Ribbons
  that end up under real decking get `hide_render = True` ONLY (manifest 51 —
  `hide_viewport` would drop them from the glTF and the runtime would lose its
  collision).
* Everything this pass makes is prefixed `wf_` so the next district can tell
  whose it is; nothing non-diegetic is created, so nothing needs `fx_`.
* Props are placed through the walk Corridor (`free`/`find_free`), so no barrel
  ever lands in a walking line, and set dressing is composed FOR THE ROUND
  (manifest 57): everything here is either against the cliff, on staging outside
  the walk, or above head height.
"""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, plank_fill, offset_poly, plane_z_fn, point_in_poly,
                          clip_halfplane, dist_poly2, Corridor)

SAVE = "save" in sys.argv
rng = random.Random(20260730)
COLL = "DIST_waterfront"

# ---------------------------------------------------------------- constants
X0, X1 = 40.10, 66.00          # the ground this district owns (starts at the spur)
Y0, Y1 = 12.50, 31.00
WATER = 0.20                   # pool-mid level
BED = -4.60
DECK_DROP = 0.055

LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-30s %s" % (kind, what, why))


# --------------------------------------------------------------- materials
MD, MT, MTD = M("mat_deck"), M("mat_timber"), M("mat_timber_dark")
MROCK, MWET, MIRON = M("mat_rock"), M("mat_wet"), M("mat_iron")
MROPE, MFRESH = M("mat_rope"), M("mat_freshwood")
MRED, MBLUE = M("mat_paint_red"), M("mat_paint_blue")
MDARKWOOD, MWALL = M("mat_wallwood_dark"), M("mat_wallwood")
MGLASS = M("mat_lantern_glass")
MGRASS, MFERN = M("mat_grass"), M("mat_fern")
MVINE, MCREEP = M("mat_vine"), M("mat_leaf_creeper")
MSHINGLE = M("mat_shingle_mossy")


def plain(name, rgb, rough=0.72, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# a split fish drying on a rack is a pale, slightly translucent slab; keep it
# well under the deck's value or a rack of them reads as a row of lamps.
MFISH = plain("mat_fish", (0.196, 0.166, 0.122), rough=0.44)
MNET = plain("mat_net", (0.072, 0.062, 0.048), rough=0.88)
MCANVAS = plain("mat_canvas", (0.115, 0.098, 0.074), rough=0.90)

# ------------------------------------------------------------- collections
for c in (COLL, COLL + "_DECK", COLL + "_PROPS", COLL + "_VEG"):
    coll(c)

# idempotent: a re-run replaces this district, it does not stack a second one.
# NOTE `veg_wf_` as well as `wf_`: this district's foliage was migrated to the
# runtime no-stand prefix (tools/veg_prefix_migrate.py), and a clean-up that
# matches only the OLD prefix is finding 117 exactly — the rebuild would stack a
# second copy of every bush and the log would say nothing.
killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("wf_", "veg_wf_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
if killed:
    log("REBUILD", "%d wf_ objects cleared" % killed, "previous pass removed before rebuild")

# --------------------------------------------------------------- corridors
WALKS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
COR0 = Corridor(WALKS, margin=0.0)          # the surface itself
COR = Corridor(WALKS, margin=0.30)          # + the QA margin
KEEP = Corridor(WALKS, margin=0.55)         # where props may not go


def over_walk(x, y, z, pad=0.16):
    """True if a solid at (x,y,z) would stand in a walking line.

    The walk QA fires a ray DOWN onto every walk face and UP for 2 m above it,
    so anything whose footprint (not just its centre — hence `pad`) sits over a
    walk surface within that band is a blocker.  Every part this district places
    near the stairs is filtered through it rather than positioned by eye.
    """
    for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                   (pad * .7, pad * .7), (-pad * .7, pad * .7),
                   (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
        t = COR.top_at(x + dx, y + dy)
        if t is not None and t - 0.10 <= z <= t + 2.05:
            return True
    return False


# ===========================================================================
# 1. GROUND — the bank and the cliff the boardwalk hugs
# ===========================================================================
def noise(x, y):
    return (math.sin(x * 1.27 + y * 0.81) * 0.50 + math.sin(x * 0.47 - y * 2.03) * 0.30 +
            math.sin(x * 3.61 + y * 2.87) * 0.12) * 0.15


def toe(x):
    """Where rock meets water.  The gorge opens downstream, so the strand
    narrows and the boardwalk walks further out onto piles as it goes east."""
    return 24.30 - 0.062 * (x - 40.0)


STRAND = 2.30          # width of the flat rock shelf at the foot of the cliff


def wf_h(x, y):
    b = 1.06 - 0.010 * (x - 40.0)
    d = toe(x) - y
    if d <= 0.0:                                   # river side of the shoreline
        h = b - 2.30 * (-d) ** 1.06
    elif d < STRAND:
        # the strand: a low rock shelf the town stacks its barrels and nets on.
        # Without it the cliff starts AT the waterline and every prop stands on
        # a 40-degree bank, which is why the first pass placed none at all.
        h = b + 0.115 * d
    else:                                          # the cliff climbing to the Weave
        u = min((d - STRAND) / 7.0, 1.0)
        h = b + 0.115 * STRAND + 13.40 * (u * u * (3.0 - 2.0 * u))
        if d - STRAND > 7.0:
            h += 0.34 * (d - STRAND - 7.0)
    h += noise(x, y)
    # the Boatyard's spur ends in a flooded cleft at x=40.1; the Waterfront cliff
    # climbs back out of it over 2.2 m, which is why the seam's piles are 8 m long.
    t = min(max((x - X0) / 2.20, 0.0), 1.0)
    h = BED + (h - BED) * (t * t * (3.0 - 2.0 * t))
    return h


TOPS = [(poly, fn, raw, nm) for poly, fn, raw, nm in COR0.tops]


def clamp_walks(x, y, h):
    """Terrace the ground under every walkway (manifest 38)."""
    for poly, fn, raw, nm in TOPS:
        d = dist_poly2(x, y, raw)
        if d < 3.6:
            h = min(h, fn(x, y) - 0.45 + d * 1.15)
    return h


def ground_z(x, y):
    return max(clamp_walks(x, y, wf_h(x, y)), BED)


ST = 0.40
NX = int(round((X1 - X0) / ST)) + 1
NY = int(round((Y1 - Y0) / ST)) + 1
V, F = [], []
for i in range(NX):
    for j in range(NY):
        V.append((X0 + i * ST, Y0 + j * ST, ground_z(X0 + i * ST, Y0 + j * ST)))
for i in range(NX - 1):
    for j in range(NY - 1):
        a = i * NY + j
        F.append((a, a + NY, a + NY + 1, a + 1))
new_mesh("wf_ground", V, F, MROCK, COLL)
log("BUILD", "wf_ground", "%d x %d grid, x %.1f..%.1f y %.1f..%.1f — the bank and cliff "
    "carried east from the Boatyard spur, terraced under every walkway"
    % (NX, NY, X0, X1, Y0, Y1))


# ===========================================================================
# 2. DECKING over the walk ribbons the district owns
# ===========================================================================
DECK_NAMES = [
    "walk_e_fish-dock__winch-foot_l2", "walk_e_fish-dock__winch-foot_l1",
    "walk_e_fish-dock__winch-foot_l0", "walk_e_deep-stairs-foot__fish-dock_l0",
    "walk_pad_deep-stairs-foot", "walk_lm_fish-dock",
    "walk_e_tenant-shack__fish-dock_l1",
]
STAIR_NAMES = [o.name for o in WALKS
               if "deep-stairs-head__deep-stairs-foot" in o.name
               and world_bbox(o)[5] < 9.6]
PLANK_ANG = {"walk_lm_fish-dock": math.radians(0), "walk_pad_deep-stairs-foot": math.radians(90)}


def ribbon_angle(pts):
    best, ang = 0.0, 0.0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = (pts[j] - pts[i]).to_2d()
            if d.length > best:
                best, ang = d.length, math.atan2(d.y, d.x)
    return ang + math.pi / 2


def below_walk(px, py, pz):
    t = COR0.top_at(px, py)
    if t is not None and pz > t - 0.02:
        return False
    return not COR.blocked((px, py, pz))


deck, joists, piles, stairs = [], [], [], []
PILE_POS = []
for nm in DECK_NAMES + STAIR_NAMES:
    ob = bpy.data.objects.get(nm)
    if ob is None:
        continue
    is_stair = nm in STAIR_NAMES
    Mx = ob.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for pi, p in enumerate(ob.data.polygons):
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
        cx = sum(v.x for v in raw) / len(raw)
        cy = sum(v.y for v in raw) / len(raw)
        cz = sum(v.z for v in raw) / len(raw)
        top = COR0.top_at(cx, cy)
        if top is not None and top > cz + 0.15:
            continue                                  # buried face (manifest 36)
        # A tread plank must never overhang: the tread below is only 0.38 m down,
        # so 60 mm of overhang both blocks the down-ray onto that tread and eats
        # its headroom.  Stairs are INSET; flat decking is generous.
        poly = offset_poly(raw, -0.045 if is_stair else 0.50)
        zfn = plane_z_fn(raw)
        ang = PLANK_ANG.get(nm, ribbon_angle(raw))
        v, f = plank_fill(poly, ang, w=0.26 if is_stair else 0.29, gap=0.014,
                          thick=0.09 if is_stair else 0.11, jitter=0.010,
                          drop=DECK_DROP, zfn=zfn, seed=(hash(nm) + pi) & 0xffff,
                          keep=None if is_stair else
                          (lambda px, py, pz: below_walk(px, py, pz)))
        tgt = stairs if is_stair else deck
        tgt.append(new_mesh("wf_d_%d" % len(tgt), v, f, MD, COLL + "_DECK"))
        if is_stair:
            continue
        xs = [q.x for q in poly]
        ys = [q.y for q in poly]
        ax0, ax1, ay0, ay1 = min(xs), max(xs), min(ys), max(ys)
        long_x = (ax1 - ax0) >= (ay1 - ay0)
        u = (ax0 if long_x else ay0) + 0.4
        lim = (ax1 if long_x else ay1) - 0.35
        while u <= lim:
            if long_x:
                seg = clip_halfplane(clip_halfplane(poly, 1, 0, u + 0.09), -1, 0, -(u - 0.09))
            else:
                seg = clip_halfplane(clip_halfplane(poly, 0, 1, u + 0.09), 0, -1, -(u - 0.09))
            if len(seg) >= 3:
                w = [q.y for q in seg] if long_x else [q.x for q in seg]
                a0, a1 = min(w), max(w)
                pa = (u, a0) if long_x else (a0, u)
                pb = (u, a1) if long_x else (a1, u)
                mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                if all(below_walk(q[0], q[1], zfn(q[0], q[1]) - 0.19) for q in (pa, pb, mid)):
                    joists.append(beam("jo", (pa[0], pa[1], zfn(*pa) - 0.28),
                                       (pb[0], pb[1], zfn(*pb) - 0.28), 0.13, 0.18,
                                       MTD, COLL + "_DECK"))
            u += 0.95
        gx = ax0 + 0.6
        while gx < ax1 - 0.4:
            gy = ay0 + 0.6
            while gy < ay1 - 0.4:
                if point_in_poly(gx, gy, poly) and below_walk(gx, gy, zfn(gx, gy) - 0.30):
                    zt = zfn(gx, gy) - 0.30
                    zb = min(ground_z(gx, gy), WATER - 0.1) - 0.40
                    if zt - zb > 0.9:
                        piles.append(cyl("pl", (gx, gy, zb), (gx, gy, zt),
                                         0.135 + rng.random() * 0.045, 7,
                                         MWET if zb < WATER else MTD, COLL + "_DECK"))
                        PILE_POS.append((gx, gy, zb, zt))
                gy += 1.55
            gx += 1.55

join_meshes(deck, "wf_planking", COLL + "_DECK")
join_meshes(joists, "wf_joists", COLL + "_DECK")
join_meshes(piles, "wf_piles", COLL + "_DECK")
log("BUILD", "wf_planking / joists / piles",
    "decking laid to %d walk ribbons + the fish-dock pad; %d piles to the bed"
    % (len(DECK_NAMES), len(piles)))


# ---- the deep stairs get treads and a stringer, not plank fill ------------
# One stringer per FLIGHT, run OUTBOARD of the treads.  A per-tread stringer is
# always over the next tread down, which is the same overhang problem as the
# planks: it blocks that tread's down-ray and eats its headroom.
strp = []
flights = {}
for nm in STAIR_NAMES:
    if "landing" in nm:
        continue
    key = nm.rsplit("_t", 1)[0]
    b = world_bbox(bpy.data.objects[nm])
    flights.setdefault(key, []).append(
        (Vector(((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[4])), b))
for key, treads in flights.items():
    if len(treads) < 2:
        continue
    treads.sort(key=lambda t: -t[0].z)
    a, b0 = treads[0][0], treads[-1][0]
    run = Vector((b0.x - a.x, b0.y - a.y, 0.0))
    if run.length < 0.2:
        continue
    ax = run.normalized()
    pp = Vector((-ax.y, ax.x, 0.0))
    # half-width of the flight measured ACROSS the run
    hw = 0.0
    for c, bb in treads:
        for cx2, cy2 in ((bb[0], bb[2]), (bb[1], bb[2]), (bb[1], bb[3]), (bb[0], bb[3])):
            hw = max(hw, abs((cx2 - c.x) * pp.x + (cy2 - c.y) * pp.y))
    hw += 0.13
    def clear_end(p, d):
        """Walk an endpoint back along the run until it is out of every corridor
        it would otherwise stand over (the flights zigzag, so 'outboard of this
        flight' is regularly 'straight over the one below')."""
        for k in range(26):
            q = p + d * (0.10 * k)
            t = COR.top_at(q.x, q.y)
            if t is None or q.z < t - 0.10:
                return q
        return p + d * 2.6

    def blocked_at(q):
        return over_walk(q.x, q.y, q.z + 0.20, pad=0.16)

    for sgn in (1, -1):
        p0 = clear_end(a + pp * (hw * sgn) - ax * 0.40 + Vector((0, 0, -0.16)), ax)
        p1 = clear_end(b0 + pp * (hw * sgn) + ax * 0.40 + Vector((0, 0, -0.16)), -ax)
        # ends alone are not enough — the flight below can cut the MIDDLE of the
        # run, so walk both ends in until every sample along it is clear.
        for _ in range(24):
            n = 12
            bad = [k for k in range(n + 1) if blocked_at(p0.lerp(p1, k / n))]
            if not bad or (p1 - p0).length < 0.9:
                break
            if sum(bad) / len(bad) < n / 2:
                p0 = p0.lerp(p1, 0.10)
            else:
                p1 = p1.lerp(p0, 0.10)
        if (p1 - p0).length < 0.9 or any(blocked_at(p0.lerp(p1, k / 12)) for k in range(13)):
            continue
        strp.append(beam("st", p0, p1, 0.11, 0.40, MTD, COLL + "_DECK"))
join_meshes(stairs, "wf_stair_treads", COLL + "_DECK")
join_meshes(strp, "wf_stair_stringers", COLL + "_DECK")
log("BUILD", "wf_stair_treads / stringers",
    "%d treads + landings of the deep stairs' lower flights given timber" % len(STAIR_NAMES))


# ===========================================================================
# 3. RAILING on the river side of the boardwalk
# ===========================================================================
def rail_run(pts, name, h=1.02):
    """Posts + two rails along a polyline of (x, y, deck_z)."""
    parts = []
    for x, y, z in pts:
        parts.append(obox("rp", x, y, z - 0.30 + (h + 0.32) / 2, 0.11, 0.11, h + 0.32,
                          rz=rng.random() * 0.2, mat=MT, cname=COLL + "_DECK"))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for dz, sec in ((h, (0.09, 0.10)), (h * 0.55, (0.07, 0.07))):
            parts.append(beam("rr", (a[0], a[1], a[2] + dz), (b[0], b[1], b[2] + dz),
                              sec[0], sec[1], MT, COLL + "_DECK"))
    return parts


def outer_edge(x, ylo, yhi, out=0.30):
    """The deck point `out` metres OUTBOARD of the walk's northern lip at x.

    Scanning south from open water finds the lip; the rail then belongs on the
    river side of it, on the decking's own overhang.  (The first pass put it
    `out` metres the wrong way and stood every post in the walking line — the
    down-ray QA named the exact samples.)
    """
    y = yhi
    z = None
    while y > ylo:
        z = COR0.top_at(x, y)
        if z is not None:
            break
        y -= 0.04
    if z is None:
        return None
    py = y + out
    while py < y + 1.2 and COR.top_at(x, py) is not None:
        py += 0.04
    return (x, py, z)


rails = []
edge = []
x = 41.0
while x <= 58.4:
    e = outer_edge(x, 24.0, 30.8)
    if e:
        edge.append(e)
    x += 1.75
rails += rail_run(edge, "wf_rail_walk")
fd = []
x = 55.4
while x <= 62.9:
    e = outer_edge(x, 28.0, 33.2)
    if e:
        fd.append(e)
    x += 1.7
rails += rail_run(fd, "wf_rail_dock")
join_meshes(rails, "wf_railings", COLL + "_DECK")
log("BUILD", "wf_railings", "%d bays along the river lip of the walk + the dock's north "
    "face, every post set outboard of the walk face by search" % (len(edge) + len(fd)))


# ===========================================================================
# 4. STAGING — the working surfaces that are NOT walkable
# ===========================================================================
def staging(name, x0, x1, y0, y1, z, ang=math.radians(90), skirt=True, mat=None):
    poly = [Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))]
    v, f = plank_fill(poly, ang, w=0.30, gap=0.016, thick=0.12, jitter=0.014, drop=0.0,
                      zfn=lambda X, Y: z, seed=hash(name) & 0xffff)
    parts = [new_mesh(name, v, f, mat or MD, COLL + "_DECK")]
    n = max(1, int((x1 - x0 - 0.8) / 1.5))
    for k in range(n + 1):
        u = x0 + 0.45 + k * (x1 - x0 - 0.9) / max(n, 1)
        parts.append(beam("jo", (u, y0, z - 0.22), (u, y1, z - 0.22), 0.13, 0.20, MT,
                          COLL + "_DECK"))
        if not skirt:
            continue
        m = max(1, int((y1 - y0 - 0.8) / 1.6))
        for q in range(m + 1):
            w = y0 + 0.42 + q * (y1 - y0 - 0.85) / max(m, 1)
            zb = min(ground_z(u, w), WATER - 0.1) - 0.45
            if z - 0.3 - zb > 0.8:
                parts.append(cyl("pl", (u, w, zb), (u, w, z - 0.28),
                                 0.13 + rng.random() * 0.04, 7,
                                 MWET if zb < WATER else MTD, COLL + "_DECK"))
    return join_meshes(parts, name, COLL + "_DECK")


# the fish dock's working platform: north of the walkable pad, over the water,
# so racks and tables never stand in a walking line (manifest 35)
staging("wf_stage_fish", 55.30, 63.10, 32.05, 35.10, 1.14, ang=math.radians(0))
# a plank bench laid ON the strand for the nets and barrels nearest the walk
staging("wf_stage_strand", 45.20, 50.60, 22.20, 23.40, 1.42, ang=math.radians(0), skirt=False)
# the winch's landing stage: what the sling is lowered onto
staging("wf_stage_winch", 31.55, 34.55, 20.90, 23.05, 1.32, ang=math.radians(90))
# a low landing beside the dock, at the water, where the skiffs come alongside
staging("wf_stage_landing", 57.20, 61.60, 35.10, 37.00, 0.62, ang=math.radians(0))
log("BUILD", "wf_stage_* x4", "fish platform, strand bench, winch landing, skiff stage — "
    "all OUTSIDE the walk corridors, so the working clutter never blocks a line")


# ===========================================================================
# 5. THE DEEP STAIRS' MOUTH  (mapVisible:false — the discreet route)
# ===========================================================================
def stairmouth():
    parts = []
    # replace the blockout portal
    gone = []
    for nm in ("lm_deep-stairs-foot_postL", "lm_deep-stairs-foot_postR",
               "lm_deep-stairs-foot_lintel"):
        o = bpy.data.objects.get(nm)
        if o:
            gone.append(nm)
            bpy.data.objects.remove(o, do_unlink=True)
    log("REPLACE", "lm_deep-stairs-foot_*", "blockout trilithon (%d parts) -> a real timber "
        "gate, hood and lit recess" % len(gone))
    zd = COR0.top_at(43.0, 26.0) or 1.0
    # gate posts, set just outside the pad so the doorway itself stays clear
    # The stair pad and the fish-dock ribbon cross here, so the doorway is 4 m of
    # continuous corridor: a post anywhere inside it is a bollard in the middle
    # of the route.  Walk each post outwards in y until the Corridor lets go.
    def clear_post(px, py0, step):
        py = py0
        for _ in range(80):
            if not KEEP.blocked((px, py, zd + 0.4)) and KEEP.top_at(px, py) is None:
                return py
            py += step
        return py

    GY = (clear_post(43.0, 26.0, -0.05), clear_post(43.0, 26.0, 0.05))
    for px in (41.44, 44.56):
        for py in GY:
            parts.append(obox("gp", px, py, zd - 0.35 + 3.55 / 2, 0.24, 0.24, 3.55,
                              rz=0.03, mat=MTD, cname=COLL))
    # head beams and a plank hood that throws the mouth into shadow
    for py in GY:
        parts.append(beam("gh", (41.22, py, zd + 3.05), (44.78, py, zd + 3.05), 0.22, 0.28,
                          MTD, COLL))
    for px in (41.44, 44.56):
        parts.append(beam("gx", (px, GY[0], zd + 3.05), (px, GY[1], zd + 3.05), 0.20, 0.26,
                          MTD, COLL))
    for k in range(9):
        u = 41.30 + k * 0.40
        parts.append(box("hd", u, u + 0.36, GY[0] - 0.15, GY[1] + 0.15,
                         zd + 3.18 + k * 0.035, zd + 3.30 + k * 0.035, MD, COLL))
    # a sign board and the tell-tale: a single lantern at the entrance
    parts.append(obox("sg", 43.02, GY[1] - 0.10, zd + 2.72, 1.30, 0.08, 0.36, rz=0.02,
                      mat=MDARKWOOD, cname=COLL))
    # the recess: a timber-lined throat set back into the cliff behind the gate,
    # dark because it is roofed and faces away from the key
    # A cover over the first FLIGHT was tried and abandoned: the deep stairs
    # zigzag, so anything carried on the l4 tread line stands over l3 — the
    # down-ray QA found seven blocked samples on the flight above.  The mouth
    # gets its shadow from the hood and from a boarded screen on the cliff side
    # of the pad, both of which sit outside every corridor.
    scz = zd
    kept = []
    for k in range(7):
        u = 39.20 + k * 0.42
        if any(over_walk(u + 0.19, GY[0] - 0.20 + dy, zq, pad=0.30)
               for zq in (scz + 0.4, scz + 1.4, scz + 2.4, scz + 2.9, scz + 3.4)
               for dy in (-0.30, 0.0, 0.30)):
            continue
        kept.append(u)
        parts.append(box("sc", u, u + 0.38, GY[0] - 0.34, GY[0] - 0.06,
                         scz - 0.5, scz + 2.9 + 0.06 * k, MTD, COLL))
    if kept:
        parts.append(beam("sb", (min(kept) - 0.05, GY[0] - 0.20, scz + 3.05),
                          (max(kept) + 0.43, GY[0] - 0.20, scz + 3.05), 0.18, 0.24,
                          MTD, COLL))
    return join_meshes(parts, "wf_stairmouth", COLL)


stairmouth()
log("BUILD", "wf_stairmouth", "gate posts + head beams + plank hood + a roofed throat back "
    "into the cliff: the route reads as going up INTO shadow")


# ===========================================================================
# 6. THE CARGO WINCH FOOT
# ===========================================================================
def winch():
    parts, ropes = [], []
    zf = 1.32
    # the tackle: double block hanging off the winch arm, hook and fall
    hx, hy = 32.80, 22.00
    top = 8.60
    for s in (-0.13, 0.13):
        ropes.append(cyl("fl", (hx + s, hy, top), (hx + s, hy, zf + 2.05), 0.022, 6,
                         MROPE, COLL))
    parts.append(obox("bl", hx, hy, zf + 1.86, 0.34, 0.20, 0.46, mat=MTD, cname=COLL))
    parts.append(cyl("sh", (hx - 0.20, hy, zf + 1.86), (hx + 0.20, hy, zf + 1.86), 0.09, 8,
                     MIRON, COLL))
    parts.append(cyl("hk", (hx, hy, zf + 1.63), (hx, hy, zf + 1.28), 0.045, 6, MIRON, COLL))
    # the sling on the stage: crates in a net, ready to go up
    for i, (dx, dy, dz, sz) in enumerate(((-0.42, -0.28, 0.0, 0.74), (0.36, -0.16, 0.0, 0.68),
                                          (-0.05, 0.34, 0.0, 0.62), (0.10, 0.02, 0.70, 0.60))):
        parts.append(obox("cr", hx + dx, hy + dy, zf + dz + sz / 2, sz, sz * 0.92, sz,
                          rz=rng.random() * 0.5, mat=MDARKWOOD, cname=COLL))
        parts.append(obox("cb", hx + dx, hy + dy, zf + dz + sz / 2, sz * 1.02, sz * 0.06, sz * 1.02,
                          rz=rng.random() * 0.5, mat=MT, cname=COLL))
    # net over the pile
    for k in range(9):
        a = 2 * math.pi * k / 9
        ropes.append(cyl("nt", (hx + math.cos(a) * 0.78, hy + math.sin(a) * 0.72, zf + 0.05),
                         (hx, hy, zf + 1.26), 0.020, 5, MROPE, COLL))
    # snubbing posts and a coil
    for px, py in ((31.75, 20.98), (34.35, 21.05)):
        parts.append(cyl("bo", (px, py, zf - 0.5), (px, py, zf + 0.62), 0.13, 9, MTD, COLL))
    join_meshes(ropes, "wf_winch_tackle", COLL)
    return join_meshes(parts, "wf_winch_load", COLL)


winch()
log("BUILD", "wf_winch_load / wf_winch_tackle",
    "block-and-hook on the fall, four crates slung in a net on the landing stage, "
    "snubbing posts — the winch now reads as WORKING, not as a mast")


# ===========================================================================
# 7. THE FISH DOCK
# ===========================================================================
def fish_dock():
    racks, fish, props, ropes = [], [], [], []
    zs = 1.14                                   # the staging deck
    # three drying racks across the platform, legs on the staging
    for r, ry in enumerate((32.80, 34.35)):
        htop = zs + 2.10 + r * 0.14
        for px in (55.75, 59.30, 62.75):
            racks.append(obox("lg", px, ry, zs + (htop - zs) / 2, 0.13, 0.13, htop - zs,
                              mat=MT, cname=COLL))
        racks.append(beam("bar", (55.55, ry, zs + (htop - zs)), (62.95, ry, zs + (htop - zs)),
                          0.10, 0.10, MT, COLL))
        # the catch: split fish over the bar, in irregular runs
        u = 55.9
        while u < 62.8:
            # fish hang in gappy runs with bare bar between them; a solid wall of
            # them reads as a fence, not as a catch.
            if rng.random() < 0.70:
                L = 0.42 + rng.random() * 0.20
                fish.append(obox("fs", u, ry, zs + (htop - zs) - L / 2 - 0.05,
                                 0.070, 0.155 + rng.random() * 0.060, L,
                                 rz=(rng.random() - 0.5) * 0.45, mat=MFISH, cname=COLL))
            u += 0.24 + rng.random() * 0.14
    # gutting table with a tub and a board
    tx, ty = 57.60, 32.60
    props.append(box("tb", tx - 0.90, tx + 0.90, ty - 0.42, ty + 0.42, zs + 0.80, zs + 0.90,
                     MFRESH, COLL))
    for dx in (-0.78, 0.78):
        for dy in (-0.32, 0.32):
            props.append(obox("tl", tx + dx, ty + dy, zs + 0.40, 0.09, 0.09, 0.80,
                              mat=MT, cname=COLL))
    props.append(cyl("tu", (tx + 1.35, ty, zs + 0.02), (tx + 1.35, ty, zs + 0.46), 0.36, 12,
                     MTD, COLL, r2=0.42))
    for dx in (-1.25, 1.25):
        for dy in (-0.75, 0.75):
            props.append(obox("ap", tx + dx, ty + dy, zs + 1.12, 0.10, 0.10, 2.24,
                              mat=MT, cname=COLL))
    for k in range(7):
        f0, f1 = k / 7.0, (k + 1) / 7.0
        y0c = ty - 0.80 + 1.60 * f0
        y1c = ty - 0.80 + 1.60 * f1
        sagv = 0.24 * math.sin(math.pi * (f0 + f1) / 2)
        props.append(box("aw", tx - 1.34, tx + 1.34, y0c, y1c,
                         zs + 2.20 - sagv, zs + 2.26 - sagv, MCANVAS, COLL))
    # salt barrels and crates of fish along the platform
    for i, (px, py) in enumerate(((61.10, 32.55), (61.85, 32.70), (56.10, 32.45),
                                  (62.55, 34.10), (55.70, 34.30))):
        props.append(cyl("bl", (px, py, zs), (px, py, zs + 0.86), 0.31, 12, MDARKWOOD,
                         COLL, r2=0.28))
        for zz in (0.20, 0.62):
            props.append(cyl("bd", (px, py, zs + zz), (px, py, zs + zz + 0.06), 0.325, 12,
                             MIRON, COLL))
    # net piles and a float line strung between two poles
    for i, (px, py) in enumerate(((59.9, 34.85), (56.9, 34.75))):
        for k in range(15):
            a = rng.random() * 6.28
            rr = rng.random() ** 0.6 * 0.60
            rad = 0.32 - 0.21 * (rr / 0.60)
            props.append(cyl("np", (px + math.cos(a) * rr, py + math.sin(a) * rr, zs + 0.01),
                             (px + math.cos(a) * rr * 1.05, py + math.sin(a) * rr * 1.05,
                              zs + 0.12 + rng.random() * 0.15),
                             rad, 8, MNET, COLL, r2=rad * 0.55))
    for px in (55.60, 63.00):
        props.append(obox("fp", px, 35.00, zs + 1.25, 0.11, 0.11, 2.50, mat=MT, cname=COLL))
    for k in range(13):
        u = 55.60 + (63.00 - 55.60) * k / 12
        sag = 2.34 - 0.55 * math.sin(math.pi * k / 12)
        if k < 12:
            u2 = 55.60 + (63.00 - 55.60) * (k + 1) / 12
            sag2 = 2.34 - 0.55 * math.sin(math.pi * (k + 1) / 12)
            ropes.append(cyl("fl", (u, 35.00, zs + sag), (u2, 35.00, zs + sag2), 0.018, 5,
                             MROPE, COLL))
        if k % 2 == 0:
            props.append(cyl("bu", (u, 35.00, zs + sag - 0.28), (u, 35.00, zs + sag - 0.06),
                             0.14, 9, MRED if (k // 2) % 2 else MBLUE, COLL))
    # a hoist pole over the water for landing the catch
    props.append(obox("hp", 62.90, 33.30, zs + 1.70, 0.16, 0.16, 3.40, mat=MT, cname=COLL))
    props.append(beam("ha", (62.90, 33.30, zs + 3.20), (62.90, 36.20, zs + 2.85), 0.13, 0.13,
                      MT, COLL))
    ropes.append(cyl("hl", (62.90, 36.10, zs + 2.86), (62.90, 36.10, zs + 1.30), 0.020, 5,
                     MROPE, COLL))
    join_meshes(racks, "wf_fish_racks", COLL)
    join_meshes(fish, "wf_fish_catch", COLL)
    join_meshes(ropes, "wf_fish_lines", COLL)
    return join_meshes(props, "wf_fish_gear", COLL)


fish_dock()
log("BUILD", "wf_fish_* x4", "3 drying racks with hanging split catch, gutting table + tub, "
    "salt barrels, net piles, a float line and a hoist pole")


# ===========================================================================
# 8. MOORED SKIFFS
# ===========================================================================
def skiff(name, cx, cy, cz, rz, L=4.30, B=1.44, D=0.70):
    """A small clinker skiff.

    The first attempt lofted one open sheet of five stations and read from every
    camera as a curved sliver of plank: a boat is not a surface, it is a SOLID
    with a sheer you can see the inside of.  This one lofts nine stations of a
    U-section, closes the sheer with a gunwale band, floors it, and stands a stem
    and a transom, so it reads as a hull from the deck above and from the water.
    """
    NS, NP = 9, 11
    ST = []
    for i in range(NS):
        t = -0.5 + i / (NS - 1.0)
        # beam and depth curves: fine forward, full amidships, cut away aft
        bw = max(0.06, (math.cos(math.pi * t) ** 0.85))
        bw *= 1.0 - 0.30 * max(0.0, t) ** 2
        dp = 0.62 + 0.38 * math.cos(math.pi * t) ** 0.6
        ST.append((t, bw, dp))

    def hull_pt(t, bw, dp, k):
        u = -1.0 + 2.0 * k / (NP - 1.0)
        y = B / 2 * bw * u
        z = -D * dp * (1.0 - abs(u) ** 1.75)
        return Vector((t * L, y, z))

    V, F = [], []
    c, sn = math.cos(rz), math.sin(rz)

    def put(p):
        V.append((cx + p.x * c - p.y * sn, cy + p.x * sn + p.y * c, cz + p.z + D * 0.34))
        return len(V) - 1

    grid = [[put(hull_pt(t, bw, dp, k)) for k in range(NP)] for t, bw, dp in ST]
    for i in range(NS - 1):
        for k in range(NP - 1):
            F.append((grid[i][k], grid[i + 1][k], grid[i + 1][k + 1], grid[i][k + 1]))
    # gunwale band: the sheer folded inboard, so the hull has a visible edge
    inner = [[put(hull_pt(t, bw * 0.86, dp * 0.90, k)) for k in (0, NP - 1)]
             for t, bw, dp in ST]
    for i in range(NS - 1):
        F.append((grid[i][0], inner[i][0], inner[i + 1][0], grid[i + 1][0]))
        F.append((grid[i][NP - 1], grid[i + 1][NP - 1], inner[i + 1][1], inner[i][1]))
    # floorboards, so you cannot see through the boat into the river bed
    fl = [[put(Vector((t * L, B / 2 * bw * 0.82 * u, -D * dp * 0.36)))
           for u in (-1.0, 1.0)] for t, bw, dp in ST]
    for i in range(NS - 1):
        F.append((fl[i][0], fl[i + 1][0], fl[i + 1][1], fl[i][1]))
    # transom
    t, bw, dp = ST[-1]
    F.append(tuple(reversed([grid[NS - 1][k] for k in range(NP)])))
    ob = new_mesh(name, V, F, MTD, COLL)
    parts = [ob]
    # stem post, thwarts and a shipped oar
    parts.append(beam("sp", (cx + (0.50 * L + 0.06) * c, cy + (0.50 * L + 0.06) * sn,
                             cz + D * 0.20),
                      (cx + (0.44 * L) * c, cy + (0.44 * L) * sn, cz + D * 0.62),
                      0.09, 0.13, MTD, COLL))
    for tt in (-0.20, 0.06, 0.30):
        px = tt * L
        hw = B / 2 * max(0.16, math.cos(math.pi * tt) ** 0.85) * 0.90
        parts.append(beam("th", (cx + px * c + hw * sn, cy + px * sn - hw * c, cz + D * 0.06),
                          (cx + px * c - hw * sn, cy + px * sn + hw * c, cz + D * 0.06),
                          0.22, 0.055, MFRESH, COLL))
    parts.append(beam("oa", (cx - (0.42 * L) * c - 0.18 * sn, cy - (0.42 * L) * sn + 0.18 * c,
                             cz + D * 0.04),
                      (cx + (0.30 * L) * c - 0.48 * sn, cy + (0.30 * L) * sn + 0.48 * c,
                       cz + D * 0.18), 0.065, 0.045, MFRESH, COLL))
    return join_meshes(parts, name, COLL)


SK = []
# float the hull so its FLOOR is above the pool surface — sunk 0.10 the water
# plane cut straight through the boat and the river rendered inside it.
SK.append(skiff("wf_skiff_dock", 59.10, 37.90, WATER + 0.18, math.radians(-8)))
SK.append(skiff("wf_skiff_walk", 47.60, 31.30, WATER + 0.18, math.radians(104), L=3.90))
painters = []
for (sx, sy), (bx, by) in ((SK[0].location.copy()[:2] if False else (59.1, 37.9), (60.4, 35.2)),
                           ((47.6, 31.3), (46.9, 29.5))):
    bz = COR0.top_at(bx, by)
    if bz is None:
        bz = ground_z(bx, by)
    painters.append(cyl("bo", (bx, by, bz - 0.30), (bx, by, bz + 0.52), 0.115, 9, MTD, COLL))
    for k in range(6):
        f0, f1 = k / 6.0, (k + 1) / 6.0
        p0 = Vector((sx + (bx - sx) * f0, sy + (by - sy) * f0,
                     WATER + 0.22 + (bz + 0.42 - WATER - 0.22) * f0 - 0.20 * math.sin(math.pi * f0)))
        p1 = Vector((sx + (bx - sx) * f1, sy + (by - sy) * f1,
                     WATER + 0.22 + (bz + 0.42 - WATER - 0.22) * f1 - 0.20 * math.sin(math.pi * f1)))
        painters.append(cyl("pt", p0, p1, 0.020, 5, MROPE, COLL))
# stakes and a net line out in the pool: the empty half of every river-side
# frame needed something at a middle distance between the dock and the far bank.
stakes = []
sx0, sy0 = 44.2, 36.6
for k in range(9):
    px = sx0 + k * 1.55
    py = sy0 + 1.05 * math.sin(k * 0.7)
    zb = BED - 0.2
    zt = WATER + 1.05 + 0.16 * math.sin(k * 1.3)
    stakes.append(cyl("sk", (px, py, zb), (px + 0.06, py + 0.05, zt), 0.085, 7, MWET, COLL))
    if k:
        qx = sx0 + (k - 1) * 1.55
        qy = sy0 + 1.05 * math.sin((k - 1) * 0.7)
        zq = WATER + 1.05 + 0.16 * math.sin((k - 1) * 1.3)
        for q in range(3):
            f0, f1 = q / 3.0, (q + 1) / 3.0
            sag = 0.20 * math.sin(math.pi * (f0 + f1) / 2)
            stakes.append(cyl("nl", (qx + (px - qx) * f0, qy + (py - qy) * f0,
                                     zq + (zt - zq) * f0 - sag),
                              (qx + (px - qx) * f1, qy + (py - qy) * f1,
                               zq + (zt - zq) * f1 - sag), 0.018, 5, MROPE, COLL))
join_meshes(stakes, "wf_stakenet", COLL)
join_meshes(painters, "wf_moorings", COLL)
log("BUILD", "wf_skiff_dock / wf_skiff_walk / wf_moorings",
    "two clinker skiffs alongside, each on a painter to its own bollard")


# ===========================================================================
# 9. CLUTTER — barrels, crates, coils, nets.  Never in a walking line.
# ===========================================================================
def surface(x, y):
    """The highest thing a prop can stand on here: staging, deck or ground."""
    best = ground_z(x, y)
    for nm in ("wf_stage_fish", "wf_stage_strand", "wf_stage_winch", "wf_stage_landing"):
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        b = world_bbox(o)
        if b[0] - 0.05 <= x <= b[1] + 0.05 and b[2] - 0.05 <= y <= b[3] + 0.05:
            best = max(best, b[5])
    return best


def slope(x, y):
    d = 0.45
    return max(abs(surface(x + d, y) - surface(x - d, y)),
               abs(surface(x, y + d) - surface(x, y - d))) / (2 * d)


def free(x, y, z, r=0.45):
    for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r)):
        if KEEP.blocked((x + dx, y + dy, z)):
            return False
        t = KEEP.top_at(x + dx, y + dy)
        if t is not None and z > t - 0.35:
            return False
    # a barrel does not stand on a 40-degree bank; it rolls into the river.
    return slope(x, y) < 0.34


ZONES = [
    (45.3, 50.5, 22.3, 23.3),      # the plank bench on the strand
    (31.7, 34.4, 21.1, 22.9),      # the winch landing
    (55.5, 62.9, 32.2, 34.9),      # the fish platform
    (41.5, 44.8, 22.2, 23.9),      # the strand west of the stairs
    (51.0, 60.0, 21.6, 23.4),      # ... and east of them
    (57.4, 61.4, 35.2, 36.8),      # the skiff stage
]
clutter = []
placed = 0
for i in range(130):
    zx0, zx1, zy0, zy1 = ZONES[i % len(ZONES)]
    for _try in range(24):
        px = zx0 + rng.random() * (zx1 - zx0)
        py = zy0 + rng.random() * (zy1 - zy0)
        pz = surface(px, py)
        if pz < WATER + 0.05:
            continue
        if not free(px, py, pz):
            continue
        break
    else:
        continue
    kind = rng.random()
    rz = rng.random() * 6.28
    if kind < 0.30:
        clutter.append(cyl("bl", (px, py, pz), (px, py, pz + 0.86), 0.30, 12, MDARKWOOD,
                           COLL + "_PROPS", r2=0.27))
        for zz in (0.18, 0.60):
            clutter.append(cyl("bd", (px, py, pz + zz), (px, py, pz + zz + 0.055), 0.315, 12,
                               MIRON, COLL + "_PROPS"))
    elif kind < 0.58:
        s = 0.58 + rng.random() * 0.24
        clutter.append(obox("cr", px, py, pz + s / 2, s, s * 0.92, s, rz=rz, mat=MDARKWOOD,
                            cname=COLL + "_PROPS"))
        clutter.append(obox("cb", px, py, pz + s / 2, s * 1.03, s * 0.055, s * 1.03, rz=rz,
                            mat=MT, cname=COLL + "_PROPS"))
    elif kind < 0.76:
        for k in range(5):
            rr = 0.30 - k * 0.045
            clutter.append(cyl("rc", (px, py, pz + 0.03 + k * 0.055),
                               (px, py, pz + 0.075 + k * 0.055), rr, 12, MROPE,
                               COLL + "_PROPS"))
    elif kind < 0.90:
        for k in range(11):
            a = rng.random() * 6.28
            rr = rng.random() ** 0.6 * 0.52
            rad = 0.30 - 0.20 * (rr / 0.52)
            clutter.append(cyl("np", (px + math.cos(a) * rr, py + math.sin(a) * rr, pz + 0.01),
                               (px + math.cos(a) * rr * 1.06, py + math.sin(a) * rr * 1.06,
                                pz + 0.11 + rng.random() * 0.13),
                               rad, 8, MNET, COLL + "_PROPS", r2=rad * 0.55))
    else:
        clutter.append(cyl("bk", (px, py, pz), (px, py, pz + 0.34), 0.17, 10, MTD,
                           COLL + "_PROPS", r2=0.21))
    placed += 1
join_meshes(clutter, "wf_clutter", COLL + "_PROPS")
log("BUILD", "wf_clutter", "%d barrels / crates / coils / net heaps, every one Corridor-tested "
    "clear of the walking lines" % placed)


# ===========================================================================
# 10. LANTERNS at dusk
# ===========================================================================
def lantern(name, x, y, z, bracket_to=None):
    parts = []
    for s in (-1, 1):
        parts.append(obox("cg", x, y, z, 0.028, 0.028, 0.34, mat=MIRON, cname=COLL))
    parts.append(obox("gl", x, y, z, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL))
    parts.append(obox("cp", x, y, z + 0.17, 0.20, 0.20, 0.055, mat=MIRON, cname=COLL))
    parts.append(obox("bs", x, y, z - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL))
    ob = join_meshes(parts, name, COLL)
    li = bpy.data.lights.new(name + "_light", 'POINT')
    li.energy = 680.0
    li.color = (1.0, 0.58, 0.24)
    li.shadow_soft_size = 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    li.shadow_maximum_resolution = 0.01
    lo = bpy.data.objects.new(name + "_light", li)
    lo.location = (x, y, z + 0.02)
    link(lo, COLL)
    return ob


brackets = []
LANT = []
# along the boardwalk: on the rail posts, river side, roughly every 8 m
for lx in (42.6, 49.4, 56.2):
    e = outer_edge(lx, 24.0, 30.8, out=0.26)
    if e is None:
        continue
    lx, ly, zt = e
    # the bracket reaches back OVER the walk, so its underside has to clear the
    # 2.0 m headroom the gate measures from the deck.
    brackets.append(beam("br", (lx, ly, zt + 2.42), (lx, ly - 0.52, zt + 2.52), 0.06, 0.06,
                         MIRON, COLL))
    LANT.append(("wf_lantern_walk_%d" % len(LANT), lx, ly - 0.52, zt + 2.30))
# the stair mouth: the tell-tale that marks the discreet route
zd = COR0.top_at(43.0, 26.0) or 1.0
_gy = None
for _o in bpy.data.objects:
    if _o.name == "wf_stairmouth":
        _b = world_bbox(_o)
        _gy = _b[3] - 0.30
LANT.append(("wf_lantern_stairmouth", 43.02, _gy if _gy else 26.46, zd + 2.72))
brackets.append(cyl("bh", (43.02, LANT[-1][2], zd + 3.02), (43.02, LANT[-1][2], zd + 2.88),
                    0.022, 5, MIRON, COLL))
# the fish dock: two over the working platform
for i, (lx, ly) in enumerate(((57.0, 32.35), (61.6, 32.35))):
    brackets.append(obox("bp", lx, ly, 1.14 + 1.30, 0.10, 0.10, 2.60, mat=MT, cname=COLL))
    brackets.append(beam("br", (lx, ly, 1.14 + 2.50), (lx, ly + 0.42, 1.14 + 2.56), 0.055,
                         0.055, MIRON, COLL))
    LANT.append(("wf_lantern_dock_%d" % i, lx, ly + 0.42, 1.14 + 2.32))
# the winch landing
brackets.append(obox("bp", 34.40, 21.20, 1.32 + 1.20, 0.10, 0.10, 2.40, mat=MT, cname=COLL))
brackets.append(beam("br", (34.40, 21.20, 1.32 + 2.30), (34.40, 21.62, 1.32 + 2.36), 0.055,
                     0.055, MIRON, COLL))
LANT.append(("wf_lantern_winch", 34.40, 21.62, 1.32 + 2.12))

for nm, lx, ly, lz in LANT:
    lantern(nm, lx, ly, lz)
join_meshes(brackets, "wf_lantern_brackets", COLL)
log("BUILD", "wf_lantern_* x%d" % len(LANT),
    "3 on the boardwalk rail, 1 at the stairs' mouth, 2 over the fish platform, "
    "1 at the winch — each with a 14 m-cutoff practical")


# ===========================================================================
# 11. VEGETATION on the new cliff
# ===========================================================================
def clone_veg(src_name, tag, n, xr, zr, scale_lo, scale_hi, mode="face"):
    src = bpy.data.objects.get(src_name)
    if src is None:
        return 0
    made = 0
    for i in range(n):
        px = xr[0] + rng.random() * (xr[1] - xr[0])
        s = scale_lo + rng.random() * (scale_hi - scale_lo)
        if mode == "face":
            pz = zr[0] + rng.random() * (zr[1] - zr[0])
            # walk north until the cliff face is at this height
            py = 12.6
            while py < 26.0 and wf_h(px, py) > pz:
                py += 0.06
            py -= 0.12
            if py < 12.7 or py > 25.4:
                continue
        else:
            py = toe(px) - 0.3 - rng.random() * 1.6
            pz = ground_z(px, py)
            if pz < WATER + 0.10:
                continue
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "veg_wf_%s_%d" % (tag, i)
        ob.data.name = ob.name
        b = world_bbox(src)
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        # a creeper is MODELLED hanging off a north-facing rock face, which is
        # exactly the face here; spinning it about Z turns the leaf cards edge-on
        # and the whole thing reads as a bundle of bare sticks.
        rot = 0.0 if tag == "creeper" else rng.random() * 6.28
        c, sn = math.cos(rot), math.sin(rot)
        for v in ob.data.vertices:
            p = src.matrix_basis @ v.co
            sz = s * (0.66 if tag == "creeper" else 1.0)
            q = Vector(((p.x - cx) * s, (p.y - cy) * s, (p.z - cz) * sz))
            v.co = Vector((q.x * c - q.y * sn, q.x * sn + q.y * c, q.z))
        ob.matrix_basis.identity()
        bb = world_bbox(ob)
        if mode == "face":
            ob.location = Vector((px, py + 0.35, pz - bb[5] + (bb[5] - bb[4]) * 0.12))
        else:
            ob.location = Vector((px, py, pz - bb[4] + 0.02))
        ob.hide_render = False
        ob.hide_viewport = False
        link(ob, COLL + "_VEG")
        made += 1
    return made


nc = clone_veg("v10_src_creeper_a", "creeper", 46, (40.6, 65.0), (2.4, 9.6), 0.8, 1.5)
if nc == 0:
    nc = clone_veg("veg_creeper_0", "creeper", 46, (40.6, 65.0), (2.4, 9.6), 0.8, 1.5)
ng = clone_veg("v10_src_tuft_grass", "tuft", 66, (40.4, 65.5), (0, 0), 0.9, 1.7, mode="toe")
if ng == 0:
    ng = clone_veg("veg_tuft_0", "tuft", 66, (40.4, 65.5), (0, 0), 0.9, 1.7, mode="toe")
nf = clone_veg("v10_src_tuft_fern", "fern", 40, (40.6, 65.0), (0, 0), 0.9, 1.6, mode="toe")
if nf == 0:
    nf = clone_veg("veg_tuft_1", "fern", 40, (40.6, 65.0), (0, 0), 0.9, 1.6, mode="toe")
nk = clone_veg("v10_src_clump_a", "rimclump", 22, (41.0, 65.0), (10.4, 14.2), 1.0, 1.8)
if nk == 0:
    nk = clone_veg("veg_rimclump_0", "rimclump", 22, (41.0, 65.0), (10.4, 14.2), 1.0, 1.8)
log("BUILD", "veg_wf_creeper/tuft/fern/rimclump",
    "%d creepers down the new cliff, %d grass + %d ferns along the strand, %d canopy "
    "clumps on its shoulder" % (nc, ng, nf, nk))


# ===========================================================================
# 12. HIDE the blockout ribbons the district now covers  (manifest 51)
# ===========================================================================
# ---- real guards on the stairs, laid exactly where the blockout rails are --
def guard_from_bar(ob, parts):
    """Post-and-rope handline following a blockout `bar_` rail's own line.

    The generated rails are the map's statement of WHERE a guard belongs, so
    the district's real one is built from them rather than re-derived: same
    line, same ends, but posts, a timber cap and a rope instead of a slab.
    """
    # A rail on a flight is a SLOPED box: its lowest vertices are the four at
    # one end, so "the two most distant low verts" measures the section, not the
    # run (0.06 m).  Take the most distant pair in XY over all verts and split
    # the vertices into the two end groups.
    P = [ob.matrix_basis @ v.co for v in ob.data.vertices]
    best = (0.0, 0, 0)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = Vector((P[i].x - P[j].x, P[i].y - P[j].y, 0.0)).length
            if d > best[0]:
                best = (d, i, j)
    L, i0, j0 = best
    if L < 0.35:
        return 0
    ax = Vector((P[j0].x - P[i0].x, P[j0].y - P[i0].y, 0.0)).normalized()
    ts = [(p.x - P[i0].x) * ax.x + (p.y - P[i0].y) * ax.y for p in P]
    mid = (min(ts) + max(ts)) / 2
    g0 = [P[k] for k in range(len(P)) if ts[k] < mid]
    g1 = [P[k] for k in range(len(P)) if ts[k] >= mid]
    if not g0 or not g1:
        return 0
    a = sum(g0, Vector()) / len(g0)
    b = sum(g1, Vector()) / len(g1)
    a = Vector((a.x, a.y, min(p.z for p in g0)))
    b = Vector((b.x, b.y, min(p.z for p in g1)))
    L = (b - a).length
    n = max(2, int(round(L / 1.15)))
    pts = [a.lerp(b, k / n) for k in range(n + 1)]
    H = 0.86
    for p in pts:
        if over_walk(p.x, p.y, p.z + H / 2, pad=0.12):
            continue
        parts.append(obox("sp", p.x, p.y, p.z + H / 2 - 0.10, 0.095, 0.095, H + 0.20,
                          rz=rng.random() * 0.15, mat=MT, cname=COLL + "_DECK"))
    for k in range(n):
        p, q = pts[k], pts[k + 1]
        if over_walk(p.x, p.y, p.z + H, pad=0.12) or over_walk(q.x, q.y, q.z + H, pad=0.12):
            continue
        parts.append(beam("sr", (p.x, p.y, p.z + H), (q.x, q.y, q.z + H), 0.075, 0.075,
                          MT, COLL + "_DECK"))
        # a rope run below the cap: this is the discreet route, not a promenade
        for t in range(3):
            f0, f1 = t / 3.0, (t + 1) / 3.0
            r0 = p.lerp(q, f0)
            r1 = p.lerp(q, f1)
            sg = 0.055 * math.sin(math.pi * (f0 + f1) / 2)
            if over_walk(r0.x, r0.y, r0.z + H * 0.56, pad=0.06):
                continue
            parts.append(cyl("sl", (r0.x, r0.y, r0.z + H * 0.56 - sg),
                             (r1.x, r1.y, r1.z + H * 0.56 - sg), 0.022, 5, MROPE,
                             COLL + "_DECK"))
    return 1


guards, nguard = [], 0
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("bar_"):
        continue
    bb = world_bbox(o)
    cx, cy = (bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2
    if 34.0 <= cx <= 64.0 and 18.0 <= cy <= 32.0 and bb[5] < 9.8:
        nguard += guard_from_bar(o, guards)
join_meshes(guards, "wf_stair_rail", COLL + "_DECK")
log("BUILD", "wf_stair_rail", "%d blockout rails replaced by post + cap + rope handlines "
    "on the deep stairs' own line" % nguard)


# ---- cross-bracing between the piles: the walk reads as built, from below --
br = []
PILE_POS.sort()
for i in range(len(PILE_POS) - 1):
    ax, ay, azb, azt = PILE_POS[i]
    bx, by, bzb, bzt = PILE_POS[i + 1]
    if math.hypot(ax - bx, ay - by) > 2.1:
        continue
    zl = max(azb, bzb) + 0.40
    zh = min(azt, bzt) - 0.35
    if zh - zl < 1.0:
        continue
    br.append(beam("xb", (ax, ay, zl), (bx, by, zh), 0.075, 0.075, MWET, COLL + "_DECK"))
    br.append(beam("xb", (ax, ay, zh), (bx, by, zl), 0.075, 0.075, MWET, COLL + "_DECK"))
join_meshes(br, "wf_pile_bracing", COLL + "_DECK")
log("BUILD", "wf_pile_bracing", "%d X-braces between pile bents — the boardwalk reads as "
    "BUILT from the river, which is the view half the cameras have" % (len(br) // 2))


hid = []
for nm in DECK_NAMES + STAIR_NAMES:
    o = bpy.data.objects.get(nm)
    if o and not o.hide_render:
        o.hide_render = True
        o.hide_viewport = False
        hid.append(nm)
# the blockout railings inside the detailed stretch are stand-ins too
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("bar_") and not o.hide_render:
        b = world_bbox(o)
        cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
        if 34.0 <= cx <= 64.0 and 18.0 <= cy <= 32.0 and b[5] < 9.8:
            o.hide_render = True
            hid.append(o.name)
log("HIDE_RENDER", "%d walk/bar meshes" % len(hid),
    "blockout slabs under the new decking; geometry untouched, viewport-visible so "
    "the glTF keeps the collision")

print("\n" + "=" * 78)
print("WATERFRONT BUILD: %d steps" % len(LOG))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("saved", bpy.data.filepath)
