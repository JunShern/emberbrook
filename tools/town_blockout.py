# town_blockout.py — raise a whole-town gray blockout in Blender from a townmap JSON.
# Run inside Blender (via MCP: exec(open(__file__).read()) or blender -b -P).
# Deterministic: same JSON -> same scene. WIPES the current scene.
#
# Geometry rules mirror the townmap viewer's material-aware rendering:
#   road/path   -> chaikin-smoothed flat ribbons (earth)
#   deck/bridge -> straight plank ribbons, leg per waypoint segment (timber)
#   stairs      -> real treads (rise <= 0.4/tread) + landing pads at waypoints
#   ladder      -> steep rail + rungs
#   winch       -> thin cable (non-walkable)
# Landmarks by class: structure (kind-shaped massing), area (flat disc, extent),
# prop (small block), portal (posts + lintel), dressing (dark simplified block).

import bpy, json, math
from mathutils import Vector

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
        r = lm.get("extent", 3)
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.25, location=(x, y, z + 0.12))
        o = bpy.context.active_object; o.name = "walk_lm_" + i
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

def stairs_leg(name, a, b):
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
        ins = max(0.55, hl * drop_frac)
        fwd_a = Vector((v.x, v.y, 0)).normalized() * ins
        fwd_b = Vector((v.x, v.y, 0)).normalized() * 0.55
        up = Vector((0, 0, 0.55))
        for sgn, tag in ((1, "A"), (-1, "B")):
            ra = a + side * sgn + up + fwd_a; rb = b + side * sgn + up - fwd_b
            leg_box("bar_%s_rail%s" % (name, tag), ra, rb, 0.06, 0.9, M_STAIR)
    n = max(1, math.ceil(abs(rise) / 0.4))
    for t in range(n):
        p0 = a + v * (t / n); p1 = a + v * ((t + 1) / n)
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
        v = b - a
        leg_box(nm + "_rail", a + Vector((0, 0, 0.1)), b, 0.5, 0.12, M_STAIR)
        n = max(2, int(abs(v.z) / 0.45))
        for r in range(n):
            p = a + v * (r / n)
            leg_box("%s_rung%02d" % (nm, r), p + Vector((-0.35, 0, 0.1)), p + Vector((0.35, 0, 0.1)), 0.3, 0.06, M_WOOD)
    elif t == "stairs":
        for i in range(len(pts) - 1):
            stairs_leg("%s_l%d" % (nm, i), pts[i], pts[i + 1])
        for wp in pts[1:-1]:
            bpy.ops.mesh.primitive_cube_add(location=(wp.x, wp.y, wp.z - 0.08))
            o = bpy.context.active_object; o.name = "walk_" + nm + "_landing"
            o.dimensions = (2.0, 2.0, 0.16); o.data.materials.append(M_WOOD)
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
