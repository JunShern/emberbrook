"""emb_pixbox.py — WHERE IS EACH OBJECT ON SCREEN, in a pinned camera's own pixel grid.

    Blender -b <blend> -P tools/emb_pixbox.py -- --cams <cameras.json>
            --want "<frame>:<selector>[;...]" [--margin N] [--json out.json]

`--json` writes a BOX MANIFEST that `tools/emb_lum.py --boxes` reads, so the ruler can tell
you when a measurement box laps a neighbouring object.  That pairing is the instrument this
town bought with three identical mistakes in twelve pixels (see emb_lum's header).

    Blender -b <blend> -P pixbox.py -- --cams <town.cameras.json> --resx 1400 --resy 800
                                       --want "district-entrance:emb_mat_lamp_glass" ...

A measurement box has to be DERIVED, not eyeballed off a bright patch: round 6's own
lesson is that a box picked by eye measures whatever else is bright in it (sun glare
through a tree read as 460 clipped lamp pixels).  So the box comes from the geometry:
project every world vertex of the named objects through the pinned camera and take the
pixel AABB.  Printed with and without a margin so the margin is visible in the record.
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


CAMS = json.load(open(opt("--cams", "")))
RESX, RESY = int(opt("--resx", "1400")), int(opt("--resy", "800"))
MARGIN = int(opt("--margin", "6"))
WANT = [w for w in opt("--want", "").split(";") if w]
JSONOUT = opt("--json", "")
MANIFEST = {}


def pixels(loc, aim, fov, objs):
    mw_loc = Vector(loc)
    q = (Vector(aim) - mw_loc).to_track_quat('-Z', 'Y')
    R = q.to_matrix()
    right, up, fwd = R.col[0], R.col[1], -R.col[2]
    tanh_ = math.tan(math.radians(fov) * 0.5)
    asp = RESX / float(RESY)
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    n = 0
    for o in objs:
        if o.type != 'MESH':
            continue
        m = o.matrix_world
        for v in o.data.vertices:
            p = m @ v.co - mw_loc
            z = p.dot(fwd)
            if z <= 0.01:
                continue
            sx = p.dot(right) / z / tanh_
            sy = p.dot(up) / z / (tanh_ / asp)
            u = (sx + 1.0) * 0.5 * RESX
            vv = (1.0 - sy) * 0.5 * RESY
            x0, x1 = min(x0, u), max(x1, u)
            y0, y1 = min(y0, vv), max(y1, vv)
            n += 1
    if n == 0:
        return None
    return (x0, y0, x1, y1, n)


def clampbox(b, mg):
    x0, y0, x1, y1 = b[:4]
    return (max(0, int(x0) - mg), max(0, int(y0) - mg),
            min(RESX, int(math.ceil(x1)) + mg), min(RESY, int(math.ceil(y1)) + mg))


for w in WANT:
    fid, _, sel = w.partition(":")
    cam = CAMS[fid]
    if sel.startswith("mat="):
        mname = sel[4:]
        objs = [o for o in bpy.data.objects if o.type == 'MESH'
                and any(s.material and s.material.name == mname for s in o.material_slots)]
    else:
        objs = [o for o in bpy.data.objects if sel in o.name]
    print("== %s  selector %r -> %d objects" % (fid, sel, len(objs)))
    # per-object, so a fixture 40 m away is not merged with one at 6 m
    rows = []
    for o in objs:
        b = pixels(cam["loc"], cam["aim"], cam["fov"], [o])
        if b is None:
            continue
        x0, y0, x1, y1, n = b
        if x1 < 0 or y1 < 0 or x0 > RESX or y0 > RESY:
            continue
        d = (Vector(o.matrix_world.translation) - Vector(cam["loc"])).length
        rows.append((d, o.name, clampbox(b, MARGIN), (x1 - x0) * (y1 - y0)))
    rows.sort()
    for d, nm, bx, area in rows:
        print("   %7.2f m  %-44s box %d,%d,%d,%d  (%.0f px2 raw)"
              % (d, nm, *bx, area))
        MANIFEST.setdefault(fid, {})[nm] = list(bx)
    if not rows:
        print("   NONE in frame")

if JSONOUT:
    import json as _j
    _j.dump(MANIFEST, open(JSONOUT, "w"), indent=1)
    print("BOX MANIFEST written to %s — pass it to tools/emb_lum.py --boxes so every "
          "measurement says whether it laps a neighbour." % JSONOUT)
