"""dh_veg_kit.py — TWO DISTRICTS INVENTED THEIR OWN GROUNDCOVER AND THE TOWN ALREADY
HAD A KIT.  A CARRIER ONTO THE LIVE MASTER, NEVER A DISTRICT REBUILD.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_veg_kit.py -- [--dry] [save] [--force]

WHAT IT MEASURED FIRST (round 11, one property probe over the master).  385 meshes in
Dellhollow wear `mat_grass` / `mat_fern`.  Their geometry falls into exactly four
shapes, and two of them are not the kit:

    160 verts / 64 faces   x150   THE TUFT KIT     Col yes  UV yes
    110 verts / 44 faces   x131   THE FERN KIT     Col yes  UV yes
      8 verts /  6 faces   x 78   veg_lf_fern_*    Col NO   UV NO   <- an obox(): A BOX
      8 verts /  2 faces   x 26   veg_lk_tuft_*    Col NO   UV NO   <- two crossed quads

**THAT 78 + 26 IS ROUND 10's "104 veg_lf_fern_*".**  It was one orphan set counted
under one prefix, and it is two districts: `locksfoot_build.py` line 1329 builds its
planting with `obox()`, and `lk_build.py` line 1648 builds its own with two crossed
quads UNDER A COMMENT THAT SAYS IT IS COPYING THE FAMILY NEXT DOOR ("a district that
invents its own foliage grammar reads as a different game from the district beside
it").  The comment describes the intent; the artifact is 8 verts and 2 faces against a
kit of 160 and 64.  Both classes are also missing the `Col` attribute every other
member has, which is why round 10 could not ship their colour: a coloured box is a
lime block, and a gradient does not make a box a plant.

WHY A COPY AND NOT NEW GEOMETRY.  Round 10's own rim-clump lesson is MATCH THE KIT'S
OWN NUMBER, DO NOT INVENT A PROJECTION — it cost a whole bake to learn.  There is a
kit here and it is the majority of the class, so nothing is authored: each orphan's
mesh data is replaced by a COPY of the town's own donor tuft/fern, which is still in
the master as `v10_src_tuft*` (and which no camera can see: the ray census puts it in
NONE of the fifteen frames).

THREE THINGS THAT ARE DERIVED RATHER THAN CHOSEN, each with the measurement behind it:

  * WHICH KIT.  By the orphan's own material — `mat_fern` -> the 110/44 fern donor,
    `mat_grass` -> the 160/64 tuft donor.  That is the same pairing every healthy
    family in town already uses.
  * HOW BIG.  A UNIFORM scale, the LARGEST that fits inside the orphan's OWN world
    bounding box.  Uniform because a plant stretched to a box's proportions is a
    stretched plant; inside because the box's footprint is what `clear_box()` cleared
    when the district was built, so a replacement that stays inside it cannot
    introduce an intersection the builder had refused.  Asserted, not hoped.
  * WHERE THE ORIGIN GOES — AND IT IS NOT A CONVENTION, IT IS THE COLOUR, SO IT IS
    SOLVED.  `mat_grass`/`mat_fern` drive their Color Ramp from Texture Coordinate
    OBJECT -> Separate XYZ.Z -> Map Range `From Min 0.0, From Max 0.45` (grass) /
    `0.55` (fern), CLAMPED.  The origin therefore decides how much of every plant
    clamps to the dark end, and "the base" and "the middle" are both guesses: measured
    by Cycles bake, base-at-zero put `mat_grass` 35% bright and centred-on-zero put it
    43% dark, and drawing the HEIGHT from the kit's own distribution moved it by
    almost nothing (61% on BOTH materials, the same factor twice).
    Because that chain is arithmetic it is evaluated IN NUMPY here and the offset is
    solved to a thousandth of a metre.  The model was checked against the thing it
    replaces before being trusted — predicted (0.0378, 0.0743, 0.0289) and
    (0.0656, 0.0848, 0.0335) against a Cycles EMIT bake of the same meshes at
    (0.0378, 0.0742, 0.0289) and (0.0653, 0.0845, 0.0334).
    AND THE TARGET IS THE HEALTHY FAMILY'S SHIPPED `Col`, NOT WHAT THE RAMP PREDICTS
    FOR IT: those differ by 1.36x (fern stored 0.0634 vs 0.0454 predicted, grass
    0.1214 vs 0.0895).  After `master_survivability` the Base Color is read from the
    `surv_col` VERTEX ATTRIBUTE and the ramp is only a bake source — so the stored
    colour is what ships, and the ramp is not a second opinion about it.

ORDER, AND IT IS LOAD-BEARING: this runs BEFORE `tools/dh_rimclump_col.py`, and that
tool's `HOLD` entry for `mat_grass`/`mat_fern` must be deleted in the same window.
Geometry first, then the colour it was owed.  The copied meshes' `Col` attribute is
DELETED on purpose so the colour tool still sees them as orphans and bakes them at
their new object-space z rather than inheriting the donor's.

IT IS IDEMPOTENT BY REFUSING: a target is only rewritten if its mesh still carries the
box (8/6) or crossed-quad (8/2) signature.  Re-running is a no-op that says so.
`--force` overrides for a deliberate re-derive.

THE DISTRICT BUILDERS ARE NOT EDITED.  Re-running `locksfoot_build.py` or
`lk_build.py` rebuilds a whole dressed district and each is a function of town
geometry that has moved since, so both carry a pointer to this file instead.  That is
the same deal `gate_rimchop`/`gate_roadchop` have with `gate_build`.
"""
import bpy, sys, math, hashlib
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "--dry" in argv
FORCE = "--force" in argv

