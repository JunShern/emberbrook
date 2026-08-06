# town_blockout.py — raise a whole-town gray blockout in Blender from a townmap JSON.
# Run inside Blender (via MCP: exec(open(__file__).read()) or blender -b -P).
# Deterministic: same JSON -> same scene. WIPES the current scene.
#
# Geometry rules mirror the townmap viewer's material-aware rendering:
#   road/path   -> chaikin-smoothed flat ribbons (earth)
#   deck/bridge -> straight plank ribbons, leg per waypoint segment (timber)
#   stairs      -> real treads (rise <= 0.4/tread) + a landing across each pivot
#                  (v2, see STAIRS_V2: the two flights at a switchback are offset
#                   apart so a body can walk DOWN without being picked back up)
#   ladder      -> steep rail + rungs
#   winch       -> thin cable (non-walkable)
# Landmarks by class: structure (kind-shaped massing), area (flat disc, extent),
# prop (small block), portal (posts + lintel), dressing (dark simplified block).

import bpy, json, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")

TOWN_JSON = "/Users/junshernchan/projects/multiplayer-rpg/public/townmap/dellhollow.map.json"
BLEND_OUT = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends/dellhollow-town.blend"

D = json.load(open(TOWN_JSON))

# ---------- scene reset ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

for n in ("CONTEXT", "PATHS", "LANDMARKS", "CAMS"):
    coll(n)

def mat(name, rgba):
    m = bpy.data.materials.get(name)
    if not m:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = rgba
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    return m

M_ROCK  = mat("m_rock",  (0.32, 0.30, 0.28, 1))
M_WATER = mat("m_water", (0.18, 0.38, 0.42, 1))
M_DAM   = mat("m_dam",   (0.10, 0.10, 0.12, 1))   # black stone, per ref 6b
M_FOAM  = mat("m_foam",  (0.85, 0.90, 0.92, 1))
M_GRAY  = mat("m_gray",  (0.55, 0.52, 0.48, 1))
M_WOOD  = mat("m_wood",  (0.45, 0.36, 0.26, 1))
M_STAIR = mat("m_stair", (0.52, 0.40, 0.26, 1))
M_PORT  = mat("m_port",  (0.75, 0.62, 0.35, 1))
M_DRESS = mat("m_dress", (0.25, 0.24, 0.23, 1))

def link_to(o, c):
    for uc in o.users_collection: uc.objects.unlink(o)
    coll(c).objects.link(o)

def box(name, loc, dims, m, c="LANDMARKS", rot=None, rz=0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object; o.name = name
    o.dimensions = dims
    if rot: o.rotation_euler = rot
    elif rz: o.rotation_euler = (0, 0, rz)
    o.data.materials.append(m)
    link_to(o, c)
    return o

def gable(name, loc, w, d, h, m):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w * 0.75, depth=h, location=loc)
    o = bpy.context.active_object; o.name = name
    o.scale.y = d / (w * 1.5) if w else 1
    o.rotation_euler = (0, 0, math.radians(45))
    o.data.materials.append(m)
    link_to(o, "LANDMARKS")
    return o

# ---------- gorge context ----------
# gorge + staircase-of-water built from the map's river spec (single source of truth)
RV = D.get("river", {})
G = RV.get("gorge", {"nearWallY": 0, "farWallY": 58})
CY = RV.get("centerY", 34); RW = RV.get("width", 16)
box("cliff_town", (50, G["nearWallY"] - 3, 14), (170, 6, 46), M_ROCK, "CONTEXT")
box("cliff_far",  (50, G["farWallY"] + 4, 16), (170, 8, 52), M_ROCK, "CONTEXT")
for pool in RV.get("pools", []):
    cx = (pool["from"] + pool["to"]) / 2
    box("water_" + pool["id"], (cx, CY, pool["level"] - 0.2),
        (pool["to"] - pool["from"], RW, 0.4), M_WATER, "CONTEXT")
for dam in RV.get("dams", []):
    dx = dam["x"]; drop = dam.get("drop", 2)
    up = next((pl["level"] for pl in RV["pools"] if abs(pl["to"] - dx) < 1), 2)
    lo = up - drop
    # black stone dam wall spanning the river, crest just above upstream level
    box("dam_%s_wall" % dam["id"], (dx, CY, (lo - 1.5 + up + 0.6) / 2),
        (3.0, RW + 2, (up + 0.6) - (lo - 1.5)), M_DAM, "CONTEXT")
    box("dam_%s_crest" % dam["id"], (dx, CY, up + 0.75), (2.2, RW + 2, 0.3), M_DAM, "CONTEXT")
    box("dam_%s_foam" % dam["id"], (dx + 2.6, CY, lo + 0.1), (2.4, RW - 2, 0.5), M_FOAM, "CONTEXT")
    for wi in range(dam.get("waterwheels", 0)):        # wheels on the downstream face (ref 6b)
        wy = CY - RW / 2 + (wi + 1) * RW / (dam["waterwheels"] + 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=2.2, depth=0.8,
            location=(dx + 2.1, wy, lo + 1.6), rotation=(0, math.radians(90), 0))
        o = bpy.context.active_object; o.name = "dam_%s_wheel%d" % (dam["id"], wi)
        o.data.materials.append(M_WOOD); link_to(o, "CONTEXT")

sun = bpy.data.lights.new("sun", 'SUN'); sun.energy = 3.2; sun.color = (1.0, 0.82, 0.6)
so = bpy.data.objects.new("sun", sun); so.rotation_euler = (0.9, 0.15, 2.2)
coll("CONTEXT").objects.link(so)
w = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.28, 0.22, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

