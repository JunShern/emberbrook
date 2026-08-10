"""emb_padcoplanar.py — TWO WALK PADS AT EXACTLY THE SAME HEIGHT RENDER AS A BLACK HOLE.

    Blender -b tools/blends/emberbrook-dressed.blend --python-exit-code 1 \
        -P tools/emb_padcoplanar.py -- [save] [revert save] [--tol 0.002] [--nudge 0.004]

RUN THIS AGAINST THE PLATE MASTER ONLY (`emberbrook-dressed.blend`).  It moves the
SMALLER member of each coincident pair DOWN by `--nudge` (4 mm) and nothing else, so it
changes THE PICTURE and cannot reach the walk network: `emb-cine/scene.glb` is exported
from `emberbrook-master.blend` and `emb-townwalk` from `emberbrook-realtime.blend`,
neither of which this file touches.

WHY A NUDGE AND NOT `hide_render`, WHICH IS WHAT THE CONTROL USED.  The control hid ONE
pad and proved the mechanism, but the census then found **55 coincident pairs town-wide**
and most are road-ribbon segments overlapping each other.  A "more than half swallowed"
rule would have DELETED THE UNCOVERED REMAINDER — `walk_pad_grandmothers-bench` is only
65% swallowed, so hiding it removes 1.5 m2 of drawn paving, and an L-segment at 51% would
leave a hole in a road.  4 mm is 6.7x Cycles' own ray epsilon at this town's distance from
the world origin (~6e-4 m at |P| ~ 60 m), so it breaks the coincidence with certainty
while nothing stops being drawn anywhere.

=============================== WHAT WAS MEASURED ================================

The red-team board's item #2 (round 1, 2026-08-09): *"a completely pitch-black rectangular
block sits on the path, appearing as broken geometry"* — three independent naive looks at
`homerow`, plus a fourth finding reporting grandmother's bench ABSENT.  In the box:
L p50 1.0/255, 53.9% of pixels <= 8, saturation 0.000 against a ring median of 53.5.

WHAT IT IS NOT, each ruled out on an instrument:
  * NOT a floating card, NOT dressing scatter — `emb_plate_object` puts the plate's own
    depth surface on the pad's own top at **residual p50 0.00 m, p90 0.01 m**.
  * NOT a black material — the same pad reads L50 45.6 where it is lit.
  * NOT the lamp's cast shadow, and NOT the sealed-lamp defect `emb_lightbodies` fixes:
    it SURVIVES the unsealing, and is more conspicuous afterwards because the paving
    around it is now lit.
  * NOT a sun shadow you could light your way out of: `EMB_sun` sits at **10.0 degrees**
    elevation and is blocked at **108 of 108** samples across the whole region, so nothing
    there is sun-lit either way.

WHAT IT IS.  Two walk pads occupy the same plane and overlap:

    walk_pad_lake-home           x[35.592, 38.592]  y[47.984, 50.984]  z 1.930..2.070
    walk_pad_grandmothers-bench  x[34.600, 37.400]  y[49.400, 50.950]  z 1.930..2.070

— identical z to the millimetre, overlapping 1.81 x 1.55 m.  Coincident coplanar
surfaces mutually occlude, and the black region in the plate is not a rectangle at all:
its silhouette is the STEPPED UNION of those two footprints, which is what named the
cause.  THE CONTROL (draft 1008x576/28 spp at homerow's own shipped grade, one
`hide_render` flag and nothing else): the box goes **p50 57.9 -> 83.5 and 40.7% of pixels
<= 8/255 -> 0.1%**.  The hole is gone and the bench is legible.

THE ROOT FIX IS NOT HERE.  `emb_blockout` emitted two threshold pads at one landmark's
own height with no overlap test; that is where a second pad should never be emitted, and
it is round 2's item.  This is the carrier that stops the town shipping a black hole in
the meantime, and it REFUSES to guess: only a pad that is (a) coplanar within `--tol`
and (b) more than half swallowed in plan by a larger pad is hidden, and every candidate
pair is PRINTED whether it is acted on or not.
"""
import bpy, sys, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
TOL = float(argv[argv.index("--tol") + 1]) if "--tol" in argv else 0.002
NUDGE = float(argv[argv.index("--nudge") + 1]) if "--nudge" in argv else 0.004
PROP = "embpad"
sc = bpy.context.scene

if REVERT:
    st = sc.get(PROP)
    assert st, "this blend carries no '%s' snapshot — nothing to revert" % PROP
    for nm, v in json.loads(st).items():
        o = sc.objects.get(nm)
        if o:
            o.location.z = v
    del sc[PROP]
    print("reverted")
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

assert not sc.get(PROP), ("this blend already carries the '%s' snapshot — run "
                          "`-- revert save` first" % PROP)

PADS = []
for o in sc.objects:
    if o.type != 'MESH' or not o.name.startswith("walk_") or o.hide_render:
        continue
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    PADS.append((o, min(w.x for w in ws), max(w.x for w in ws), min(w.y for w in ws),
                 max(w.y for w in ws), max(w.z for w in ws),
                 (max(w.x for w in ws) - min(w.x for w in ws)) *
                 (max(w.y for w in ws) - min(w.y for w in ws))))
print("%d walk meshes; looking for coplanar (|dz| <= %.4f m) overlapping pairs" % (len(PADS), TOL))

hide, pairs = {}, 0
for i, a in enumerate(PADS):
    for b in PADS[i + 1:]:
        if abs(a[5] - b[5]) > TOL:
            continue
        ox = min(a[2], b[2]) - max(a[1], b[1])
        oy = min(a[4], b[4]) - max(a[3], b[3])
        if ox <= 0 or oy <= 0:
            continue
        area = ox * oy
        small, big = (a, b) if a[6] <= b[6] else (b, a)
        frac = area / max(1e-9, small[6])
        pairs += 1
        print("  %-34s x %-34s  overlap %.2f x %.2f m = %.2f m2 (%.0f%% of the smaller), "
              "dz %.4f  ->  drop %s by %.3f m"
              % (a[0].name[:34], b[0].name[:34], ox, oy, area, 100 * frac,
                 abs(a[5] - b[5]), small[0].name, NUDGE))
        if small[0].name not in hide:
            hide[small[0].name] = small[0].location.z

assert pairs, ("no coplanar overlapping walk pair found — an instrument that finds "
               "nothing must be able to prove it could have found something; this blend "
               "is either already carried or is not Emberbrook")
sc[PROP] = json.dumps(hide)
for nm in hide:
    sc.objects[nm].location.z -= NUDGE
print("%d coplanar overlapping pair(s); %d mesh(es) dropped %.3f m IN THE PLATE MASTER "
      "ONLY (the walk network is exported from the master and the realtime tier, neither "
      "of which this file touches): %s"
      % (pairs, len(hide), NUDGE, ", ".join(sorted(hide))))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