TARGET_PREFIXES = ("veg_lf_fern_", "veg_lk_tuft_")
ORPHAN_SIG = {(8, 6), (8, 2)}          # obox, and two crossed quads
KIT_SIG = {"fern": (110, 44), "tuft": (160, 64)}
MAT_KIT = {"mat_fern": "fern", "mat_grass": "tuft"}


def sig(me):
    return (len(me.vertices), len(me.polygons))


def local_co(ob):
    me = ob.data
    v = np.zeros(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", v)
    return v.reshape(-1, 3)


def world_bbox(ob):
    v = local_co(ob)
    M = np.array(ob.matrix_world)
    w = v @ M[:3, :3].T + M[:3, 3]
    return w.min(axis=0), w.max(axis=0)


# --------------------------------------------------------------- the donors ---
donors = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for kind, s in KIT_SIG.items():
        if o.name.startswith("v10_src_tuft") and sig(o.data) == s:
            donors[kind] = o
if set(donors) != set(KIT_SIG):
    raise SystemExit("REFUSE: donors not found in the master — have %s, want %s"
                     % (sorted(donors), sorted(KIT_SIG)))
# ---------------------------------------- the kit's own origin fraction, per material
# Measured, never chosen: of the meshes already wearing this material AND carrying
# `Col`, the median share of the plant that sits BELOW its own origin.  That share is
# the share that clamps to the dark end of the ramp, so it is the colour.
KIT_FRAC = {}
KIT_H = {}
for mname in MAT_KIT:
    fr, hs = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith(TARGET_PREFIXES):
            continue
        if mname not in [s.material.name for s in o.material_slots if s.material]:
            continue
        if "Col" not in o.data.color_attributes:
            continue
        z = local_co(o)[:, 2]
        h = float(z.max() - z.min())
        if h > 1e-4:
            fr.append(float(-z.min()) / h)
            hs.append(h)
    if not fr:
        raise SystemExit("REFUSE: no healthy %s mesh to take an origin fraction from" % mname)
    KIT_FRAC[mname] = float(np.median(fr))
    KIT_H[mname] = sorted(hs)
    print("KIT %-10s origin fraction %.3f · height p05/p50/p95 %.2f/%.2f/%.2f "
          "(%d healthy meshes carrying Col)"
          % (mname, KIT_FRAC[mname], *np.percentile(hs, [5, 50, 95]), len(fr)))

for kind, o in sorted(donors.items()):
    lo, hi = local_co(o).min(axis=0), local_co(o).max(axis=0)
    print("DONOR %-5s %-22s %d verts / %d faces  local bbox %s..%s  uv %s"
          % (kind, o.name, len(o.data.vertices), len(o.data.polygons),
             tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi),
             [l.name for l in o.data.uv_layers]))

# ---------------------------------------------------------------- the census --
targets, already, refused = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(TARGET_PREFIXES):
        continue
    mats = [s.material.name for s in o.material_slots if s.material]
    kind = next((MAT_KIT[m] for m in mats if m in MAT_KIT), None)
    if kind is None:
        refused.append((o.name, "no mat_fern/mat_grass slot (%s)" % mats)); continue
    if sig(o.data) not in ORPHAN_SIG and not FORCE:
        already.append(o.name); continue
    mname = next(m for m in mats if m in MAT_KIT)
    targets.append((o, kind, mname))

print("== dh_veg_kit ==")
print("orphan groundcover meshes to re-shape : %d" % len(targets))
byk = {}
for o, k, _m in targets:
    byk[k] = byk.get(k, 0) + 1
print("   by kit %s" % byk)
byp = {}
for o, k, _m in targets:
    p = o.name.rsplit("_", 1)[0]
    byp[p] = byp.get(p, 0) + 1
