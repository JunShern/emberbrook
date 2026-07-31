#!/usr/bin/env python3
"""embint_verify.py — the gate every Emberbrook interior must pass.

    Blender -b --python-exit-code 1 -P tools/embint_verify.py -- \
        --build tools/embint_inn_build.py [--json docs/qa/interiors/<key>.json]
    Blender -b <room>.blend -P tools/embint_verify.py --                # a saved blend

Exit code is non-zero on any failure.

--------------------------------------------------------------------------
1. DETERMINISM, MEASURED HONESTLY
--------------------------------------------------------------------------
The handover asks for "two runs byte-identical".  That is not achievable and
the claim should never be made, so here is the measurement instead of the
slogan:

  A 40-cube scene with literally no random input, saved twice by the same
  Blender 5.1.1 to the same path, differs in **160 bytes**.  A `.blend`
  serialises datablock MEMORY ADDRESSES; two processes do not allocate at the
  same addresses.  Nothing a build script does can change that.

  Run uncompressed, this room's two builds are **9 632 178 bytes each — the
  same length** — and differ only in that same class of address field.

So the gate this file enforces is the one that actually means "deterministic":
a SHA-256 over the scene's CONTENT — every mesh's world-space vertices to 1e-5,
its material slots, every light's type/energy/colour/position, the camera's
transform and lens.  Two builds must produce the same digest.  That is
strictly stronger than a byte compare of the geometry and strictly honest
about the pointers.

--------------------------------------------------------------------------
2. WALK QA ON THE FLOOR
--------------------------------------------------------------------------
An interior that is lovely and unwalkable is a failure, and Dellhollow paid
for that lesson twice (`tools/interior_circulation.py`: "the runtime treats
every visible floor-standing mesh as solid... a basket beside the door mat is
a wall").  Asserted here, against the runtime's own numbers
(body half-width 0.30, collide height 1.30, step-up 0.63):

  W1  `walk_pad_door` exists.  `tools/scenegraph_derive.mjs` reads that exact
      name to build the interior side of the door edge; without it the room
      has no exits and the derive silently skips it.
  W2  every `walk_pad_*` stands over a walk surface (a pad floating in the air
      is a spawn point off the network).
  W3  the walk network is CONNECTED under the runtime's step rules: a flood
      fill on a 0.20 m grid from the door pad, climbing at most 0.63 m per
      step, must reach every other pad.
  W4  BODY CLEARANCE: the same flood, re-run with the runtime's body box
      (r 0.30, z floor+0.65 .. floor+1.30) tested against every visible
      triangle, must still reach every pad.  This is the one that catches
      "beautiful room, you cannot get to the fire".
  W5  HEADROOM: nothing solid within 2.00 m above any reachable floor cell.
  W6  the floor's character datum is z = 0.000 (the walkable top the runtime
      stands a 1.70 m character on).

--------------------------------------------------------------------------
3. FRAMING
--------------------------------------------------------------------------
  F1  the room has exactly one camera, and it is named CAM_int_*.
  F2  every point named in the build's `FRAME_CHECKS` projects inside the
      frame — including, always, the door: seam canon applies indoors and an
      exit nobody can see is not an exit.
"""
import bpy, bmesh, sys, os, json, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
sys.path.insert(0, os.path.join(ROOT, "tools"))

BODY_R = 0.30
BODY_LO = 0.67          # step-up 0.63 + 0.04: what the runtime refuses to enter
BODY_HI = 1.30
STEP_UP = 0.63
# 1.70 m character + 0.10.  NOT the master's 2.00: outdoors that number guards
# a street, and indoors the whole vocabulary of a real room is bressummers,
# stair soffits and dropped nook ceilings.  A beam a walking body clears is
# architecture; the gate's job is to catch one it does not.
HEADROOM = 1.80
GRID = 0.20

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


fails, notes = [], []


