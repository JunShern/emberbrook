"""master_pool_fix.py — bring water_pool-downstream to the level the MAP rules.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_pool_fix.py -- [save]

The map (topology truth) puts `pool-downstream` at level -3.80 — the level the
2026-07-29 ruling created when it took `dam-five`'s drop from 1.8 to 4.0 so the
kit's 4.4 m breast wheels read at true scale.  The saved master had its surface at
-2.80, and the slab was a ZERO-THICKNESS sheet, because `locksfoot_build.py` wrote
the world level straight into `v.co.z` on an object whose origin sits at z -1.8
with a 0.2 z scale (see `boatyard_lib.reseat_slab`, which is the durable fix and is
what this script calls — nothing is re-implemented here).

Everything else in the district was already built for the TRUE -3.80: the tail race
boils sit at -3.90, the far-bank toe keeps a lip under -3.80, and the wheels are
axled at -1.55 to span down to -3.75.  Against the wrong surface all of that was
about a metre under water.  So this corrects the one object and then VERIFIES the
consequences it was supposed to have, instead of asserting the number it just wrote.
"""
import bpy, sys, math

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import world_bbox, reseat_slab

SAVE = "save" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
MAP = "/Users/junshernchan/projects/multiplayer-rpg/public/townmap/dellhollow.map.json"
POOL_THICK = 0.40
TOL = 1e-6

import json
m = json.load(open(MAP))
pools = {p["id"]: p for p in m["river"]["pools"]}
dams = {d["id"]: d for d in m["river"]["dams"]}
WANT = pools["pool-downstream"]["level"]
HEAD = pools["pool-mid"]["level"]
DROP = dams["dam-five"]["drop"]

print("=" * 78)
print("POOL DEPTH FIX — the map is the authority")
print("=" * 78)
print("  map: pool-mid %.2f, pool-downstream %.2f, dam-five drop %.2f"
      % (HEAD, WANT, DROP))
assert abs((HEAD - WANT) - DROP) < 1e-9, \
    "the MAP disagrees with itself: %.2f - %.2f != %.2f" % (HEAD, WANT, DROP)

ob = bpy.data.objects["water_pool-downstream"]
b0 = world_bbox(ob)
print("\n  before: world z %.3f..%.3f (thickness %.3f)  origin_z=%+.3f  scale=%s"
      % (b0[4], b0[5], b0[5] - b0[4], ob.location.z,
         tuple(round(s, 3) for s in ob.scale)))
print("          surface is %+.2f m off the map's %.2f"
      % (b0[5] - WANT, WANT))

b1 = reseat_slab(ob, WANT, POOL_THICK)
print("  after : world z %.3f..%.3f (thickness %.3f)  origin_z=%+.3f  scale=%s"
      % (b1[4], b1[5], b1[5] - b1[4], ob.location.z,
         tuple(round(s, 3) for s in ob.scale)))
assert abs(b1[5] - WANT) < TOL, "surface %.4f != map %.4f" % (b1[5], WANT)
assert abs((b1[5] - b1[4]) - POOL_THICK) < TOL, "slab thickness wrong"
assert abs(b1[0] - b0[0]) < TOL and abs(b1[1] - b0[1]) < TOL, "plan x extent moved"
assert abs(b1[2] - b0[2]) < TOL and abs(b1[3] - b0[3]) < TOL, "plan y extent moved"
print("  -> surface EXACTLY on the map level, plan extent unchanged (x %.1f..%.1f, "
      "y %.1f..%.1f)" % (b1[0], b1[1], b1[2], b1[3]))

# ---------------------------------------------------------- what it was for
print("\n  the consequences the deepening was ruled FOR:")
wheels = sorted(o for o in (x.name for x in bpy.data.objects) if o.startswith("lf_wheel_")
                and "brg" not in o)
for n in wheels:
    w = world_bbox(bpy.data.objects[n])
    dia = w[5] - w[4]
    print("    %-14s z %.3f..%.3f  (dia %.2f m)  bottom sits %+.3f m vs the tail water "
          "(a breast wheel wants ~0: it takes water at the crest and its sole just "
          "grazes the tail), %+.3f m over the tail bed"
          % (n, w[4], w[5], dia, w[4] - WANT, w[4] - (-7.30)))
    assert w[4] > WANT - 0.05, "%s dips below the tail water" % n
    assert dia > 4.0, "%s is not a true-scale 4.4 m wheel (%.2f)" % (n, dia)

for n in ("lf_dam_boil", "lf_dam_wall", "lf_dam_crest"):
    o = bpy.data.objects.get(n)
    if o is None:
        continue
    w = world_bbox(o)
    print("    %-14s z %.3f..%.3f" % (n, w[4], w[5]))
boil = bpy.data.objects.get("lf_dam_boil")
if boil is not None:
    w = world_bbox(boil)
    assert w[4] < WANT < w[5], \
        "the tail race boil (z %.2f..%.2f) does not BREAK the %.2f surface " \
        "(finding 86)" % (w[4], w[5], WANT)
    print("    -> the boil straddles the new surface, so it breaks it (finding 86)")

bed = world_bbox(bpy.data.objects["lf_riverbed_tail"])
print("    %-14s z %.3f..%.3f  -> %.2f m of water column under the surface"
      % ("lf_riverbed_tail", bed[4], bed[5], WANT - bed[5]))
assert bed[5] < WANT, "the tail bed pokes through its own pool"

print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("not saved")