print("   by prefix %s" % byp)
if already:
    print("already kit-shaped (skipped, pass --force to re-derive) : %d" % len(already))
for n, why in refused:
    print("   REFUSED %s : %s" % (n, why))
if not targets:
    print("nothing to do"); sys.exit(0)

if DRY:
    print("--dry: nothing written")
    sys.exit(0)

# ----------------------------------------------------------------- the carry --
# PASS 1 builds every replacement with its BASE AT LOCAL ZERO and holds it; the z
# offset is the only thing left to decide and it is SOLVED in between, not chosen.
built = []
for ob, kind, mname in targets:
    if "dh_veg_kit_box" in ob:                 # a re-derive uses the ORIGINAL envelope
        b = list(ob["dh_veg_kit_box"])
        lo, hi = np.array(b[:3], float), np.array(b[3:], float)
    else:
        lo, hi = world_bbox(ob)
        ob["dh_veg_kit_box"] = [float(x) for x in list(lo) + list(hi)]
    size = hi - lo
    ctr = (lo + hi) * 0.5
    dn = donors[kind]
    dv = local_co(dn)
    dlo, dhi = dv.min(axis=0), dv.max(axis=0)
    dsz = np.maximum(dhi - dlo, 1e-6)
    # HEIGHT COMES FROM THE KIT, NOT FROM THE BOX.  Fitting the largest uniform scale
    # into each district's own envelope made plants 61% of the healthy family's baked
    # colour on BOTH materials — the same factor twice, which is the signature of a
    # SIZE difference and not an origin one (a base-dark/tip-light ramp with a clamped
    # 0..0.45 domain reads a short plant dark).  So the height is drawn deterministically
    # from the healthy family's OWN height distribution and only ever scaled DOWN to fit
    # the envelope its builder cleared.
    h = int(hashlib.sha256(ob.name.encode()).hexdigest()[:8], 16)
    want_h = KIT_H[mname][(h >> 16) % len(KIT_H[mname])]
    s = want_h / float(dhi[2] - dlo[2])
    s = min(s, float(np.min(size / dsz)))       # never larger than the cleared box
    # deterministic yaw off the object's own name — a row of identical plants all
    # facing one way is the tell that they were placed by a loop
    a = (h % 3600) / 3600.0 * 2.0 * math.pi
    ca, sa = math.cos(a), math.sin(a)
    # x/y centred on the donor's middle; z measured from the plant's own BASE for now
    off = np.array([(dlo[0] + dhi[0]) * 0.5, (dlo[1] + dhi[1]) * 0.5, dlo[2]])
    v = (dv - off) * s
    x = v[:, 0] * ca - v[:, 1] * sa
    y = v[:, 0] * sa + v[:, 1] * ca
    v = np.stack([x, y, v[:, 2]], axis=1)
    # A UNIFORM SCALE CHOSEN ON THE UNROTATED BOX CAN STILL BREAK IT ONCE ROTATED —
    # the plant is not axis-aligned and its own footprint is not square.  Shrink to
    # the rotated extent rather than assert on it; the footprint the district
    # builder cleared is the constraint, and the yaw is a free choice.
    ext = v.max(axis=0) - v.min(axis=0)
    fit = float(np.min(size / np.maximum(ext, 1e-6)))
    if fit < 1.0:
        v *= fit
        s *= fit
        ext = v.max(axis=0) - v.min(axis=0)
    assert (ext <= size + 1e-6).all(), (
        "%s: kit copy %s exceeds the box it replaces %s" % (ob.name, ext, size))

    built.append((ob, kind, mname, v, lo, ctr, size, s))

# ------------------------------------- SOLVE THE ORIGIN OFFSET, PER MATERIAL ----
# `mat_grass`/`mat_fern` are `Texture Coordinate OBJECT -> Separate XYZ.Z ->
# Map Range(0, FromMax, CLAMPED) -> a two-stop Color Ramp`, which is arithmetic, so
# the baked colour can be EVALUATED IN NUMPY instead of bisected by Cycles bakes.
# Verified against the real thing before it was trusted: predicted (0.0378, 0.0743,
# 0.0289) / (0.0656, 0.0848, 0.0335) against a Cycles EMIT bake of the same meshes at
# (0.0378, 0.0742, 0.0289) / (0.0653, 0.0845, 0.0334) — four decimals on both.
#
# AND THE TARGET IS THE HEALTHY FAMILY'S SHIPPED `Col`, NOT WHAT THE RAMP SAYS ABOUT
# IT.  Those two differ by 1.36x (fern stored 0.0634 against 0.0454 predicted, grass
# 0.1214 against 0.0895), which is a fact worth stating: after
# `master_survivability`, Base Color is read from the `surv_col` VERTEX ATTRIBUTE and
# the ramp is only ever a bake source, so the stored colour is what ships and the
# ramp is not a second opinion about it.
def _ramp(m):
    nt = bpy.data.materials[m].node_tree
    mr = [n for n in nt.nodes if n.type == 'MAP_RANGE'][0]
    cr = nt.nodes["Color Ramp"]
    return (float(mr.inputs['From Max'].default_value),
            np.array(cr.color_ramp.elements[0].color[:3]),
            np.array(cr.color_ramp.elements[1].color[:3]))


