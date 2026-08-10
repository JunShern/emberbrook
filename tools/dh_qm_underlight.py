"""dh_qm_underlight.py — THE QUAY-MARKET STAIR MASS IS A BACK FACE, NOT A SHADOW,
AND THE TOWN'S FRONTAGE-FILL RUN HAS A HOLE WHERE IT STANDS.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_qm_underlight.py -- [--dry] [save] [--shrink 3.0] [--cutoff 16.0]
  … -P tools/dh_qm_underlight.py -- revert save        # remove the cards again

WHAT IT MEASURED (round 10).  Round 9 handed over deep-stairs darkness at 3/3 naive
judge passes — "extremely harsh cast shadows completely obscure the pathing",
"pitch-black cast shadow completely obscures the passage and stairwell cut into the
cliff face".  Put on the geometry (`dh_objmap box`), the box all three drew is

    49.0%  qm_stair_underworks   mat_qm_stone_dark   27.3 m
    12.2%  seam_bank             mat_rock            28.0 m
     9.7%  wf_ground             mat_rock            31.5 m

`qm_stair_underworks` is 5.98% of the deep-stairs frame at L p05 4.1 / p50 10.0, and
the SAME material reads p50 60.4 at waterfront, 42.9 at lockhead and 36.6 at
loop-stairs — so the material is capable and this face is unlit.

**THE "CAST SHADOW" IS REFUTED WITH A NUMBER.**  440 samples on the visible face,
each shadow-rayed to every light:

    KEY_slip          reached 247/440   plate L p50 on reached 12.1 · on blocked  7.3
    KEY_gorge_dam_0   reached 403/440   plate L p50 on reached  9.0 · on blocked  9.5
    SUN_key           reached   0/440   383 of the 440 blocked by qm_stair_underworks
    KEY_gorgewall     reached   0/440

A cast shadow is a boundary.  There is no boundary: the pixels a light REACHES are
4.8 levels of 255 brighter than the ones it does not, and for the widest-reaching
light the difference INVERTS.  The mass is uniformly dark because its visible faces
point away from every source — 87% of the sun rays are blocked by its OWN BODY.
That also refutes the obvious fix twice over: raising `KEY_slip` is "adjusting an
existing light", which this town's night-grade doctrine records as never having
moved it, and raising `KEY_gorgewall` was rejected once already because more light
prints the rock's 16.7 m texture period as a quilt.

THE LEVER IS THE ONE THE NEXT DISTRICT ALREADY USES, AND IT IS MISSING HERE.
`weave_light.py` fills exactly this class of surface with `KEYW_CLIFF_`: small
horizontal cards standing GORGE-WARD of the frontages, firing back at the cliff
(-y).  Their safety is geometric, not a wattage — anything further out in +y sits
BEHIND the emitter, where the card's own cosine is negative and the contribution is
zero by construction.  That run starts at x = 46.0 and goes east.  The quay-market
stair mass stands at x 34.7..38.6, in the gap, and the census says so:

    CLIFF_BOUNCE      (x 28.0, the 120 W parent) reached  10/440 at 0.0033
    KEYW_CLIFF_0      (x 46.0, 13.3 W after shrink)      166/440 at 0.0057

So this adds `KEYQ_UNDER_*` — the same `CLIFF_BOUNCE` card, same shrink, same
cutoff, same -y rotation — over the gap.  ADDING A SOURCE, which is what this town
has always responded to, in an existing named class, at a measured hole in its run.

POSITIONS ARE DERIVED, NOT AUTHORED.  The run is laid along the subject's own world
bounding box in x, at a y taken from the mass's own +y face plus a standoff, at the
mass's own mid z.  Re-running after the geometry moves moves the cards.

WHAT IT ASSERTS:
  * the cards stand OUTBOARD in y of every vertex of the subject (otherwise the
    cosine argument that makes them safe does not hold);
  * `use_shadow = False` on every card — a faked bounce must not also cast;
  * removing and re-adding is exact: `revert` deletes precisely the `KEYQ_UNDER_`
    namespace and nothing else, and a second run replaces rather than stacks.
"""
import bpy, sys, math
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "--dry" in argv
REVERT = "revert" in argv


def opt(f, d):
    return type(d)(argv[argv.index(f) + 1]) if f in argv else d


PREFIX = "KEYQ_UNDER_"
SRC = "CLIFF_BOUNCE"
SUBJECT = "qm_stair_underworks"
SHRINK = opt("--shrink", 3.0)
CUTOFF = opt("--cutoff", 16.0)
STANDOFF = opt("--standoff", 4.5)     # metres gorge-ward (+y) of the mass's own face
N = opt("--n", 3)

# ------------------------------------------------------------------- revert ----
old = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
if old:
    print("removing %d existing %s* card(s)" % (len(old), PREFIX))
    for o in old:
        d = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if d.users == 0:
            bpy.data.lights.remove(d)
if REVERT:
    if SAVE:
        bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
    else:
        print("reverted in memory (pass `save`)")
    sys.exit(0)

# ------------------------------------------------------------------ derive -----
sub = bpy.data.objects[SUBJECT]
ws = [sub.matrix_world @ v.co for v in sub.data.vertices]
x0, x1 = min(v.x for v in ws), max(v.x for v in ws)
y0, y1 = min(v.y for v in ws), max(v.y for v in ws)
z0, z1 = min(v.z for v in ws), max(v.z for v in ws)
print("%s world bbox  x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f"
      % (SUBJECT, x0, x1, y0, y1, z0, z1))

cy = y1 + STANDOFF
cz = z0 + (z1 - z0) * 0.55
AT = [(x0 + (x1 - x0) * (i + 0.5) / N, cy, cz) for i in range(N)]
for p in AT:
    print("   card at (%.2f, %.2f, %.2f)" % p)

# The cosine argument, asserted rather than asserted-in-a-comment: every vertex of
# the subject must be on the -y side of the cards, or a card lights nothing.
assert cy > y1, "card row is inside the subject in y (%.2f <= %.2f)" % (cy, y1)

src = bpy.data.objects[SRC]
coll = src.users_collection[0]
print("source %s: %s %.1f W, size %.2f, collection %s"
      % (SRC, src.data.type, src.data.energy, src.data.size, coll.name))

if DRY:
    print("--dry: nothing added")
    sys.exit(0)

for i, p in enumerate(AT):
    d = src.data.copy()
    d.size /= SHRINK
    d.size_y /= SHRINK
    d.energy /= SHRINK * SHRINK
    d.use_shadow = False                 # a faked card must not also cast
    d.use_custom_distance = True
    d.cutoff_distance = CUTOFF
    ob = bpy.data.objects.new("%s%d" % (PREFIX, i), d)
    d.name = ob.name
    ob.location = Vector(p)
    ob.rotation_euler = Euler((-math.pi / 2, 0.0, 0.0))   # horizontal, firing -y
    coll.objects.link(ob)

made = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
assert len(made) == N, "expected %d cards, made %d" % (N, len(made))
for o in made:
    assert o.data.use_shadow is False
    assert o.location.y > y1
print("ADDED %d %s* cards at 1/%.0f size, 1/%.0f power, cutoff %.1f m"
      % (len(made), PREFIX, SHRINK, SHRINK * SHRINK, CUTOFF))
print("   each %.2f W, size %.2f" % (made[0].data.energy, made[0].data.size))

if SAVE:
    bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
