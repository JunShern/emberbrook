"""lantern_reseat.py — a lamp that pierces a live landing moves off it, by a
full-height version of its own placement rule (Bet 2 iteration 8).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/lantern_reseat.py -- [save] [revert]

WHY.  locksfoot_build stands its route lanterns through `COR.find_free(x, y,
base + 1.0)` — ONE probe height.  Lantern 1 (brief station 71.80, 26.10) stands
on the low moorage deck, base 1.67, and is 2.34 m tall; r29 then migrated the
weave-huts__moorage switchback to STAIRS_V2 and the l1/l2 pivot landing
(`walk_e_weave-huts__moorage_landing.001`, top 3.30) grew across its plan spot.
The post now PIERCES the landing's body window from below (z 1.67..4.01 through
the 3.30..5.30 corridor) — and the build's own test cannot see it, because
base + 1.0 = 2.67 is UNDER the landing: a locksfoot_build re-run would put the
lantern straight back.  Measured on the 2026-08-06 bundle (_court_probe --who,
0.15 m): **lf_lantern_1 blocks 14 cells of the landing's own ground at
[72.3–72.6, −25.7..−26.3]**, one of the three walls that shut the switchback's
one-thread ascent (the other two: cx_rail posts on t03/t04's own treads, fixed
as cx_build's on_walk_ribbon guard in the same window).

WHAT THIS DOES.  Not a deletion and not an authored move: the generator's own
ring search from the brief's own station, with the one-z probe corrected to the
post's FULL vertical extent over every corridor face (margin 0.30, the build's
own margin).  The group (mesh + point light) translates by one delta; the post
re-seats on the district's own deck at the blessed spot (`deck_below`, the
build's rule).  A lit practical is MOVED, never removed — night-grade doctrine:
source COUNT is what changes a town, so the count stays.

FAITHFULNESS.  Old matrices snapshotted into a `LRS_SRC` text datablock
(fake-user); `revert save` puts every object back bit-exact; a SHA-256 content
digest over every OTHER mesh's name+vertcount is asserted unchanged.
Idempotent: a group already clear of every corridor is a no-op.
"""
import bpy, sys, json, hashlib, math
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import Corridor, point_in_poly, world_bbox

SAVE = "save" in sys.argv
REVERT = "revert" in sys.argv
GROUP = "lf_lantern_1"
STATION = (71.80, 26.10)          # locksfoot_build's own brief for lantern 1
SNAP = "LRS_SRC"
BODY_H = 2.00                     # the corridor band over a walk face


def town_digest(skip):
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or o.name in skip:
            continue
        h.update(o.name.encode())
        h.update(str(len(o.data.vertices)).encode())
    return h.hexdigest()[:16]


group = [o for o in bpy.data.objects
         if o.name == GROUP or o.name.startswith(GROUP + "_") or o.name.startswith(GROUP + ".")]
assert group, "no %s* objects in this master" % GROUP
SKIP = {o.name for o in group}

if REVERT:
    txt = bpy.data.texts.get(SNAP)
    assert txt is not None, "no %s snapshot to revert from" % SNAP
    old = json.loads(txt.as_string())
    for o in group:
        if o.name in old:
            o.matrix_world = [Vector(r) for r in old[o.name]]
    bpy.data.texts.remove(txt)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED", bpy.data.filepath)
    print("REVERTED %d objects" % len(group))
    sys.exit(0)

pre_digest = town_digest(SKIP)

WALKS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
COR = Corridor(WALKS, margin=0.30)
COR0 = Corridor(WALKS, margin=0.0)


def deck_below(x, y, zmax=4.0):
    best = None
    for poly, fn, raw, nm in COR0.tops:
        if point_in_poly(x, y, poly):
            z = fn(x, y)
            if z <= zmax and (best is None or z > best):
                best = z
    return best


bpy.context.view_layer.update()
_DG = bpy.context.evaluated_depsgraph_get()
_SC = bpy.context.scene


def art_below(x, y, zmax=4.0):
    """The district's own visible structure under (x, y) — the build's ground
    fallback (its lanterns stand OFF the walk polys; a seat is deck or ground
    art, never a ribbon).  First render-visible non-walk/bar hit below zmax."""
    org = Vector((x, y, zmax + 2.0))
    d = Vector((0, 0, -1))
    for _ in range(12):
        hit, loc, n, i, ob, mw = _SC.ray_cast(_DG, org, d, distance=12.0)
        if not hit:
            return None
        if not ob.name.startswith(("walk_", "bar_")) and not ob.hide_render and n.z > 0.45:
            return loc.z
        org = loc + d * 0.02
    return None


mesh_parts = [o for o in group if o.type == 'MESH']
bbs = [world_bbox(o) for o in mesh_parts]
x0 = min(b[0] for b in bbs); x1 = max(b[1] for b in bbs)
y0 = min(b[2] for b in bbs); y1 = max(b[3] for b in bbs)
z0 = min(b[4] for b in bbs); z1 = max(b[5] for b in bbs)
H = z1 - z0
FOOT = [((x0 + x1) / 2, (y0 + y1) / 2), (x0, y0), (x0, y1), (x1, y0), (x1, y1)]
cx, cy = FOOT[0]


def pierced(dx, dy, base):
    """Any corridor face whose body window the translated post's z-range enters,
    at any of the five footprint points."""
    top = base + H
    for (fx, fy) in FOOT:
        px, py = fx + dx, fy + dy
        for poly, fn, raw, nm in COR.tops:
            if point_in_poly(px, py, poly):
                t = fn(px, py)
                if top > t + 0.005 and base < t + BODY_H:
                    return nm
    return None


hit = pierced(0.0, 0.0, z0)
if hit is None:
    print("NO-OP: lantern group clear of every corridor (full-height test)")
    sys.exit(0)
print("PIERCES %s at (%.2f, %.2f), post z %.2f..%.2f — searching from the brief "
      "station (%.2f, %.2f)" % (hit, cx, cy, z0, z1, STATION[0], STATION[1]))

best = None
r = 0.2
while r <= 6.0 and best is None:
    for i in range(24):
        a = 2 * math.pi * i / 24
        nx, ny = STATION[0] + math.cos(a) * r, STATION[1] + math.sin(a) * r
        gz = art_below(nx, ny)
        if gz is None:
            continue
        nb = gz - 0.05
        if pierced(nx - cx, ny - cy, nb) is None:
            best = (nx, ny, nb)
            break
    r += 0.2
assert best is not None, "no corridor-free full-height seat within 6 m of the station"
px, py, nb = best
dx, dy, dz = px - cx, py - cy, nb - z0

txt = bpy.data.texts.get(SNAP) or bpy.data.texts.new(SNAP)
txt.use_fake_user = True
txt.clear()
txt.write(json.dumps({o.name: [list(r_) for r_ in o.matrix_world] for o in group}))

for o in group:
    m = o.matrix_world.copy()
    m.translation = m.translation + Vector((dx, dy, dz))
    o.matrix_world = m
bpy.context.view_layer.update()

post_digest = town_digest(SKIP)
assert pre_digest == post_digest, "carrier touched geometry outside the lantern group"
print("RESEAT %s: foot (%.2f, %.2f, %.2f) -> (%.2f, %.2f, %.2f)  delta (%.2f, %.2f, %.2f)"
      % (GROUP, cx, cy, z0, px, py, nb, dx, dy, dz))
print("FAITHFULNESS: digest over every other mesh unchanged: %s" % pre_digest)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