def _loopz(dn, v):
    lv = np.zeros(len(dn.data.loops), dtype=np.int32)
    dn.data.loops.foreach_get("vertex_index", lv)
    return v[lv, 2]


HEALTH = {}
for mname in MAT_KIT:
    acc = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith(TARGET_PREFIXES):
            continue
        if mname not in [sl.material.name for sl in o.material_slots if sl.material]:
            continue
        ca = o.data.color_attributes.get("Col")
        if ca is None:
            continue
        c = np.zeros(len(ca.data) * 4, dtype=np.float32)
        ca.data.foreach_get("color", c)
        acc.append(c.reshape(-1, 4)[:, :3].mean(axis=0))
    HEALTH[mname] = np.mean(acc, axis=0)

SHIFT = {}
for mname in MAT_KIT:
    fm, c0, c1 = _ramp(mname)
    zs = [_loopz(donors[k], v) for _o, k, m, v, _l, _c, _s, _sc in built if m == mname]
    tgt = HEALTH[mname]
    best = None
    for d in np.arange(-0.60, 0.31, 0.005):     # metres the plant is pushed DOWN
        a = np.mean([(c0 + np.clip((z + d) / fm, 0, 1)[:, None] * (c1 - c0)).mean(axis=0)
                     for z in zs], axis=0)
        e = float(np.abs(a / np.maximum(tgt, 1e-6) - 1).mean())
        if best is None or e < best[0]:
            best = (e, float(d), a)
    SHIFT[mname] = best[1]
    print("SOLVED %-10s origin offset %+.3f m -> predicted Col (%.4f, %.4f, %.4f) "
          "against the healthy family's own (%.4f, %.4f, %.4f), %.1f%% off"
          % (mname, best[1], *best[2], *tgt, 100 * best[0]))

# --------------------------------------------------------- PASS 2: write it out --
made = 0
scales = []
for ob, kind, mname, v, lo, ctr, size, s in built:
    dn = donors[kind]
    v = v.copy()
    v[:, 2] += SHIFT[mname]
    me = bpy.data.meshes.new(ob.data.name + "_kit")
    faces = [tuple(p.vertices) for p in dn.data.polygons]
    me.from_pydata([tuple(p) for p in v], [], faces)
    me.update()
    # the kit's UV, rebuilt loop for loop (the donor and the copy share topology)
    if dn.data.uv_layers:
        src = dn.data.uv_layers[0]
        uv = np.zeros(len(dn.data.loops) * 2, dtype=np.float32)
        src.data.foreach_get("uv", uv)
        lay = me.uv_layers.new(name=src.name)
        lay.data.foreach_set("uv", uv)
    for slot in ob.material_slots:
        me.materials.append(slot.material)
    old = ob.data
    ob.data = me
    # the plant's own base sits on the bottom of the envelope its builder cleared
    ob.location = Vector((float(ctr[0]), float(ctr[1]),
                          float(lo[2] - v[:, 2].min())))
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    # A COPIED `Col` WOULD BE THE DONOR'S, BAKED AT THE DONOR'S OWN Z.  Leave the
    # mesh an orphan so dh_rimclump_col bakes it where it now stands.
    for ca_ in list(me.color_attributes):
        me.color_attributes.remove(ca_)
    scales.append(s)
    made += 1

print("RE-SHAPED %d meshes  uniform scale p05/p50/p95 %.3f / %.3f / %.3f"
      % (made, float(np.percentile(scales, 5)), float(np.percentile(scales, 50)),
         float(np.percentile(scales, 95))))
post = {}
for o, k, _m in targets:
    post[sig(o.data)] = post.get(sig(o.data), 0) + 1
print("   post signatures %s (want only %s)" % (post, sorted(KIT_SIG.values())))
assert set(post) <= set(KIT_SIG.values()), "a target kept a non-kit signature"
assert all(len(o.data.color_attributes) == 0 for o, _k, _m in targets)
assert all(len(o.data.uv_layers) == 1 for o, _k, _m in targets)
print("   every re-shaped mesh: 0 colour attributes (owed to dh_rimclump_col), 1 UV layer")

if SAVE:
    bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
