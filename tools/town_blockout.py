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
STAIRS_V2 = {"deep-stairs-head__deep-stairs-foot"}


def pivot_split(prev, w, nxt, asym=False):
    """(arriving-leg END, departing-leg START) at an interior stairs waypoint.

    THE SPLIT IS ASYMMETRIC: the departing leg takes the WHOLE separation and the
    arriving leg's line is left alone.  A balanced split swings the arriving leg too,
    and the first leg cannot afford it (see the ribbon note above) — but it was also
    tried EVERYWHERE ELSE, where it is free of that constraint, and it was worse:
    balanced at pivots 2..4 drove 36/40 where asymmetric drove 40/40.  One line moved
    per pivot is both the safer rule and the measured one."""
    a = Vector((w.x - prev.x, w.y - prev.y, 0))
    d = Vector((nxt.x - w.x, nxt.y - w.y, 0))
    if a.length < 1e-6 or d.length < 1e-6: return w, w
    a.normalize(); d.normalize()
    th = math.degrees(math.acos(max(-1.0, min(1.0, a.dot(d)))))
    off = PIVOT_OFF * max(0.0, min(1.0, (th - PIVOT_KNEE) / PIVOT_SPAN))
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


def plan_trim(a, b, t):
    """pull b back toward a by t IN PLAN, keeping b's height (the riser count and
    every tread top are unchanged; only the run shortens, which walks the ladder
    out from under the landing)."""
    v = Vector((b.x - a.x, b.y - a.y, 0)); L = v.length
    if L <= t + 0.6: return b
    return b - v.normalized() * t


def stairs_leg(name, a, b, rail_ins=(0.0, 0.0)):
    v = b - a; rise = b.z - a.z
    hl = Vector((v.x, v.y, 0)).length
    # side rails: stop walkers mounting flights sideways (the scoop-trap), read as
    # rickety-town railings. bar_ = collision barrier, never a floor (thin + tall).
    side = Vector((v.y, -v.x, 0))
    if side.length > 1e-6 and hl > 1.6:
        # wide enough that the walker's side-rays clear them ON the flight
        # (tread half-width 0.7 + char radius 0.42 + margin), inset from both
        # ends so junctions/landings stay open
        side = side.normalized() * 1.25
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
        o.dimensions = (max(hl / n, 0.35), 1.4, 0.14)
        o.rotation_euler = (0, 0, math.atan2(v.y, v.x))
        o.data.materials.append(M_STAIR)
        link_to(o, "PATHS")

LM_CLASS = {l["id"]: l for l in D["landmarks"]}
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
            pts[idx] = trim_toward(pts[idx], pts[nbr], r)
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
        if not v2:
            for i in range(len(pts) - 1):
                stairs_leg("%s_l%d" % (nm, i), pts[i], pts[i + 1])
            for wp in pts[1:-1]:
                bpy.ops.mesh.primitive_cube_add(location=(wp.x, wp.y, wp.z - 0.08))
                o = bpy.context.active_object; o.name = "walk_" + nm + "_landing"
                o.dimensions = (2.0, 2.0, 0.16); o.data.materials.append(M_WOOD)
                link_to(o, "PATHS")
        else:
            # split every interior pivot, then lay the legs between the split ends
            ends = [(pts[0], pts[0])]
            for i in range(1, len(pts) - 1):
                ends.append(pivot_split(pts[i - 1], pts[i], pts[i + 1], asym=(i == 1)))
            ends.append((pts[-1], pts[-1]))
            for i in range(len(pts) - 1):
                s, f = ends[i][1], ends[i + 1][0]
                # set the LOWER end back off its landing; the upper end needs no
                # setback (that flight's treads all lie BELOW the landing they leave)
                if i + 1 < len(pts) - 1 and f.z < s.z: f = plan_trim(s, f, FOOT_TRIM)
                elif i > 0 and s.z < f.z:              s = plan_trim(f, s, FOOT_TRIM)
                stairs_leg("%s_l%d" % (nm, i), s, f,
                           rail_ins=(RAIL_INS if i > 0 else 0.0,
                                     RAIL_INS if i + 1 < len(pts) - 1 else 0.0))
            for i in range(1, len(pts) - 1):
                A, Dp = ends[i]
                sep = Vector((Dp.x - A.x, Dp.y - A.y, 0))
                if sep.length > 1e-6:
                    ang = math.atan2(sep.y, sep.x); lx = sep.length + LAND_CROSS
                else:   # a gentle turn: lay the slab ACROSS the way through
                    w = Vector((pts[i + 1].x - pts[i - 1].x, pts[i + 1].y - pts[i - 1].y, 0)).normalized()
                    ang = math.atan2(w.y, w.x) + math.pi / 2; lx = LAND_CROSS
                bpy.ops.mesh.primitive_cube_add(
                    location=((A.x + Dp.x) / 2, (A.y + Dp.y) / 2, pts[i].z - 0.08))
                o = bpy.context.active_object; o.name = "walk_" + nm + "_landing"
                o.dimensions = (lx, LAND_LONG, 0.16)
                o.rotation_euler = (0, 0, ang)
                o.data.materials.append(M_WOOD)
                link_to(o, "PATHS")
    else:
        draw = chaikin(pts) if t in ("road", "path") else pts   # deck/bridge stay segmented
        wdt = 1.3 if t == "bridge" else 1.6
        for i in range(len(draw) - 1):
            leg_box("walk_%s_l%d" % (nm, i), draw[i], draw[i + 1], wdt, 0.14, M_WOOD)
        if t == "bridge":  # low rails so the span reads as a bridge in gray
            for i in range(len(draw) - 1):
                up = Vector((0, 0, 0.45))
                side = (draw[i + 1] - draw[i]).cross(Vector((0, 0, 1))).normalized() * 0.6
                leg_box("bar_%s_railA%d" % (nm, i), draw[i] + up + side, draw[i + 1] + up + side, 0.08, 0.5, M_WOOD)
                leg_box("bar_%s_railB%d" % (nm, i), draw[i] + up - side, draw[i + 1] + up - side, 0.08, 0.5, M_WOOD)

import os
os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print("BLOCKOUT OK — objects:", len(bpy.data.objects), "| saved", BLEND_OUT)