# ---------- landmarks ----------
for lm in D["landmarks"]:
    x, y, z = lm["pos"]; i = lm["id"]
    cls = lm.get("class", "structure"); kind = lm.get("kind", "")
    if cls == "area":
        # FOOTPRINT OVERRIDES EXTENT (map _doc_landmark_footprint, coordinator ruling
        # 2026-08-01). `extent` becomes a filled DISC, and at the waterfront that disc is
        # parked on the river: walk_water_audit measured the town's four worst
        # walk-on-water records as exactly the four `area` pads. A landmark that states a
        # `footprint` — a LIST of measured-landed [x0, x1, y0, y1] rects in map
        # coordinates — gets the union of those rects instead, joined into ONE walk record
        # under the same name, because the record name is the ownership contract every
        # camera, seam and audit resolves by. `extent` stays the fallback, so every
        # landmark that states no footprint derives exactly as it did before.
        fp = lm.get("footprint")
        if isinstance(fp, list) and fp and isinstance(fp[0], (list, tuple)):
            parts = []
            for k, (x0, x1, y0, y1) in enumerate(fp):
                bpy.ops.mesh.primitive_cube_add(size=1,
                    location=((x0 + x1) / 2, (y0 + y1) / 2, z + 0.12))
                q = bpy.context.active_object
                q.scale = (abs(x1 - x0), abs(y1 - y0), 0.25)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                q.name = "walk_lm_%s_r%d" % (i, k)
                parts.append(q)
            o = parts[0]
            if len(parts) > 1:
                bpy.ops.object.select_all(action='DESELECT')
                for q in parts:
                    q.select_set(True)
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.join()
            o.name = "walk_lm_" + i
        else:
            r = lm.get("extent", 3)
            bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.25,
                                                location=(x, y, z + 0.12))
            o = bpy.context.active_object
            o.name = "walk_lm_" + i
        o.data.materials.append(M_WOOD); link_to(o, "LANDMARKS")
    elif cls == "portal":
        box("lm_%s_postL" % i, (x - 1.1, y, z + 1.4), (0.5, 0.5, 2.8), M_PORT)
        box("lm_%s_postR" % i, (x + 1.1, y, z + 1.4), (0.5, 0.5, 2.8), M_PORT)
        box("lm_%s_lintel" % i, (x, y, z + 2.9), (3.0, 0.6, 0.5), M_PORT)
    elif cls == "prop":
        box("lm_" + i, (x, y, z + 0.5), (0.8, 0.8, 1.0), M_GRAY)
    elif cls == "dressing":
        box("lm_" + i, (x, y, z + 1.0), (6, 3, 2.0), M_DRESS)
    else:  # structure
        if kind == "lock":
            box("lm_%s_wallS" % i, (x, y - 2.6, z + 1.2), (7, 1.6, 2.4), M_GRAY)
            box("lm_%s_wallN" % i, (x, y + 2.6, z + 1.2), (7, 1.6, 2.4), M_GRAY)
            box("lm_%s_gateA" % i, (x - 3.2, y, z + 1.0), (0.7, 3.8, 2.0), M_WOOD)
            box("lm_%s_gateB" % i, (x + 3.2, y, z + 1.0), (0.7, 3.8, 2.0), M_WOOD)
        elif kind == "machine":
            box("lm_%s_base" % i, (x, y, z + 0.9), (1.6, 1.6, 1.8), M_GRAY)
            box("lm_%s_arm" % i, (x, y + 1.4, z + 2.1), (0.4, 3.2, 0.4), M_WOOD)
        elif kind == "building-cluster":
            for j, (dx, dy, rz) in enumerate(((-2.2, -1.2, 0.2), (1.8, 0.8, -0.3), (0.2, 2.4, 0.1))):
                box("lm_%s_%d" % (i, j), (x + dx, y + dy, z + 1.4), (3.4, 3.0, 2.8), M_WOOD, rz=rz)
                gable("lm_%s_%d_roof" % (i, j), (x + dx, y + dy, z + 3.4), 3.4, 3.0, 1.3, M_GRAY)
        else:
            big = kind.startswith("shop") or kind == "building"
            bw, bd, bh = (4.2, 3.6, 3.2) if big else (3.2, 3.0, 2.6)
            box("lm_%s_body" % i, (x, y, z + bh / 2), (bw, bd, bh), M_WOOD)
            gable("lm_%s_roof" % i, (x, y, z + bh + 0.65), bw, bd, 1.4, M_GRAY)

# threshold pads: a walkable landing at every structure/prop/portal position.
# Paths terminate AT landmark centers, so without a pad two abutting ribbons
# meet at a zero-width point (unwalkable pinch at shop doors). Also: somewhere
# to stand when talking/entering.
for lm in D["landmarks"]:
    if lm.get("class", "structure") in ("structure", "prop", "portal"):
        x, y, z = lm["pos"]
        box("walk_pad_" + lm["id"], (x, y, z - 0.02), (2.6, 2.6, 0.12), M_WOOD, "PATHS")

# ---------- paths ----------
LM = {l["id"]: Vector(l["pos"]) for l in D["landmarks"]}

def leg_box(name, a, b, wdt, hgt, m):
    mid = (a + b) / 2; v = b - a; L = v.length
    if L < 1e-6: return
    bpy.ops.mesh.primitive_cube_add(location=mid)
    o = bpy.context.active_object; o.name = name
    o.dimensions = (L, wdt, hgt)
    o.rotation_euler = v.to_track_quat('X', 'Z').to_euler()
    o.data.materials.append(m)
    link_to(o, "PATHS")

def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out += [p * 0.75 + q * 0.25, p * 0.25 + q * 0.75]
        out.append(pts[-1]); pts = out
    return pts