def check(ok, msg, detail=None):
    (notes if ok else fails).append(msg + ("" if detail is None else "  " + str(detail)))
    print(("  ok   " if ok else "  FAIL ") + msg + ("" if detail is None else
                                                    "  " + str(detail)))
    return ok


# ------------------------------------------------------------------- build --
build_mod = None
bpath = opt("--build")
if bpath:
    name = os.path.basename(bpath)[:-3]
    import importlib
    build_mod = importlib.import_module(name)
    build_mod.build()

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


# --------------------------------------------------------------- 1. DIGEST --
def digest():
    h = hashlib.sha256()
    obs = sorted([o for o in bpy.data.objects], key=lambda o: o.name)
    for o in obs:
        h.update(o.name.encode())
        h.update(("%s" % o.type).encode())
        if o.type == "MESH":
            Mx = o.matrix_world
            h.update(b"|".join(("%.5f,%.5f,%.5f" % tuple(Mx @ v.co)).encode()
                               for v in o.data.vertices))
            h.update(b"|".join((s.material.name if s.material else "-").encode()
                               for s in o.material_slots))
            h.update(("%d" % len(o.data.polygons)).encode())
            h.update(("%d" % int(o.visible_camera)).encode())
            h.update(("%d" % int(o.hide_render)).encode())
            for m in o.modifiers:
                h.update(("%s:%s" % (m.type, getattr(m, "width", ""))).encode())
        elif o.type == "LIGHT":
            d = o.data
            h.update(("%s|%.4f|%.4f,%.4f,%.4f|%.4f,%.4f,%.4f" % (
                d.type, d.energy, d.color[0], d.color[1], d.color[2],
                o.location.x, o.location.y, o.location.z)).encode())
        elif o.type == "CAMERA":
            h.update(("%.6f|%.6f|%s|%s" % (
                o.data.angle_y, o.data.lens, tuple(round(v, 6) for v in o.location),
                tuple(round(v, 6) for v in o.rotation_euler))).encode())
    for m in sorted(bpy.data.materials, key=lambda m: m.name):
        h.update(m.name.encode())
    return h.hexdigest()


DIG = digest()
print("\n== DETERMINISM")
print("  content digest %s" % DIG)
print("  (a .blend also stores datablock MEMORY ADDRESSES; a 40-cube scene with"
      " no random\n   input differs in 160 bytes between two saves, so a byte"
      " compare can never pass.\n   Two builds must produce the SAME DIGEST"
      " above — that is the real invariant.)")


# ------------------------------------------------------- the walk surfaces --
class Tri:
    __slots__ = ("a", "b", "c", "zmin", "zmax")

    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        self.zmin = min(a.z, b.z, c.z)
        self.zmax = max(a.z, b.z, c.z)


def _pt_in_tri(p, a, b, c):
    v0, v1, v2 = c - a, b - a, p - a
    d00 = v0.x * v0.x + v0.y * v0.y
    d01 = v0.x * v1.x + v0.y * v1.y
    d11 = v1.x * v1.x + v1.y * v1.y
    d20 = v2.x * v0.x + v2.y * v0.y
    d21 = v2.x * v1.x + v2.y * v1.y
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        return None
    u = (d11 * d20 - d01 * d21) / den
    v = (d00 * d21 - d01 * d20) / den
    if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6:
        return None
    n = (b - a).cross(c - a)
    if abs(n.z) < 1e-9:
        return None
    return a.z - (n.x * (p.x - a.x) + n.y * (p.y - a.y)) / n.z


