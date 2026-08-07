"""qm_awning_fix.py — THE QUAY-MARKET AWNINGS STOP READING AS FLOATING PALE SLIVERS.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/qm_awning_fix.py -- [save]

A CARRIER, not a rebuild.  `qm_build.py` derives its walls and stall sites FROM
walk records, so re-running it against the live master moves shipped red-teamed
art (CLAUDE.md, district-art carries).  This edits the five `qm_awning_*` meshes
in place and touches nothing else.

WHAT WAS MEASURED (graphics round 3, item 3; the round-2 residual was filed as
"the quay-west deck sliver, ribbon edge-on" and that attribution is WRONG).
Pixel ray-census replaying quay-west's own solved camera, on the two bright
pale strips at u 0.42..0.49 / v 0.423..0.436 and u 0.53..0.60 / v 0.449..0.456:

    every hit is `qm_awning_3` / `qm_awning_4`, material mat_qm_awning

not the round-2 paving ribbon (`walk_e_market-stalls__lockhead_l0`), which the
same census never sees from that camera.  Two defects, both structural:

  1. PITCH.  `qm_build.stall()` sets the lip from `awning_lip()` — walk ground
     + AWN_CLEAR (2.24 m) — and then takes the ridge as `max(zc + 2.30,
     lip + 0.26)`.  Wherever headroom drives the lip, the second term wins and
     the canvas ships with 0.26 m of fall over 0.98 m of depth: a 15 deg sheet.
     quay-west looks down at ~19 deg, so the canvas is within ~4 deg of the view
     ray and collapses to a ~25 px strip — and being the only sunlit surface in
     a shadowed pocket, that strip blows out to near-white.  A stripe of canvas
     seen end-on with nothing under it in light is a floating sliver.
  2. WINDING.  `qm_awning_0/1/3/4` have 0 of 12 faces pointing up; only
     `qm_awning_2` (built with the opposite sign on y) and every
     `shelf_awning_*` are correct.  `awning()` appends its quads with one fixed
     winding, so which way the normals face depends on the sign of
     (y_out - y_wall).  Cycles shades two-sided so the plates hid it; the
     realtime tier's backface culling would not.

THE FIX, and what it deliberately does NOT touch: **the lip does not move.**
The lip is the headroom contract (measured 2.29 m over `qm_paving` under
awning_3's lip, against the district's 2.24 m rule and the master's 2.05 m
corridor) and this carrier asserts it byte-for-byte afterwards.  All the new
geometry goes UP, at the ridge, which hangs over the stall counter (top z 15.24)
and has free air to the bunting above it.  The ridge rises until the pitch
reaches PITCH_WANT or until it is CEIL_GAP under whatever the ray finds above
it, whichever comes first — measured per awning, never typed.  The mid row keeps
its share of the fall plus the builder's own 0.055 m sag, so the canvas stays
curved instead of becoming a folded plane.

GATE (prints, and exits 1 on a violation): every awning's lip z unchanged to
1e-6, every face up, pitch and the measured ceiling gap reported per awning.
"""
import bpy, sys, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
PROP = "qm_awn_fix"

PITCH_WANT = 0.52      # metres of fall the canvas wants over its own depth
CEIL_GAP = 0.12        # keep this much air under whatever is above the ridge
SAG = 0.055            # the builder's own mid-row bulge, preserved

sc = bpy.context.scene
NAMES = sorted(o.name for o in sc.objects
               if o.type == 'MESH' and o.name.startswith("qm_awning_"))
assert NAMES, "no qm_awning_* in this blend"

# the ceiling probe must not stop on the awning itself
for nm in NAMES:
    sc.objects[nm].hide_viewport = True
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def ceiling(x, y, z0):
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, z0 + 0.02)),
                                            Vector((0, 0, 1)), distance=6.0)
    return (loc.z, ob.name) if hit else (None, None)