# ---------- stairs v2: a switchback whose flights do not stack ----------------
# THE TWO FLIGHTS AT A PIVOT MUST NOT SHARE GROUND.  play3d's walkGround takes the
# HIGHEST top within [fy-(STEP_DN+.1), fy+(STEP_UP+.1)], and a switchback laid about
# a SINGLE waypoint puts the arriving flight's TAIL and the departing flight's HEAD
# on the same plan cells one riser apart — so a body walking DOWN is picked back UP,
# rung by rung, and the stair cannot be descended at all.  Measured in del-cine, on
# the deep stairs, `_court_probe --way` tread by tread: the drive climbs the ladder
# 10.49 -> 10.80 (landing) -> 11.27 (l0_t07) -> 11.67 (l0_t06) and ends at
# [39.25, 11.67, -19.85], which is where round 20's receipt run ended.
#
# AND A FLOOD FILL CANNOT SEE IT: the fill's lattice adjacency allows a step UP, so
# it reports the shipped deep stairs as ONE component of 1663 cells while no body can
# get down them.  Only the drive says so — CLAUDE.md's own line, earned again.
#
# So each interior waypoint is SPLIT: the arriving leg ends off to one side, the
# departing leg starts off to the other, and the landing bridges the two feet.  That
# is what a real switchback is — two flights side by side across one landing.
# Three numbers, all swept offline against play3d's own walkGround/blocked rules
# (17 landings x ~200 body-box cells, plus a 0.075 m drive of every flight):
PIVOT_OFF  = 1.20   # half the lateral separation at a 150-degrees-or-sharper turn
PIVOT_KNEE = 80.0   # a turn gentler than this already misses itself — no offset
PIVOT_SPAN = 70.0   # degrees of turn over which the offset ramps to PIVOT_OFF
FOOT_TRIM  = 0.25   # plan-only setback of a leg's LOWER end off its own landing
LAND_LONG  = 0.90   # landing depth ALONG the flights (a deeper one gets roofed)
LAND_CROSS = 1.40   # landing width ADDED to the pivot's own separation
RAIL_INS   = 1.05   # rail setback at a SPLIT end (LAND_LONG/2 + a body's half-width)
#
# THE SPLIT IS ASYMMETRIC, and that is the second thing a rebuild had to teach me.
# Moving BOTH ends off the waypoint swings the ARRIVING leg's whole line, and the
# flight's first leg cannot afford it: `walk_e_quay-deck__deep-stairs-head_l2`, the
# flat ribbon that feeds the deep stairs, lies at 14.07 ON TOP OF the first six
# treads (the approach comes in from the east and the stair doubles straight back
# under it), and the only way down is a 0.05 m sliver of tread sticking out past the
# ribbon's south edge.  Swing the leg 0.2 m north and that sliver is gone: measured
# `--comp` from the head pad, 0 cells past z -18.3, and the drive parked on the
# ribbon's lip at [39.61, 14.07, -18.52].  So the arriving leg KEEPS the waypoint and
# the departing leg takes the whole 2 x PIVOT_OFF.  Same separation, one line moved.
# FOOT_TRIM is bounded by that same sliver: 0.25 drives the descent 40/40, 0.34 does
# not.  The margin is the map's, not the parameter's.  And GROWING THE LANDING to keep
# up with a bigger trim is not the way out — tried at 0.45, every landing read 99-100%
# standable and the drive lost the last pivot at 13/40: clean AND disconnected.
#
# STAIRS_V2 IS A MIGRATION LEDGER, NOT A TASTE.  Six of Dellhollow's seven flights
# have DISTRICT ART derived from their walk records at build time — gs_build
# (valley-gate__inn), ls_build (shelf-homes__market-stalls, loop-landing__quay-deck),
# lg_build (keepers-cottage__lock-five), cx_build + locksfoot_build
# (weave-huts__moorage), qm_build (quay-deck__pilot-cluster) — so moving a ribbon
# without re-running its builder in the SAME window leaves rails and treads
# registered to a stair that is no longer there.  An edge joins this set only when
# its district art is carried with it.  The deep stairs are here first because ONE
# builder owns theirs — `waterfront_build.py`, which clears its own `wf_`/`veg_wf_`
# prefix and rebuilds deterministically, so re-running it is safe.
# AND A SEARCH BY NODE ORIGIN CANNOT FIND THAT ART: `wf_stair_treads` is a JOINED
# mesh whose origin is nowhere near the stair, so "93 nodes in the stairs' box, all
# scatter" was a wrong answer confidently obtained.  Ask for WORLD BOUNDING BOXES.
# When the set covers every stairs edge, delete it and the `if` below with it.
STAIRS_V2 = {"deep-stairs-head__deep-stairs-foot",
             # 2026-08-06, BET 2 (user-ratified): THE ONE DESCENT — the gate->shelf
             # flight rebuilt as a single straight 2.2 u-wide run, no waypoints, no
             # pivots (the S-bend and the 'gate-stair' passage both deleted; see the
             # map edge's _superseded_S_bend_2026-08-06). In the set for the rail
             # discipline (a rail may not stand in a body window of its own edge),
             # not for pivot splitting — a straight flight has nothing to split.
             # District art: gs_build (gs_) owns it; shelf_build's
             # shelf_stair_underworks carries it — both re-run in the same window.
             "valley-gate__inn",
             # 2026-08-06, BET 2 iteration 2 (pain inventory defects #1/#6): the quay
             # interchange. The market flight was v1 (its l2 rails penned the
             # lockhead-return spawn pocket); width 2.0 from the map, ls_build re-run
             # in the same window. The QUAY BRANCH (loop-landing__quay-deck) and its
             # fork landmark are DELETED outright, not migrated: the fork stood 5.59 u
             # from the plaza centre against an extent-5.5 disc, so the stairs trim
             # could never start the flight outside the plaza's own floor and the whole
             # branch overlaid it — unfixable by v2, redundant beside the flat
             # quay-deck__market-stalls hop. See the market edge's _bet2_2026-08-06b.
             "shelf-homes__market-stalls",
             # ...and the shops->weave connector (inventory #7): v1, measured failing
             # both ways, one 0.92 m leg, its head railA on the deck floor (7 cells).
             # Art: qm_build re-run in the same window.
             "quay-deck__pilot-cluster",
             # 2026-08-05, PT-20260805-049: the moorage switchback's un-split hairpins
             # stack l1 over l2 (and l0 over l1) inside the body window — UP stalled
             # under walk_e_weave-huts__moorage_l1_t04 (bottom 4.00 over t01's 3.03)
             # and DOWN was picked back up at the top hairpin, measured with
             # _court_probe --way in the running game. Joined WITH its art: weave_build
             # (wv_, owns l0/l1's decking) + locksfoot_build (lf_) + cx_build (cx_)
             # re-run in the same window, per the ledger rule above.
             "weave-huts__moorage"}


