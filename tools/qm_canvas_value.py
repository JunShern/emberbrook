"""qm_canvas_value.py — THE CANVAS WAS BRIGHTER THAN EVERY SUNLIT STONE IN TOWN.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/qm_canvas_value.py -- [--canvas r,g,b] [save]

A CARRIER, NEVER A REBUILD (`qm_build.py` derives `mat_qm_cliff`, which
`t3_rock_projection` owns — round 5's time bomb).  `qm_build.py`'s `CANVAS_B`
carries the same number so a rebuild agrees.  IDEMPOTENT: it re-derives every
awning's whole `Col` layer from the two stripe colours it finds, so running it
twice is a no-op and running it after `qm_awning_relief` is safe.

WHY (round 9, measured through `dh_objmap`'s ray-derived mask on the SHIPPED
plates — the same pixels on both sides).  Round 8 fixed the awning's SHAPE and
its own receipt named the residual: two of three naive judge passes still said
"untextured" and "WHITE".  Round 9 measured what the frame wants, and the answer
is not a preference:

    crossing, qm_awning_0            478 rays   5.3 m   L p05 97.3  p50 159.2  p95 186.4
    crossing, everything else 2.6-10.6 m       1716 rays  L p05  3.2  p50  98.4  p95 131.7
    mat_qm_paving — THE TOWN'S OWN SUNLIT STONE, five cameras:
        crossing 117.5   loop-stairs 106.0   weave 107.6   lockhead 104.0   quay-west 99.8
        ... and its p95 never exceeds 138.1 on any of them.

So the canvas's MEDIAN sits above the p95 of every paved surface in Dellhollow,
its own 5th percentile equals the near field's MEDIAN, and 57.3% of it is above
L150 against 0.2-0.9% for the paving.  A cloth awning in the same light as the
stone under it may be lighter than the stone; it may not be the brightest large
object in the frame by a third of a level.

AND THE OTHER LEVER WAS REFUSED ON A MEASUREMENT, not on taste.  Round 8's
handover proposed a shorter stripe period on the grounds that "the in-frame
corner is two cream columns".  That was true of the SEVEN-column canvas it
measured and is FALSE of the thirteen-column one it shipped: projecting
`qm_awning_0`'s 39 vertices through crossing's own solved camera now puts
columns 07..12 in frame, and column 09 is the navy `STALLC[1]`
(0.068, 0.123, 0.191).  The plate agrees — the awning's own L runs 92.1 at the
0th percentile.  THE DARK STRIPE IS ALREADY IN THE PICTURE AND THE CORNER STILL
READS WHITE, because 57.3% of the canvas is above L150.  More stripes would add
more of a contrast that is already there; only the value moves the verdict.

THE NUMBER IS SWEPT, NOT DERIVED — AgX is not a power law and the canvas's own
relief means its normals vary, so the albedo -> displayed-L map was measured on
draft renders of crossing (1008x576 / 28 spp, the documented ruler) at three
rungs, and the shipped value is the one that lands the canvas inside the paving
band without crossing under it.  The sweep table is beside the constant below.
"""
import bpy, sys, os, json, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SAVE = "save" in argv


def _arg(f, d=None):
    return argv[argv.index(f) + 1] if f in argv else d


# THE SWEEP (crossing, draft 1008x576 / 28 spp, `qm_awning_0` read through its own
# ray-derived mask).  Target band: the town's sunlit stone, L p50 100-118 / p95 <= 138.
#   factor  canvas rgb                 canvas L p50   >L150
#   1.00    0.320, 0.295, 0.248        (see DAYLOG)
#   0.75    0.240, 0.221, 0.186
#   0.60    0.192, 0.177, 0.149
#   0.45    0.144, 0.133, 0.112
CANVAS_OLD = tuple(float(x) for x in _arg("--from", "0.320,0.295,0.248").split(","))
CANVAS_NEW = tuple(float(x) for x in _arg("--canvas", "0.144,0.133,0.112").split(","))
# A SECOND NUMBER ON THE SAME MATERIAL, and the control below is why it is here:
# at albedo 0.020 — sixteen times darker than the shipped cream, i.e. black paint —
# the canvas STILL reads L p50 104.2, because what is left is the Principled's
# default 0.5 Specular IOR Level (~4% reflectance) on a surface that catches the
# only direct light in that corner.  Woven canvas is a rough dielectric and 4% is
# a painted-panel number; `--spec` is the lever, `-1` leaves it alone.
SPEC = float(_arg("--spec", "-1"))
EPS = 1e-3


