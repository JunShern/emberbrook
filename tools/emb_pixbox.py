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

THE PROJECTION CONVENTION, NAMED, BECAUSE GETTING IT WRONG IS INVISIBLE AT FRAME CENTRE.
`cine_bake` builds its cameras with `sensor_fit = 'VERTICAL'` and `angle_y = fov`.  So the
half-angle the FOV describes is the VERTICAL one: tan(fov/2) is the vertical half-tangent,
and the horizontal half-tangent is tan(fov/2) * aspect.  The aspect therefore divides X and
never Y.  Until 2026-08-01 this file had it on Y, and the resulting boxes were correct at the
centre of frame and wrong everywhere else — 857 px out at a corner.  Every off-centre box
this tool produced before that date is VOID.

    Blender -b <blend> -P tools/emb_pixbox.py -- --cams <cams.json> --selftest

`--selftest` is the proof that caught the bug, kept as the gate that prevents its return: it
fires a ray through five pixels (centre plus four well off-centre), lets Blender's own
ray_cast find the world point, projects that point back through this file's own maths, and
FAILS above 0.5 px.  A centre-only test would have passed on the broken code — the off-centre
samples are the whole point.
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
            # THE ASPECT BELONGS ON X, AND FOR TWO YEARS IT WAS ON Y (fixed 2026-08-01).
            # cine_bake builds every camera with sensor_fit='VERTICAL' and angle_y = fov,
            # so `tanh_` is the VERTICAL half-tangent and the horizontal one is tanh_*asp.
            # This read `sx = .../tanh_` and `sy = .../(tanh_/asp)`, which puts the aspect
            # on the wrong axis. The error is EXACTLY ZERO AT FRAME CENTRE and grows toward
            # the edges — 857 px at a corner of a 2688x1536 plate — which is why it survived
            # every eyeball check ever run on it: the boxes people validated were central.
            # `--selftest` now round-trips five pixels and fails above 0.5 px; see below.
            sx = p.dot(right) / z / (tanh_ * asp)
            sy = p.dot(up) / z / tanh_
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


def selftest():
    """THE CLOSED LOOP, KEPT. Ray out through a pixel, project the hit back, demand the same
       pixel. Five samples: centre plus four well off-centre, because the defect this guards
       against is EXACTLY ZERO at centre and only appears at the edges."""
    import bpy as _b
    camid = WANT[0].split(":")[0] if WANT else sorted(CAMS)[0]
    cam = CAMS[camid]
    loc = Vector(cam["loc"])
    fwd_v = (Vector(cam["aim"]) - loc).normalized()
    R = fwd_v.to_track_quat('-Z', 'Y').to_matrix()
    right, up, fwd = R.col[0], R.col[1], -R.col[2]
    tanh_ = math.tan(math.radians(cam["fov"]) * 0.5)
    asp = RESX / float(RESY)
    dg = _b.context.evaluated_depsgraph_get()
    sc = _b.context.scene
    pts = [(RESX // 2, RESY // 2), (int(RESX * 0.92), int(RESY * 0.18)),
           (int(RESX * 0.08), int(RESY * 0.85)), (int(RESX * 0.90), int(RESY * 0.88)),
           (int(RESX * 0.10), int(RESY * 0.12))]
    worst, tested, missed = 0.0, 0, 0
    print("PIXBOX SELFTEST  round-tripping %d pixels through %s" % (len(pts), camid))
    for PX, PY in pts:
        sx = (2 * PX / RESX - 1) * tanh_ * asp
        sy = (1 - 2 * PY / RESY) * tanh_
        d = (fwd + right * sx + up * sy).normalized()
        hit, pos_, _n, _i, ob, _m = sc.ray_cast(dg, loc, d, distance=2000.0)
        if not hit:
            print("   (%5d,%5d)  no geometry along this ray — skipped" % (PX, PY))
            missed += 1
            continue
        dd = pos_ - loc
        z = dd.dot(fwd)
        u = (dd.dot(right) / z / (tanh_ * asp) + 1) * 0.5 * RESX
        v = (1 - dd.dot(up) / z / tanh_) * 0.5 * RESY
        err = math.hypot(u - PX, v - PY)
        worst = max(worst, err)
        tested += 1
        print("   (%5d,%5d) -> %-30s -> (%7.1f,%7.1f)  err %.3f px"
              % (PX, PY, ob.name[:30], u, v, err))
    assert tested >= 2, ("PIXBOX SELFTEST inconclusive: only %d of %d rays hit geometry. "
                         "Point it at a camera that frames something." % (tested, len(pts)))
    assert worst <= 0.5, ("PIXBOX SELFTEST FAILED: worst round-trip error %.2f px (bar 0.5). "
                          "The projection convention is wrong — check that the aspect divides "
                          "X and not Y for a sensor_fit='VERTICAL' camera." % worst)
    print("PIXBOX SELFTEST  PASS — worst round-trip error %.3f px over %d rays (bar 0.5)"
          % (worst, tested))


if "--selftest" in argv:
    selftest()

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