def pivot_split(prev, w, nxt, asym=False, width=1.4):
    """(arriving-leg END, departing-leg START) at an interior stairs waypoint.

    THE SPLIT IS ASYMMETRIC: the departing leg takes the WHOLE separation and the
    arriving leg's line is left alone.  A balanced split swings the arriving leg too,
    and the first leg cannot afford it (see the ribbon note above) — but it was also
    tried EVERYWHERE ELSE, where it is free of that constraint, and it was worse:
    balanced at pivots 2..4 drove 36/40 where asymmetric drove 40/40.  One line moved
    per pivot is both the safer rule and the measured one.

    THE SEPARATION SCALES WITH TREAD WIDTH (BET 2 iteration 6, measured).  PIVOT_OFF's
    1.20 was swept at width 1.4: separation 2.4 leaves 1.0 m between the two flights'
    tread EDGES at the split ends.  At width 2.0 the same 2.4 leaves 0.4 m — less than
    a body — and the searched pilot-cluster hairpin duly stacked: `--who` named l1_t06
    ON l2_t01's walking line at dy 1.20 (inside the body window) and the up-drive
    stalled under the overhang at [59.95, 9.47, -24.05].  max(1, width/1.4) keeps every
    1.4-wide flight (deep stairs, moorage — both receipt-green) bit-identical and gives
    a wide flight the same 1.0 m edge clearance the sweep validated."""
    a = Vector((w.x - prev.x, w.y - prev.y, 0))
    d = Vector((nxt.x - w.x, nxt.y - w.y, 0))
    if a.length < 1e-6 or d.length < 1e-6: return w, w
    a.normalize(); d.normalize()
    th = math.degrees(math.acos(max(-1.0, min(1.0, a.dot(d)))))
    off = PIVOT_OFF * max(1.0, width / 1.4) * max(0.0, min(1.0, (th - PIVOT_KNEE) / PIVOT_SPAN))
    if off < 1e-3: return w, w
    s = -a                                  # back along the arriving flight
    m = (s + d)                             # both flights lie roughly along m
    if m.length < 1e-6: return w, w
    m.normalize()
    n = s - m * s.dot(m)                    # the side the arriving flight leans to
    if n.length < 1e-6: return w, w
    n.normalize()
    if asym: return w, w - n * (2 * off)
    return w + n * off, w - n * off


def lay_stair_rails(nm, railq):
    """A RAIL MAY NOT STAND IN A BODY WINDOW OF ITS OWN EDGE (PT-20260805-049).

    The pivot split moves sibling legs SIDEWAYS, so a leg's own 1.25 m side rail can
    now stand over ANOTHER leg's corridor (bar_..._l1_railA stood over the relocated
    l2's treads) or across a landing that the split laid beside the leg rather than
    on its end (bar_..._l1_railB crossed the upper landing at head height).  The
    invisible-wall sweep in walk_rederive is blind to both BY DESIGN — it sweeps a
    rebuilt bar_ against OTHER edges' ribbons only.  So the rails of a v2 flight are
    laid LAST, when every tread and landing of the edge exists, and each run is
    marched at 0.15 m: a sample is cut where the rail slab would enter
    [top+0.60, top+1.30] over any of this edge's own walk records under it (grown
    0.35 m for the body box).  Kept sub-runs shorter than 0.5 m are dropped — a
    post-length stub guards nothing.  The FIRST kept run inherits the bar's own
    name so district builders (cx_build reads the six blockouts BY NAME) still find
    it; later runs get _s<k>."""
    # 2026-08-06 (BET 2 iteration 2, measured): the clip set is the edge's OWN records
    # PLUS every LANDMARK floor (walk_lm_* / walk_pad_*).  A flight that terminates on
    # an `area` disc runs its side rails onto that disc's own floor — the quay branch's
    # railA/railB stood on walk_lm_quay-deck fencing the promenade, and `--who` named
    # them on 19 cells with the promenade crossing stalled from BOTH sides.  Landmark
    # pads are built BEFORE the edge loop, so clipping against them is order-safe;
    # OTHER EDGES' ribbons are deliberately not read here (edge build order is map
    # order) — crossings against those remain walk_rederive's sweep's job.
    walks = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o.name.startswith("walk_" + nm) or
                                 o.name.startswith(("walk_lm_", "walk_pad_"))):
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            walks.append((min(p.x for p in bb) - 0.35, max(p.x for p in bb) + 0.35,
                          min(p.y for p in bb) - 0.35, max(p.y for p in bb) + 0.35,
                          max(p.z for p in bb)))
    for name, ra, rb in railq:
        L = (rb - ra).length
        if L < 1e-6:
            continue
        n = max(2, int(L / 0.15))
        keep = []
        for k in range(n + 1):
            p = ra.lerp(rb, k / n)
            z0, z1 = p.z - 0.45, p.z + 0.45          # the slab about the rail line
            cut = False
            for x0, x1, y0, y1, top in walks:
                if x0 <= p.x <= x1 and y0 <= p.y <= y1 and z1 > top + 0.60 and z0 < top + 1.30:
                    cut = True; break
            keep.append(not cut)
        runs, s = [], None
        for k in range(n + 1):
            if keep[k] and s is None: s = k
            if (not keep[k] or k == n) and s is not None:
                e = k if keep[k] else k - 1
                if (e - s) * (L / n) >= 0.5: runs.append((s, e))
                s = None
        for j, (s0, e0) in enumerate(runs):
            leg_box(name if j == 0 else "%s_s%d" % (name, j),
                    ra.lerp(rb, s0 / n), ra.lerp(rb, e0 / n), 0.06, 0.9, M_STAIR)
        ncut = (n + 1) - sum(keep)
        if not runs:
            print("  RAIL %s: every sample inside its own edge's body window — NOT BUILT" % name)
        elif ncut:
            print("  RAIL %s: clipped %d of %d samples against own-edge walk windows -> %d run(s)"
                  % (name, ncut, n + 1, len(runs)))