report = {}
for nm in NAMES:
    ob = sc.objects[nm]
    me = ob.data
    M = ob.matrix_world
    Mi = M.inverted()
    ws = [M @ v.co for v in me.vertices]
    ys = [w.y for w in ws]
    zs = [w.z for w in ws]
    y_lip, y_ridge = None, None
    # the three rows are (wall, mid, out) repeated: the ridge row is the one
    # whose z is highest, the lip row the lowest.  Read them off, never assume.
    z_hi, z_lo = max(zs), min(zs)
    ridge = [w for w in ws if abs(w.z - z_hi) < 1e-4]
    lip = [w for w in ws if abs(w.z - z_lo) < 1e-4]
    y_ridge = sum(w.y for w in ridge) / len(ridge)
    y_lip = sum(w.y for w in lip) / len(lip)
    depth = abs(y_ridge - y_lip)
    fall_now = z_hi - z_lo
    xs = [w.x for w in ws]
    # how much air is over the ridge, measured at three points along it
    caps = []
    for t in (0.15, 0.5, 0.85):
        x = min(xs) + (max(xs) - min(xs)) * t
        cz, cn = ceiling(x, y_ridge, z_hi)
        caps.append((cz, cn))
    lim = min([c[0] for c in caps if c[0] is not None], default=None)
    z_ridge_max = (lim - CEIL_GAP) if lim is not None else (z_hi + PITCH_WANT)
    fall_new = max(fall_now, min(PITCH_WANT, z_ridge_max - z_lo))
    report[nm] = dict(depth=round(depth, 3), fall_before=round(fall_now, 3),
                      fall_after=round(fall_new, 3), lip_z=round(z_lo, 4),
                      ceiling=(round(lim, 3) if lim is not None else None),
                      ceiling_obj=next((c[1] for c in caps if c[0] == lim), None))
    if ob.get(PROP):
        continue
    # rewrite z per vertex from its own fractional position along the canvas
    for v, w in zip(me.vertices, ws):
        f = 0.0 if depth < 1e-6 else abs(w.y - y_lip) / depth   # 0 at lip, 1 at ridge
        z = z_lo + fall_new * f
        if 0.2 < f < 0.8:
            z += SAG
        nw = Vector((w.x, w.y, z))
        v.co = Mi @ nw
    # winding: every face up.  `Mesh.flip_normals()` reverses the whole mesh,
    # which is exactly right here — the builder's bug is per-OBJECT (the sign of
    # y_out - y_wall), so an awning is 12/12 wrong or 12/12 right, never mixed.
    # It also leaves the POINT-domain `Col` layer alone; bmesh would round-trip
    # it, which weave_lib forbids on a vertex-coloured mesh.
    N = M.to_3x3().inverted().transposed()
    me.update()
    down = sum(1 for p in me.polygons if (N @ p.normal).normalized().z < 0)
    flipped = 0
    if down:
        assert down == len(me.polygons), \
            "%s has MIXED winding (%d/%d down) — flip_normals is the wrong tool" \
            % (nm, down, len(me.polygons))
        me.flip_normals()
        flipped = down
    me.update()
    ob[PROP] = 1
    report[nm]["flipped"] = flipped

for nm in NAMES:
    sc.objects[nm].hide_viewport = False

# ------------------------------------------------------------------ GATE ----
print("=" * 78)
print("qm_awning_fix — pitch raised at the RIDGE only; the lip is the headroom "
      "contract and does not move")
print("=" * 78)
bad = 0
for nm in NAMES:
    ob = sc.objects[nm]
    me = ob.data
    M = ob.matrix_world
    N = M.to_3x3().inverted().transposed()
    ws = [M @ v.co for v in me.vertices]
    z_lo = min(w.z for w in ws)
    z_hi = max(w.z for w in ws)
    up = sum(1 for p in me.polygons if (N @ p.normal).normalized().z > 0)
    r = report[nm]
    ok_lip = abs(z_lo - r["lip_z"]) < 1e-6
    ok_up = (up == len(me.polygons))
    if not (ok_lip and ok_up):
        bad += 1
    print("  %-14s lip %.4f %s   fall %.3f -> %.3f over %.2f m (%.1f deg)   "
          "up-faces %d/%d %s   ceiling %s @ %s"
          % (nm, z_lo, "OK" if ok_lip else "MOVED — REFUSED",
             r["fall_before"], round(z_hi - z_lo, 3), r["depth"],
             __import__("math").degrees(__import__("math").atan2(z_hi - z_lo,
                                                                max(r["depth"], 1e-6))),
             up, len(me.polygons), "OK" if ok_up else "BAD",
             r["ceiling"], r["ceiling_obj"]))
assert bad == 0, "%d awning(s) failed the gate" % bad

json.dump(dict(_doc=("GENERATED by tools/qm_awning_fix.py — the quay-market "
                     "awnings' pitch and winding. A CARRIER on the live master; "
                     "qm_build.py must not be re-run against it."),
               generator="tools/qm_awning_fix.py", pitch_want=PITCH_WANT,
               ceil_gap=CEIL_GAP, sag=SAG, awnings=report),
          open("/Users/junshernchan/projects/multiplayer-rpg/tools/blends/districts/"
               "qm_awning_fix.json", "w"), indent=1)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