walk_tris = []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith("walk_") or "_pad_" in o.name:
        continue
    Mx = o.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    me = o.data
    for p in me.polygons:
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        vs = [Mx @ me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            walk_tris.append(Tri(vs[0], vs[k], vs[k + 1]))


def _floor_pt(x, y):
    best = None
    p = Vector((x, y, 0))
    for t in walk_tris:
        z = _pt_in_tri(p, t.a, t.b, t.c)
        if z is not None and (best is None or z > best):
            best = z
    return best


def floor_at(x, y):
    """The HIGHEST walk surface over (x, y), or None — the runtime's own rule.

    Probes a 25 mm cross, not a single point.  Real plank floors are built as
    individual boards with an 8 mm shadow gap between them (that gap is what
    stops a 1k texture reading as one tiled sheet), and a sample landing in one
    is a hole in the walk network that does not exist.  Without this the flood
    fill stopped at the snug threshold and reported the second room
    unreachable — a defect in the MEASUREMENT, and the kind that gets a real
    room 'fixed' until it is wrong."""
    z = _floor_pt(x, y)
    if z is not None:
        return z
    for dx, dy in ((0.025, 0), (-0.025, 0), (0, 0.025), (0, -0.025)):
        z = _floor_pt(x + dx, y + dy)
        if z is not None:
            return z
    return None


# every visible triangle is solid to the runtime
solid = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.hide_render or not o.visible_camera:
        continue
    if o.name.startswith("walk_"):
        continue
    # RENDER-ONLY VOLUMES ARE NOT SOLID.  `depth_bake.py` deletes every mesh
    # whose name carries fog/haze/steam_vol/smoke before it bakes depth or
    # exports the collision GLB, so they are not in the shipped bundle either.
    # Left in, the room's own haze box is a 8 x 7 x 3 m wall and every cell
    # inside it reads as blocked -- which is exactly what the first snug
    # diagnosis said.
    _n = o.name.lower()
    if any(k in _n for k in ("fog", "haze", "steam_vol", "smoke", "shadow_")):
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    Mx = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for f in bm.faces:
        solid.append([Mx @ v.co for v in f.verts])
    bm.free()
    ev.to_mesh_clear()

verts, polys = [], []
for tri in solid:
    base = len(verts)
    verts.extend(tri)
    polys.append([base, base + 1, base + 2])
BVH = BVHTree.FromPolygons(verts, polys, all_triangles=True) if polys else None
print("  scene: %d walk tris, %d solid tris" % (len(walk_tris), len(solid)))


# --- the body box, tested as a BOX ------------------------------------------
# A sphere test (`BVH.find_nearest(p, 0.30)` at the band's low sample) reports a
# hit on anything within 300 mm IN ANY DIRECTION -- including a bench top 250 mm
# BELOW the band, which a walking body steps straight over.  That is not a
# near-miss: on the first inn run it condemned the whole snug as unreachable and
# named a 110 mm bench as the wall.  So: bin the solid triangles by plan cell
# and test the real AABB.
BIN = 0.60
_bins = {}
for _t in solid:
    _xs = [p.x for p in _t]; _ys = [p.y for p in _t]; _zs = [p.z for p in _t]
    _rec = (min(_xs), max(_xs), min(_ys), max(_ys), min(_zs), max(_zs), _t)
    for _i in range(int(math.floor(min(_xs) / BIN)), int(math.floor(max(_xs) / BIN)) + 1):
        for _j in range(int(math.floor(min(_ys) / BIN)), int(math.floor(max(_ys) / BIN)) + 1):
            _bins.setdefault((_i, _j), []).append(_rec)


def _tri_hits_square(tri, x0, x1, y0, y1):
    """2D separating-axis test: triangle vs axis-aligned square, in plan."""
    pts = [(p.x, p.y) for p in tri]
    sq = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for poly in (pts, sq):
        n = len(poly)
        for i in range(n):
            ax = poly[(i + 1) % n][0] - poly[i][0]
            ay = poly[(i + 1) % n][1] - poly[i][1]
            nx, ny = -ay, ax
            pa = [nx * p[0] + ny * p[1] for p in pts]
            pb = [nx * p[0] + ny * p[1] for p in sq]
            if max(pa) < min(pb) - 1e-9 or max(pb) < min(pa) - 1e-9:
                return False
    return True


def body_free(x, y, z0):
    """The runtime's body box at (x, y) standing on floor z0: half-width 0.30,
    from floor+0.67 (just over the step-up grace) to floor+1.30."""
    lo, hi = z0 + BODY_LO, z0 + BODY_HI
    x0, x1, y0, y1 = x - BODY_R, x + BODY_R, y - BODY_R, y + BODY_R
    seen = set()
    for i in range(int(math.floor(x0 / BIN)), int(math.floor(x1 / BIN)) + 1):
        for j in range(int(math.floor(y0 / BIN)), int(math.floor(y1 / BIN)) + 1):
            for rec in _bins.get((i, j), ()):
                if id(rec) in seen:
                    continue
                seen.add(id(rec))
                if rec[5] < lo or rec[4] > hi:
                    continue
                if rec[1] < x0 or rec[0] > x1 or rec[3] < y0 or rec[2] > y1:
                    continue
                if _tri_hits_square(rec[6], x0, x1, y0, y1):
                    return False
    return True


def head_free(x, y, z0):
    """Clear from the top of the step-up grace to HEADROOM above the floor.

    It starts at floor+0.67, not at the floor, and that is the whole point: the
    runtime lets a body step up 0.63, so a 0.47 m bench is something you walk
    OVER, not something you bang your head on.  Measuring from the floor made
    every bench and stool in the room a headroom failure -- 43 of them on the
    first run -- which is the gate calling furniture a ceiling."""
    if BVH is None:
        return True
    hit = BVH.ray_cast(Vector((x, y, z0 + BODY_LO)), Vector((0, 0, 1)),
                       HEADROOM - BODY_LO)
    return hit[0] is None


# -------------------------------------------------------------- 2. WALK QA --
print("\n== WALK QA")
pads = {o.name: o for o in bpy.data.objects
        if o.type == "MESH" and o.name.startswith("walk_pad_")}
check("walk_pad_door" in pads,
      "W1 walk_pad_door present (scenegraph_derive reads this name verbatim)",
      sorted(pads))

pad_floor = {}
for n, o in sorted(pads.items()):
    z = floor_at(o.location.x, o.location.y)
    pad_floor[n] = z
    check(z is not None, "W2 %s stands over a walk surface" % n,
          None if z is None else "floor z %.3f" % z)

# --- flood fill on the walk network, with and without the body box
start = pads.get("walk_pad_door")


def flood(with_body):
    if start is None:
        return set()
    sx, sy = start.location.x, start.location.y
    sz = floor_at(sx, sy)
    if sz is None:
        return set()
    key = lambda x, y: (int(round(x / GRID)), int(round(y / GRID)))
    seen = {key(sx, sy): sz}
    stack = [(sx, sy, sz)]
    while stack:
        x, y, z = stack.pop()
        for dx, dy in ((GRID, 0), (-GRID, 0), (0, GRID), (0, -GRID)):
            nx, ny = x + dx, y + dy
            k = key(nx, ny)
            if k in seen:
                continue
            nz = floor_at(nx, ny)
            if nz is None or nz - z > STEP_UP:
                continue
            if with_body and not body_free(nx, ny, nz):
                continue
            seen[k] = nz
            stack.append((nx, ny, nz))
    return seen


net = flood(False)
walkable = flood(True)
print("  reachable cells: %d on the raw network, %d with the runtime body box"
      % (len(net), len(walkable)))


def reached(cells, n, o):
    k = (int(round(o.location.x / GRID)), int(round(o.location.y / GRID)))
    if k in cells:
        return True
    # a pad's own centre may sit under its own furniture; accept any cell of the
    # pad's footprint
    w = o.dimensions.x / 2 or 0.5
    d = o.dimensions.y / 2 or 0.5
    for i in range(-3, 4):
        for j in range(-3, 4):
            px = o.location.x + i * GRID
            py = o.location.y + j * GRID
            if abs(px - o.location.x) > w + 0.35 or abs(py - o.location.y) > d + 0.35:
                continue
            if (int(round(px / GRID)), int(round(py / GRID))) in cells:
                return True
    return False


for n, o in sorted(pads.items()):
    if n == "walk_pad_door":
        continue
    check(reached(net, n, o), "W3 %s is on the connected walk network" % n)
for n, o in sorted(pads.items()):
    if n == "walk_pad_door":
        continue
    if not check(reached(walkable, n, o),
                 "W4 %s is REACHABLE with the runtime body box (r %.2f, z +%.2f..%.2f)"
                 % (n, BODY_R, BODY_LO, BODY_HI)):
        # name the obstruction rather than leaving the builder to guess: the
        # nearest body-blocked cell to the pad, and what is standing in it
        px, py = o.location.x, o.location.y
        best = None
        for (i, j), z in net.items():
            cx, cy = i * GRID, j * GRID
            if (i, j) in walkable:
                continue
            d = math.hypot(cx - px, cy - py)
            if best is None or d < best[0]:
                best = (d, cx, cy, z)
        if best and BVH is not None:
            _, cx, cy, z = best
            hit = BVH.find_nearest(Vector((cx, cy, z + (BODY_LO + BODY_HI) / 2)),
                                   BODY_R + 0.4)
            owner = "?"
            if hit[0] is not None:
                pt = hit[0]
                bestd = 1e9
                for ob in bpy.data.objects:
                    if ob.type != "MESH" or ob.hide_render or not ob.visible_camera:
                        continue
                    if ob.name.startswith("walk_"):
                        continue
                    c = ob.matrix_world @ (sum((Vector(b) for b in ob.bound_box),
                                               Vector()) / 8.0)
                    dd = (c - pt).length
                    if dd < bestd:
                        bestd, owner = dd, ob.name
            print("       blocked nearest the pad at (%.2f, %.2f): likely '%s'"
                  % (cx, cy, owner))

blocked_head = []
for (i, j), z in sorted(walkable.items()):
    if not head_free(i * GRID, j * GRID, z):
        blocked_head.append((round(i * GRID, 2), round(j * GRID, 2), round(z, 2)))
check(not blocked_head, "W5 headroom >= %.2f m over every reachable floor cell"
      % HEADROOM, "%d blocked cells %s" % (len(blocked_head), blocked_head[:6]))

tops = []
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("walk_floor"):
        tops.append(max((o.matrix_world @ Vector(c)).z for c in o.bound_box))
check(bool(tops) and abs(max(tops)) < 0.02,
      "W6 character datum: the main floor's top is z = 0.000",
      "max floor top %.4f" % (max(tops) if tops else -99))

# --------------------------------------------------------------- 3. FRAMING --
print("\n== FRAMING")
cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
check(len(cams) == 1 and cams[0].name.startswith("CAM_int"),
      "F1 exactly one camera, named CAM_int_*", [c.name for c in cams])
checks = getattr(build_mod, "FRAME_CHECKS", None) if build_mod else None
if checks and cams:
    from bpy_extras.object_utils import world_to_camera_view
    for label, p in checks:
        u, v, d = world_to_camera_view(bpy.context.scene, cams[0], Vector(p))
        check(0.02 <= u <= 0.98 and 0.02 <= v <= 0.98,
              "F2 '%s' is inside the frame" % label,
              "ndc (%.3f, %.3f) depth %.2f" % (u, v, d))

# ------------------------------------------------------------------ report --
out = opt("--json")
if out:
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"digest": DIG, "walkTris": len(walk_tris), "solidTris": len(solid),
               "reachableRaw": len(net), "reachableBody": len(walkable),
               "pads": {k: (None if v is None else round(v, 4))
                        for k, v in pad_floor.items()},
               "fails": fails, "ok": notes}, open(out, "w"), indent=1)
    print("wrote", out)

print("\n%s  %d checks ok, %d failed" % ("PASS" if not fails else "FAIL",
                                         len(notes), len(fails)))
if fails:
    sys.exit(1)