def plan_trim(a, b, t):
    """pull b back toward a by t IN PLAN, keeping b's height (the riser count and
    every tread top are unchanged; only the run shortens, which walks the ladder
    out from under the landing)."""
    v = Vector((b.x - a.x, b.y - a.y, 0)); L = v.length
    if L <= t + 0.6: return b
    return b - v.normalized() * t


def stairs_leg(name, a, b, rail_ins=(0.0, 0.0), rail_out=None, width=1.4):
    """`width` (map edge key "width", default 1.4) is the TREAD width, and the rail
    offset scales WITH it — the 1.25 literal was tread half-width 0.7 + char radius
    0.42 + margin, so a wider flight keeps the same clearance rule (w/2 + 0.55).
    lay_stair_rails' own-edge sweep grows records by 0.35, so a scaled rail stays
    0.20 clear of its own treads at any width (BET 2: the gate descent ships 2.2)."""
    v = b - a; rise = b.z - a.z
    hl = Vector((v.x, v.y, 0)).length
    # side rails: stop walkers mounting flights sideways (the scoop-trap), read as
    # rickety-town railings. bar_ = collision barrier, never a floor (thin + tall).
    side = Vector((v.y, -v.x, 0))
    if side.length > 1e-6 and hl > 1.6:
        # wide enough that the walker's side-rays clear them ON the flight
        # (tread half-width + char radius 0.42 + margin), inset from both
        # ends so junctions/landings stay open
        side = side.normalized() * (width / 2 + 0.55)
        # rails guard the DROP, not the approach: begin where the flight has
        # descended 0.3 below its start (else rails fence the flat deck they
        # depart from — found blocking the quay crossing under volume physics)
        drop_frac = min(0.6, 0.3 / abs(rise)) if abs(rise) > 1e-6 else 0.0
        # AND A RAIL MUST CLEAR THE LANDING IT ENDS AT, wherever that landing IS.
        # 0.55 was enough while a landing sat ON the leg's own end; a split pivot
        # puts it OFF TO THE SIDE, straight across the rail line, and the rail then
        # fences the flight off from its own landing.  Measured: `--who` named
        # `wf_stair_rail_1` (waterfront_build's art, laid on this bar_) blocking the
        # body on l1_t08 at 7.82, and the drive stopped 0.92 m short of landing001.
        ins = max(0.55, hl * drop_frac, rail_ins[0])
        fwd_a = Vector((v.x, v.y, 0)).normalized() * ins
        fwd_b = Vector((v.x, v.y, 0)).normalized() * max(0.55, rail_ins[1])
        up = Vector((0, 0, 0.55))
        for sgn, tag in ((1, "A"), (-1, "B")):
            ra = a + side * sgn + up + fwd_a; rb = b + side * sgn + up - fwd_b
            if rail_out is not None:
                rail_out.append(("bar_%s_rail%s" % (name, tag), ra, rb))
            else:
                leg_box("bar_%s_rail%s" % (name, tag), ra, rb, 0.06, 0.9, M_STAIR)
    n = max(1, math.ceil(abs(rise) / 0.4))
    for t in range(n):
        p0 = a + v * (t / n); p1 = a + v * ((t + 1) / n)
        # A TREAD'S HEIGHT IS NOT NEGOTIABLE, and that is a measurement, not taste.
        # Round 14 prescribed laying a tread's top at its leg's own LOWER end instead
        # of its upper one (tops U-step..L rather than U..L+step), which does clear
        # every landing.  BUILT AND MEASURED, it broke the flight at BOTH ends:
        # `qm_stair_underworks` — qm_build's masonry, laid UNDER the old treads —
        # came up into the body window over l0_t05/t06, and the approach ribbon
        # `walk_e_quay-deck__deep-stairs-head_l2` (top 14.07, over the first six
        # treads) stopped being level with the flight's head and became a 0.40 m
        # lip the walker could not leave: `--comp` from the head pad filled 0 cells
        # past z -18.3.  SIX DISTRICT BUILDERS derive art from these tread tops.  So
        # v2 moves treads only IN PLAN, where the defect actually is.
        z = min(p0.z, p1.z) + abs(rise / n)
        bpy.ops.mesh.primitive_cube_add(location=((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, z))
        o = bpy.context.active_object; o.name = "walk_%s_t%02d" % (name, t)
        o.dimensions = (max(hl / n, 0.35), width, 0.14)
        o.rotation_euler = (0, 0, math.atan2(v.y, v.x))
        o.data.materials.append(M_STAIR)
        link_to(o, "PATHS")

LM_CLASS = {l["id"]: l for l in D["landmarks"]}

# ---------- bridge rails: queued, laid AFTER every ribbon exists --------------
# 2026-08-06 (BET 2 iteration 5, measured): A BRIDGE RAIL MAY NOT STAND ON ANOTHER
# WAY'S FLOOR.  The weave-huts__keepers-cottage span and the lockhead__keepers-cottage
# ramp CONVERGE on the cottage doorstep, and the bridge's rails — laid per-leg with no
# clipping — ran all the way onto walk_pad_keepers-cottage and across the ramp's foot
# corridor.  `_court_probe --who` over the ramp band named bar_..._railA2 on 35 cells
# (plus cx_rail, its dressed twin, on 8) and the down-drive stalled 0.89 m short of the
# door: pain inventory #3's P0, whose "taper" was this wall, not the ribbon.
# So bridge rails are QUEUED here and laid after the edge loop, marched at 0.15 m like
# lay_stair_rails, with two deliberate differences:
#   * the clip set is every walk_ record EXCEPT the bridge's own ribbon (a bridge rail
#     legitimately stands on its own deck's edge — clipping against itself deletes it),
#     landmark floors and pads included, other edges' ribbons included (they all exist
#     by post-pass time, so there is no build-order hole);
#   * the vertical test is the BODY VOLUME [top+0.20, top+1.50], not blocked()'s head
#     window [0.60, 1.30]: the bridge rail slab rides at [z+0.20, z+0.70], BELOW the
#     head window over a floor at its own deck height — and the engine still refuses
#     those cells (the --who receipt above).  A shin-height rail is a wall to the body.
BRIDGE_RAILQ = []   # (name, ra, rb, own_edge_nm)


def lay_bridge_rails():
    if not BRIDGE_RAILQ:
        return
    walks = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("walk_"):
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            walks.append((o.name,
                          min(p.x for p in bb) - 0.35, max(p.x for p in bb) + 0.35,
                          min(p.y for p in bb) - 0.35, max(p.y for p in bb) + 0.35,
                          max(p.z for p in bb)))
    for name, ra, rb, own in BRIDGE_RAILQ:
        own_pfx = "walk_e_%s" % own
        L = (rb - ra).length
        if L < 1e-6:
            continue
        n = max(2, int(L / 0.15))
        keep = []
        for k in range(n + 1):
            p = ra.lerp(rb, k / n)
            z0, z1 = p.z - 0.25, p.z + 0.25      # the 0.5 m slab about the rail line
            cut = False
            for wn, x0, x1, y0, y1, top in walks:
                if wn.startswith(own_pfx):
                    continue
                if x0 <= p.x <= x1 and y0 <= p.y <= y1 and z1 > top + 0.20 and z0 < top + 1.50:
                    cut = True; break
            keep.append(not cut)
        runs, s = [], None
        for k in range(n + 1):
            if keep[k] and s is None: s = k
            if (not keep[k] or k == n) and s is not None:
                e2 = k if keep[k] else k - 1
                if (e2 - s) * (L / n) >= 0.5: runs.append((s, e2))
                s = None
        for j, (s0, e0) in enumerate(runs):
            leg_box(name if j == 0 else "%s_s%d" % (name, j),
                    ra.lerp(rb, s0 / n), ra.lerp(rb, e0 / n), 0.08, 0.5, M_WOOD)
        ncut = (n + 1) - sum(keep)
        if not runs:
            print("  BRIDGE RAIL %s: every sample on another way's floor — NOT BUILT" % name)
        elif ncut:
            print("  BRIDGE RAIL %s: clipped %d of %d samples against other-way floors -> %d run(s)"
                  % (name, ncut, n + 1, len(runs)))
# landmarks where a stairs flight terminates — flat ribbons must stop short of
# these points or their tips hover over the descending treads (unwalkable lip)
STAIR_ENDS = set()
for e in D["edges"]:
    if e["type"] == "stairs":
        STAIR_ENDS.add(e["from"]); STAIR_ENDS.add(e["to"])

def trim_toward(a, b, dist):
    v = Vector((b.x - a.x, b.y - a.y, 0))
    if v.length <= dist + 0.6: return a
    return a + v.normalized() * dist

for e in D["edges"]:
    a = LM.get(e["from"]); b = LM.get(e["to"])
    if a is None or b is None:
        print("SKIP dangling edge", e["from"], e["to"]); continue
    pts = [a] + [Vector(wp) for wp in e.get("waypoints", [])] + [b]
    t = e["type"]; nm = "e_%s__%s" % (e["from"], e["to"])
    if t == "stairs":
        # flights start OUTSIDE the flat feature at their endpoint: area discs
        # (rim + margin) and threshold pads alike — otherwise the flat surface
        # bridges over the descending treads and ends in a drop
        for end, idx, nbr in ((e["from"], 0, 1), (e["to"], -1, -2)):
            lmc = LM_CLASS.get(end, {})
            if lmc.get("class") == "area":
                r = lmc.get("extent", 3) + 0.6
            elif lmc.get("class") in ("structure", "prop", "portal"):
                r = 1.0   # inside the 1.3 pad half-width: flight and pad must overlap, never gap
            else:
                continue
            centre = pts[idx].copy()
            pts[idx] = trim_toward(pts[idx], pts[nbr], r)
            # 2026-08-06 (BET 2 iteration 3, measured): AN AREA-TERMINATED FLIGHT OWES AN
            # APRON.  The disc's own floor ends at `extent`; the trim above starts the
            # flight at extent+0.6 — and NOTHING bridges the 0.6 m annulus between them
            # unless some other edge's ribbon happens to pave it.  Measured on the quay
            # flight's head (`--at`): deck floor 14.06 at [58,-17.2], flight floor 14.07
            # at [58.4,-17.6], and the two cells between them have NO floor at deck
            # height — contact was one diagonal cell, which walkStep's 0.075 m stride
            # cannot cross.  v1 never met this because its short-edge guard collapsed
            # the head to the disc CENTRE (the overlay disease iteration 2 fixed).  The
            # apron is flat, at the endpoint's own height, laid from 0.4 INSIDE the rim
            # to 0.1 past the flight's start — it stands BEFORE the first tread, so it
            # cannot roof a descending flight (the thing the trim exists to prevent).
            if lmc.get("class") == "area":
                v = Vector((pts[idx].x - centre.x, pts[idx].y - centre.y, 0))
                ext = lmc.get("extent", 3)
                if v.length > ext + 1e-6:
                    dirv = v.normalized()
                    inner = centre + dirv * (ext - 0.4)
                    outer = centre + dirv * (v.length + 0.1)
                    mid = (inner + outer) / 2
                    bpy.ops.mesh.primitive_cube_add(
                        location=(mid.x, mid.y, pts[idx].z - 0.08))
                    o = bpy.context.active_object
                    o.name = "walk_%s_apron%d" % (nm, 0 if idx == 0 else 1)
                    o.dimensions = ((outer - inner).length, float(e.get("width", 1.4)), 0.16)
                    o.rotation_euler = (0, 0, math.atan2(dirv.y, dirv.x))
                    o.data.materials.append(M_STAIR)
                    link_to(o, "PATHS")
    elif t in ("deck", "road", "path", "bridge"):
        # stop flat ribbons short of stair junction points (pad bridges the gap)
        if e["from"] in STAIR_ENDS: pts[0] = trim_toward(pts[0], pts[1], 0.9)
        if e["to"] in STAIR_ENDS: pts[-1] = trim_toward(pts[-1], pts[-2], 0.9)
    if t == "winch":
        leg_box(nm, a + Vector((0, 0, 2.4)), b + Vector((0, 0, 1.2)), 0.08, 0.08, M_GRAY)
    elif t == "ladder":
        # A LADDER EDGE SHIPS NO WALK RIBBON — it never has.  `routes_derive` marks
        # every one of them `blocked: true` and `route_overlay`'s legend has called
        # them "a way on that LOOKS walkable and is not" since it was written.  Round
        # 24's playtest agent spent 22 of its first 24 steps at the foot of two of
        # them, because the blockout drew them whole and evenly runged, exactly like
        # the one flight that works.  So a ladder is built BROKEN from here on:
        # tools/ladder_derate.py owns the shape, and the same module is what the
        # district builders and tools/del_ladder_derate.py (the carrier that put this
        # on the live Dellhollow master) use, so the three cannot drift apart.
        # If a ladder edge is ever meant to be CLIMBABLE, it needs a walk ribbon
        # first — and then it is not a ladder edge.
        import ladder_derate as LD
        v = b - a
        head = a + Vector((0, 0, 0.1))
        n = max(2, int(abs(v.z) / 0.45))
        ss = [r / float(n) for r in range(n)]
        X = Vector((0.35, 0, 0))                 # the rungs' own half-length, world X
        P = lambda s, side: head + v * s + X * side
        for i, (s0, c0, s1, c1) in enumerate(LD.rails()):
            leg_box("%s_stile%d" % (nm, i), P(s0, c0), P(s1, c1), 0.09, 0.09, M_STAIR)
        kept = LD.rungs(ss)
        for r, s in enumerate(ss):
            if s not in kept:
                continue
            leg_box("%s_rung%02d" % (nm, r), P(s, -1), P(s, +1), 0.3, 0.06, M_WOOD)
        s0, c0, s1, c1 = LD.bar()
        leg_box(nm + "_bar", P(s0, c0), P(s1, c1), 0.10, 0.05, M_WOOD)
        s0, c0, s1, c1 = LD.dangle()
        leg_box(nm + "_hang", P(s0, c0), P(s1, c1), 0.07, 0.05, M_WOOD)
        print("  LADDER %s: %s" % (nm, LD.report(ss)))
    elif t == "stairs":
        v2 = ("%s__%s" % (e["from"], e["to"])) in STAIRS_V2
        ew = float(e.get("width", 1.4))
        if not v2:
            for i in range(len(pts) - 1):
                stairs_leg("%s_l%d" % (nm, i), pts[i], pts[i + 1], width=ew)
            for wp in pts[1:-1]:
                bpy.ops.mesh.primitive_cube_add(location=(wp.x, wp.y, wp.z - 0.08))
                o = bpy.context.active_object; o.name = "walk_" + nm + "_landing"
                o.dimensions = (2.0, 2.0, 0.16); o.data.materials.append(M_WOOD)
                link_to(o, "PATHS")
        else:
            # split every interior pivot, then lay the legs between the split ends
            ends = [(pts[0], pts[0])]
            for i in range(1, len(pts) - 1):
                ends.append(pivot_split(pts[i - 1], pts[i], pts[i + 1], asym=(i == 1),
                                        width=ew))
            ends.append((pts[-1], pts[-1]))
            railq = []
            for i in range(len(pts) - 1):
                s, f = ends[i][1], ends[i + 1][0]
                # set the LOWER end back off its landing; the upper end needs no
                # setback (that flight's treads all lie BELOW the landing they leave)
                if i + 1 < len(pts) - 1 and f.z < s.z: f = plan_trim(s, f, FOOT_TRIM)
                elif i > 0 and s.z < f.z:              s = plan_trim(f, s, FOOT_TRIM)
                stairs_leg("%s_l%d" % (nm, i), s, f,
                           rail_ins=(RAIL_INS if i > 0 else 0.0,
                                     RAIL_INS if i + 1 < len(pts) - 1 else 0.0),
                           rail_out=railq, width=ew)
            for i in range(1, len(pts) - 1):
                A, Dp = ends[i]
                sep = Vector((Dp.x - A.x, Dp.y - A.y, 0))
                cx_, cy_ = (A.x + Dp.x) / 2, (A.y + Dp.y) / 2
                if sep.length > 1e-6:
                    ang = math.atan2(sep.y, sep.x)
                    # THE LANDING'S EXTENSION IS ASYMMETRIC, LIKE THE SPLIT (BET 2
                    # iteration 9, measured on the moorage l1/l2 pivot).  A symmetric
                    # + LAND_CROSS box extends 0.70 past BOTH split ends — and past
                    # the ARRIVING end that 0.70 runs UNDER the arriving flight's own
                    # rising treads: t04 (0.84 over the pad, past STEP_UP 0.63)
                    # roofed the tongue's cells and the open throat beside them
                    # measured 0.7 m — under two bodies, and both greedy drives
                    # through the junction stalled on it (with the furniture already
                    # cleared: this strip was the LAST wall).  The up side now gets
                    # 0.15 — enough to keep the foot tread's own join — and the down
                    # side keeps the full 0.70 (nothing of this edge stands above a
                    # departing leg's start; its treads all lie below).
                    up_A = pts[i - 1].z >= pts[i + 1].z   # arriving side is the up side
                    ext_a = 0.15 if up_A else LAND_CROSS / 2
                    ext_d = LAND_CROSS / 2 if up_A else 0.15
                    u = sep.normalized()
                    lx = sep.length + ext_a + ext_d
                    cx_ += u.x * (ext_d - ext_a) / 2
                    cy_ += u.y * (ext_d - ext_a) / 2
                else:   # a gentle turn: lay the slab ACROSS the way through
                    w = Vector((pts[i + 1].x - pts[i - 1].x, pts[i + 1].y - pts[i - 1].y, 0)).normalized()
                    ang = math.atan2(w.y, w.x) + math.pi / 2; lx = LAND_CROSS
                bpy.ops.mesh.primitive_cube_add(
                    location=(cx_, cy_, pts[i].z - 0.08))
                o = bpy.context.active_object; o.name = "walk_" + nm + "_landing"
                # THE PAD SCALES WITH THE FLIGHT IT SERVES (iteration 9, same lesson
                # as the width-scaled pivot split): LAND_LONG 0.90 was sized for 1.4
                # treads meeting the pad end-on; a hairpin's arriving leg meets it
                # BROADSIDE, and 0.90 minus one tread's body shadow is a needle.
                # max(1, w/1.4) keeps every 1.4-wide flight bit-identical.
                o.dimensions = (lx, LAND_LONG * max(1.0, ew / 1.4), 0.16)
                o.rotation_euler = (0, 0, ang)
                o.data.materials.append(M_WOOD)
                link_to(o, "PATHS")
            lay_stair_rails(nm, railq)
    else:
        draw = chaikin(pts) if t in ("road", "path") else pts   # deck/bridge stay segmented
        # `width` honoured for flat ribbons too (BET 2: the crossing ships 1.8 — see the
        # map edge's _bet2_2026-08-06_width for the measured slot arithmetic)
        wdt = float(e.get("width", 1.3 if t == "bridge" else 1.6))
        for i in range(len(draw) - 1):
            leg_box("walk_%s_l%d" % (nm, i), draw[i], draw[i + 1], wdt, 0.14, M_WOOD)
        if t == "bridge":  # low rails so the span reads as a bridge in gray
            for i in range(len(draw) - 1):
                up = Vector((0, 0, 0.45))
                dv = draw[i + 1] - draw[i]
                dn = Vector((dv.x, dv.y, 0)).normalized()
                # rails ride the deck's own edge at any width (w/2 - 0.05); the 0.6
                # literal was exactly that for the old 1.3 deck
                side = dv.cross(Vector((0, 0, 1))).normalized() * (wdt / 2 - 0.05)
                # RAILS INSET 0.55 AT INTERIOR JUNCTIONS (BET 2 iteration 5, measured):
                # un-inset, the two legs' rails MEET at each bend and the inner corner
                # pokes into the corridor — the west drive wedged on railB0/B1's corner
                # at [74.65, 7.96, -22.9], and cx_build's parapet posts followed the bar
                # lines into the l1/l2 bend.  0.55 is stairs_leg's own junction rule
                # (body half-width + margin); span ends need none (the pad clip below
                # already opens them).
                ins_a = dn * 0.55 if i > 0 else Vector((0, 0, 0))
                ins_b = dn * 0.55 if i + 1 < len(draw) - 1 else Vector((0, 0, 0))
                # queued, not laid: see lay_bridge_rails above (BET 2 iteration 5)
                BRIDGE_RAILQ.append(("bar_%s_railA%d" % (nm, i),
                                     draw[i] + up + side + ins_a,
                                     draw[i + 1] + up + side - ins_b, nm[2:]))
                BRIDGE_RAILQ.append(("bar_%s_railB%d" % (nm, i),
                                     draw[i] + up - side + ins_a,
                                     draw[i + 1] + up - side - ins_b, nm[2:]))

lay_bridge_rails()   # every ribbon and pad exists now — clip and lay the queued rails

import os
os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print("BLOCKOUT OK — objects:", len(bpy.data.objects), "| saved", BLEND_OUT)