def close(a, b):
    return all(abs(a[i] - b[i]) < EPS for i in range(3))


def digest(obs):
    h = hashlib.sha256()
    for ob in obs:
        h.update(ob.name.encode())
        ca = ob.data.color_attributes.get("Col")
        if ca:
            for d in ca.data:
                h.update(("%.4f %.4f %.4f " % tuple(d.color[:3])).encode())
    return h.hexdigest()[:16]


AWN = sorted([o for o in bpy.data.objects if o.name.startswith("qm_awning_")],
             key=lambda o: o.name)
assert AWN, "no qm_awning_* in this blend"
print("DIGEST before %s  (%d awnings)  canvas %s -> %s"
      % (digest(AWN), len(AWN), CANVAS_OLD, CANVAS_NEW))

report = []
for ob in AWN:
    me = ob.data
    ca = me.color_attributes.get("Col")
    if not ca:
        print("SKIP %-14s no Col layer" % ob.name)
        continue
    NC = len(me.vertices) // 3
    assert NC % 2 == 1 and NC >= 5, "%s: %d columns is not 2n+1" % (ob.name, NC)
    n = (NC - 1) // 2
    cols = [tuple(round(c, 4) for c in ca.data[3 * k].color[:3]) for k in range(NC)]
    # The builder's own layout: column 1 is panel 0 and column 3 is panel 1, so
    # the two stripe colours are read off the mesh rather than off a table — a
    # carrier that assumed `STALLC` would break the one awning `restripe` moved.
    a, b = cols[1], cols[3]
    a2 = CANVAS_NEW if close(a, CANVAS_OLD) else a
    b2 = CANVAS_NEW if close(b, CANVAS_OLD) else b
    if a2 == a and b2 == b:
        print("SKIP %-14s neither stripe is the canvas cream (%s / %s)" % (ob.name, a, b))
        continue
    # THE GUARD ROUND 8 EARNED, AND PULLING THE VALUE WOULD HAVE RE-BROKEN IT.
    # `qm_awning_1`'s cloth IS the cream (`STALLC[3]` is bit-identical to the
    # constant partner), so round 8 gave it `CANVAS_ALT` (0.150, 0.128, 0.104) as
    # its second stripe.  Moving the cream DOWN to 0.144 puts those two colours
    # 0.006 apart — the one genuinely monochrome canvas in town, back again, by
    # the same mechanism and for the opposite reason.  A stripe that is not a
    # stripe is refused here rather than shipped: the partner is re-derived at
    # half the cream's value, keeping its own hue.
    if max(abs(a2[i] - b2[i]) for i in range(3)) < 0.03:
        old = b2
        b2 = tuple(round(c * 0.47, 4) for c in a2)
        print("PARTNER %-12s %s and %s are the same cloth after the pull — partner "
              "re-derived to %s (contrast %.2fx)"
              % (ob.name, a2, old, b2,
                 sum(a2) / max(sum(b2), 1e-6)))
    stripe = [a2 if k % 2 == 0 else b2 for k in range(n)]
    for j in range(NC):
        rib = (j % 2 == 0)
        k = j // 2
        if not rib:
            c = stripe[k]
        elif j == 0:
            c = stripe[0]
        elif j == NC - 1:
            c = stripe[n - 1]
        else:
            c = tuple((stripe[k - 1][i] + stripe[k][i]) / 2.0 for i in range(3))
        for r in range(3):
            ca.data[3 * j + r].color = (c[0], c[1], c[2], 1.0)
    report.append((ob.name, a, a2, b, b2))
    print("CANVAS %-14s stripes %s / %s -> %s / %s   (%d columns rewritten)"
          % (ob.name, a, b, a2, b2, NC))

if SPEC >= 0.0:
    m = bpy.data.materials.get("mat_qm_awning")
    assert m and m.use_nodes, "mat_qm_awning is missing or has no node tree"
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            s = n.inputs.get("Specular IOR Level") or n.inputs.get("Specular")
            assert s is not None, "no specular socket on mat_qm_awning"
            print("SPEC mat_qm_awning %.3f -> %.3f" % (s.default_value, SPEC))
            s.default_value = SPEC

print("DIGEST after  %s" % digest(AWN))
print("TOUCHED %d of %d awnings" % (len(report), len(AWN)))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN — pass `save` to write")
