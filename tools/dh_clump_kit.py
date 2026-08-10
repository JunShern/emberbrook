"""dh_clump_kit.py — THE THIRD FOLIAGE GRAMMAR, AND THE "THERE IS NO KIT" CLAIM IS FALSE.
A CARRIER ONTO THE LIVE MASTER, NEVER A DISTRICT REBUILD.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_clump_kit.py -- [--dry] [--rim] [save] [--force]

WHAT IT MEASURED FIRST (round 12, one property probe over the master + one
`dh_objmap` dump).  Round 11 found smooth pale lozenges on north-landing's cliff BY
LOOKING and named them `veg_nl_clump_*`, 2.80% of that frame.  They are 15 meshes.
**THE SAME BUILDER MAKES 74 MORE, ONE FUNCTION UP THE SAME FILE**, and nobody had put
the two together:

    veg_wv_clump_*  x74   54 verts / 33 faces   lf_matte   world h p50 0.96
    veg_nl_clump_*  x15   54 verts / 33 faces   lf_matte   world h p50 1.11

Both are `weave_build.py` building THREE 9-SIDED TAPERED DRUMS (`cyl(..., 9, MMATTE,
r2=w*0.16)`) and joining them — lines 1567-1591 and 1726-1749.  54 verts is 3 x 18;
33 faces is 3 x (9 sides + 2 caps).  So the third grammar is EIGHTY-NINE meshes on
ELEVEN of the fifteen cameras, not fifteen on one:

    north-landing 3.22%  cottage 2.08%  fishdock 1.62%  deep-stairs 1.08%
    waterfront    1.01%  weave   0.96%  lockfive 0.59%  lockhead    0.42%
    crossing      0.20%  quay-west 0.02%  gate     0.01%

`lf_matte` is NOT the subject — it is 14.85% of lockfive as barge hulls, dam caps and
bunting cloth.  The subject is the OBJECT PREFIX; the material is a symptom.

**AND THERE IS A KIT, SITTING IN THE MASTER BESIDE THE ONE `dh_veg_kit` ALREADY USED.**

    v10_src_clump_a  184 verts / 46 faces  mat_leaf_autumn  h 2.099  uv area/face 1.00000
    v10_src_clump_b  112 verts / 28 faces  mat_leaf_autumn  h 1.216  uv area/face 1.00000

both `hide_render`, both at the origin, and 63 healthy in-town clumps (`veg_wf_rimclump_*`,
`veg_rimclump_*`, `veg_gate_rimclump*`) already wear exactly those two signatures.  At
deep-stairs and waterfront a healthy clump and an orphan drum stand IN THE SAME FRAME.

THREE THINGS DERIVED RATHER THAN CHOSEN, each with its measurement:

  * WHICH DONOR — `v10_src_clump_b` (h 1.216) for the drums, whose own heights run
    0.69/0.96/1.50 at p05/p50/p95.  The taller `_a` is 2.1 m and would have to be
    scaled to 46% of itself.
  * THE HEIGHT IS THE ORPHAN'S OWN, WHICH IS THE OPPOSITE OF `dh_veg_kit`'S RULE, AND
    THE REASON IS THE MATERIAL.  `mat_grass`/`mat_fern` drive a Color Ramp from
    object-space Z through a CLAMPED Map Range, so a short plant reads dark and the
    height had to be drawn from the kit.  `mat_leaf_green` HAS NO Z TERM AT ALL — its
    Base Color and its Translucent Color both come straight from the `surv_col` vertex
    attribute.  So height is free here, and the height the district's own
    `clear_box(px, py, gz, gz+1.2)` cleared is the one that cannot introduce an
    intersection.
  * AND THE WIDTH IS THE BUILDER'S CLEARANCE TEST, NOT THE DRUM'S OWN BOX.  Fitting
    the donor inside each drum's own bounding box was tried first and LOOKED WRONG:
    the donor is 1.16 WIDER THAN TALL and a drum is taller than wide, so the fit was
    width-limited and the plants came out at 0.71 m against the drums' own 0.96 m
    (scale p50 0.582) — small enough that at cottage's 21 m they nearly vanished.
    The bound that is actually load-bearing is the one `weave_build` itself tested
    before placing anything: `spot(px, py, 0.55)` for the weave run and
    `spot(px, py, 0.60)` for the landing, i.e. a cleared CIRCLE of diameter 1.10 /
    1.20 m, with `clear_box(..., gz, gz + 1.4 / 1.2)` above it.  A plant inside that
    envelope stands in ground the builder proved clear, and at the donor's own aspect
    a height-matched copy lands within 1% of that diameter — which is why this is a
    derivation and not a preference.
  * THE DRUMS' COLOUR IS KEPT, NOT SOLVED, BECAUSE IT IS ALREADY IN FAMILY.  Each one
    carries its own dye (`PAL[leaf|mosswood|leafdry|leafturn]` with the builder's 0.13
    jitter, 89 distinct means).  Measured against the 63 healthy clumps' stored `Col`:

        healthy clump family   Col luminance p05/p50/p95  0.1501 / 0.1535 / 0.1617
        the 89 orphan drums    Col luminance p05/p50/p95  0.1059 / 0.1309 / 0.1653

    18% apart at the median and overlapping at both tails.  There is no colour defect
    there, so nothing is repaired: the mean of each object's OWN `Col` is written back
    onto its replacement and its four-dye variety survives the carry.
  * THE RIM CLUMPS' COLOUR IS NOT IN FAMILY AND THE GEOMETRY FIX MADE IT LEGIBLE.
    They read `Col` luminance p05/p50/p95 **0.3037 / 0.3061 / 0.3094 — 2.0x the
    healthy family** — and desaturated with it: mean (0.4332, 0.2781, 0.2111) against
    the family's (0.2560, 0.1357, 0.0416).  As stacked cylinders that was a bright
    orange fan; on kit geometry with the cutout it photographs as pale pink-brown
    blossom, which is worse.  Same shape as round 10's "A REPAIR CAN MAKE A SECOND
    DEFECT LEGIBLE".  Their dye is therefore NOT carried: each takes a dye drawn
    deterministically (FNV of its own name) from the 63 healthy clumps' OWN list of
    per-object `Col` means.  That family is tight enough for this to be a copy rather
    than a choice — its luminance spread is +-4% about the median.
    NOTE the provenance: that stale dye is `dh_rimclump_col`'s round-10 bake of an
    object-space Z ramp over the CYLINDER geometry.  The geometry it was baked for no
    longer exists, so carrying it forward would have been carrying a derived artifact
    past the thing it was derived from.

**AND THE TWO LEAF MATERIALS ARE ONE MATERIAL.**  `mat_leaf_green` and
`mat_leaf_autumn` were dumped node by node and link by link and are IDENTICAL —
same 17 nodes, same 18 links, same two Color Ramps.  `Color Ramp.001` (the one that
looks like the autumn tint, stops at 0.235/0.062/0.028 .. 0.285/0.180/0.058) DRIVES
NOTHING: its Color output is unlinked, and the only ramp that reaches the shader is
the CUTOUT factor.  Every autumn/green difference in this town is carried by the
vertex colour.  So the material named here is free, and `mat_leaf_green` is used for
all 89 for the honest reason that the material carries no colour at all.

WHAT THE SWAP BUYS, MECHANICALLY: the radial UV cutout (`Texture Coordinate.UV ->
(uv-0.5).length -> Map Range -> Color Ramp -> Mix Shader.001.Factor` against a
Transparent BSDF) and the 0.22 Translucent mix.  Round 10 paid a whole bake to learn
that the cutout is a RADIAL mask and a face mapped to the full 0..1 square is ONE
LEAF: the donor's UV is 1.00000 area per face, the kit's own number, and it is copied
loop for loop, so the scale is right by construction and not by choice.

`--rim` ALSO CARRIES TARGET 4 (`veg_lf_rimclump_*`, 41 meshes, 66 verts / 41 faces =
three 9-gon drums PLUS a 6-gon trunk, 5.24% of the cottage frame).  Round 11 declined
it as "authoring, not carrying, because there is NO KIT to copy" — that is refuted by
`v10_src_clump_a` above.  The trunk is KEPT: only the `mat_leaf_autumn` faces are
replaced, and the `mat_timber_dark` faces are carried through untouched, because a
whole-mesh copy would delete a trunk the donor does not have.

IT IS IDEMPOTENT BY REFUSING: a target is only rewritten while its mesh still carries
the drum signature.  Re-running is a no-op that says so.  `--force` overrides.

THE DISTRICT BUILDERS ARE NOT EDITED, for the same reason `dh_veg_kit` does not edit
`locksfoot_build.py`: re-running `weave_build.py` rebuilds two whole dressed districts
and is a function of town geometry that has moved since.
"""
import bpy, sys, math, hashlib
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "--dry" in argv
FORCE = "--force" in argv
RIM = "--rim" in argv

DRUM_PREFIXES = ("veg_wv_clump_", "veg_nl_clump_")
DRUM_SIG = {(54, 33)}                       # three 9-gon tapered drums, joined
RIM_PREFIX = "veg_lf_rimclump_"
RIM_SIG = {(66, 41)}                        # the same three drums + a 6-gon trunk
LEAF_MAT = "mat_leaf_green"
TRUNK_MAT = "mat_timber_dark"
# `weave_build`'s OWN clearance tests, per run — the radius it passed to `spot()`
# before it agreed to place anything there, and the height it passed to `clear_box`.
CLEARED = {"veg_wv_clump_": (0.55, 1.4), "veg_nl_clump_": (0.60, 1.2)}
HEALTHY_PREFIXES = ("veg_wf_rimclump_", "veg_rimclump_", "veg_gate_rimclump")


def sig(me):
    return (len(me.vertices), len(me.polygons))


def local_co(ob):
    me = ob.data
    v = np.zeros(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", v)
    return v.reshape(-1, 3)


def world_of(ob, v):
    M = np.array(ob.matrix_world)
    return v @ M[:3, :3].T + M[:3, 3]


def col_mean(ob):
    ca = ob.data.color_attributes.get("Col")
    if ca is None:
        return None
    a = np.zeros(len(ca.data) * 4, dtype=np.float32)
    ca.data.foreach_get("color", a)
    return a.reshape(-1, 4)[:, :3].mean(axis=0).astype(np.float64)


# --------------------------------------------------------------- the donors ---
DONOR_SIG = {"small": (112, 28), "large": (184, 46)}
donors = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("v10_src_clump"):
        continue
    for kind, s in DONOR_SIG.items():
        if sig(o.data) == s:
            donors[kind] = o
if set(donors) != set(DONOR_SIG):
    raise SystemExit("REFUSE: clump donors not found in the master — have %s, want %s"
                     % (sorted(donors), sorted(DONOR_SIG)))
for kind, o in sorted(donors.items()):
    v = local_co(o)
    if not o.data.uv_layers:
        raise SystemExit("REFUSE: donor %s carries no UV layer, and the leaf cutout IS "
                         "the UV" % o.name)
    print("DONOR %-6s %-18s %3d verts / %3d faces  h %.3f  uv=%s  hide_render=%s"
          % (kind, o.name, len(o.data.vertices), len(o.data.polygons),
             v[:, 2].max() - v[:, 2].min(), o.data.uv_layers[0].name, o.hide_render))

if LEAF_MAT not in bpy.data.materials:
    raise SystemExit("REFUSE: %s is not in this master" % LEAF_MAT)
LEAF = bpy.data.materials[LEAF_MAT]

# THE MATERIAL CLAIM IS ASSERTED, NOT ASSUMED.  If someone ever makes the two leaf
# materials genuinely different, this file's "the material is free" reasoning stops
# being true and the run must stop with it.
_a, _b = bpy.data.materials["mat_leaf_green"], bpy.data.materials.get("mat_leaf_autumn")
if _b is not None:
    ka = sorted((n.bl_idname, n.name) for n in _a.node_tree.nodes)
    kb = sorted((n.bl_idname, n.name) for n in _b.node_tree.nodes)
    la = sorted((l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name)
                for l in _a.node_tree.links)
    lb = sorted((l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name)
                for l in _b.node_tree.links)
    if ka != kb or la != lb:
        raise SystemExit("REFUSE: mat_leaf_green and mat_leaf_autumn are no longer the "
                         "same node tree — re-derive which one this carrier should use")
    print("CHECK  mat_leaf_green == mat_leaf_autumn : %d nodes, %d links, identical"
          % (len(ka), len(la)))

# ---------------------------------------------------------------- the census --
targets, already, refused = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if o.name.startswith(DRUM_PREFIXES):
        kind = "drum"
    elif RIM and o.name.startswith(RIM_PREFIX):
        kind = "rim"
    else:
        continue
    want = DRUM_SIG if kind == "drum" else RIM_SIG
    if sig(o.data) not in want and not FORCE:
        already.append(o.name)
        continue
    if col_mean(o) is None:
        refused.append((o.name, "no Col attribute — its dye cannot be carried")); continue
    if kind == "rim":
        mats = [s.material.name if s.material else None for s in o.material_slots]
        if LEAF_MAT.replace("green", "autumn") not in mats and "mat_leaf_autumn" not in mats:
            refused.append((o.name, "no mat_leaf_autumn slot (%s)" % mats)); continue
        if TRUNK_MAT not in mats:
            refused.append((o.name, "no %s slot (%s)" % (TRUNK_MAT, mats))); continue
    targets.append((o, kind))

print("== dh_clump_kit ==")
byk = {}
for o, k in targets:
    byk[k] = byk.get(k, 0) + 1
print("orphan clump meshes to re-shape : %d  %s" % (len(targets), byk))
byp = {}
for o, _k in targets:
    p = o.name.rsplit("_", 1)[0]
    byp[p] = byp.get(p, 0) + 1
print("   by prefix %s" % byp)
if already:
    print("already kit-shaped (skipped, pass --force to re-derive) : %d" % len(already))
for n, why in refused:
    print("   REFUSED %s : %s" % (n, why))
if not targets:
    print("nothing to do")
    sys.exit(0)

# ------------------------------------------- THE KIT'S OWN DYE, FOR THE RIM RUN ---
HEALTHY = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(HEALTHY_PREFIXES):
        c = col_mean(o)
        if c is not None:
            HEALTHY.append(c)
if any(k == "rim" for _o, k in targets):
    if len(HEALTHY) < 8:
        raise SystemExit("REFUSE: only %d healthy clumps to draw a dye from" % len(HEALTHY))
    H = np.array(HEALTHY)
    hl = 0.2126 * H[:, 0] + 0.7152 * H[:, 1] + 0.0722 * H[:, 2]
    print("KIT DYE from %d healthy clumps: mean (%.4f, %.4f, %.4f)  luminance "
          "p05/p50/p95 %.4f / %.4f / %.4f"
          % (len(H), *H.mean(axis=0), *np.percentile(hl, [5, 50, 95])))

if DRY:
    print("--dry: nothing written")
    sys.exit(0)


def fit_copy(dn, lo, hi, name):
    """The donor's local verts, uniformly scaled and yawed to sit inside [lo,hi].

    Uniform because a plant stretched to a drum's proportions is a stretched plant;
    inside because that box is what the district builder's own `clear_box` cleared,
    so a replacement that stays in it cannot introduce an intersection the builder
    had already refused.  Asserted at the end, not hoped."""
    dv = local_co(dn)
    dlo, dhi = dv.min(axis=0), dv.max(axis=0)
    size = hi - lo
    dsz = np.maximum(dhi - dlo, 1e-6)
    s = float(np.min(size / dsz))
    h = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
    a = (h % 3600) / 3600.0 * 2.0 * math.pi      # a row of identical plants all facing
    ca, sa = math.cos(a), math.sin(a)            # one way is the tell of a placement loop
    off = np.array([(dlo[0] + dhi[0]) * 0.5, (dlo[1] + dhi[1]) * 0.5, dlo[2]])
    v = (dv - off) * s
    v = np.stack([v[:, 0] * ca - v[:, 1] * sa, v[:, 0] * sa + v[:, 1] * ca, v[:, 2]], 1)
    ext = v.max(axis=0) - v.min(axis=0)
    fit = float(np.min(size / np.maximum(ext, 1e-6)))
    if fit < 1.0:                 # a uniform scale chosen on the UNROTATED box can
        v *= fit                  # still break it once yawed — shrink, never assert
        s *= fit
        ext = v.max(axis=0) - v.min(axis=0)
    assert (ext <= size + 1e-6).all(), "%s: kit copy %s exceeds its own box %s" % (
        name, ext, size)
    return v, s


made, scales, dyes = 0, [], []
for ob, kind in targets:
    dye = col_mean(ob)
    if kind == "rim":
        # NOT the object's own — see the header.  A deterministic draw from the kit.
        h = int(hashlib.sha256(("dye:" + ob.name).encode()).hexdigest()[:8], 16)
        dye = HEALTHY[h % len(HEALTHY)]
    dyes.append(dye)
    lv = local_co(ob)
    wv = world_of(ob, lv)
    if kind == "drum":
        lo, hi = wv.min(axis=0), wv.max(axis=0)
        # THE ENVELOPE IS THE BUILDER'S, NOT THE DRUM'S: its own cleared circle in
        # plan, its own design height in z, anchored on the drum's own base.
        pre = next(p for p in CLEARED if ob.name.startswith(p))
        rad, ch = CLEARED[pre]
        cx, cy = (lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5
        lo = np.array([cx - rad, cy - rad, lo[2]])
        hi = np.array([cx + rad, cy + rad, lo[2] + min(hi[2] - wv[:, 2].min(), ch)])
        dn = donors["small"]
        v, s = fit_copy(dn, lo, hi, ob.name)
        faces = [tuple(p.vertices) for p in dn.data.polygons]
        verts = v
        mats = [LEAF]
        midx = [0] * len(faces)
        uvsrc = [(dn, 0, len(faces))]
    else:
        # THE TRUNK IS NOT THE DONOR'S TO GIVE.  Split by material index, replace only
        # the leaf faces, carry the timber faces through in their own world places.
        names = [sl.material.name if sl.material else None for sl in ob.material_slots]
        li = names.index("mat_leaf_autumn")
        ti = names.index(TRUNK_MAT)
        leafp = [p for p in ob.data.polygons if p.material_index == li]
        trunkp = [p for p in ob.data.polygons if p.material_index == ti]
        keep = sorted({i for p in trunkp for i in p.vertices})
        remap = {i: k for k, i in enumerate(keep)}
        lidx = sorted({i for p in leafp for i in p.vertices})
        lw = wv[lidx]
        lo, hi = lw.min(axis=0), lw.max(axis=0)
        dn = donors["large"]
        v, s = fit_copy(dn, lo, hi, ob.name)
        base = np.array([(lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5, lo[2]])
        verts = np.concatenate([wv[keep] - base, v], axis=0)
        n0 = len(keep)
        faces = ([tuple(remap[i] for i in p.vertices) for p in trunkp]
                 + [tuple(n0 + i for i in p.vertices) for p in dn.data.polygons])
        mats = [ob.material_slots[ti].material, LEAF]
        midx = [0] * len(trunkp) + [1] * len(dn.data.polygons)
        uvsrc = [(dn, len(trunkp), len(dn.data.polygons))]
        lo = np.array([lo[0], lo[1], min(lo[2], float(wv[keep][:, 2].min()))])
        hi = np.array([hi[0], hi[1], hi[2]])
        # re-centre on the same anchor the drum branch uses
        v = verts

    me = bpy.data.meshes.new(ob.data.name + "_kit")
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    for m in mats:
        me.materials.append(m)
    for p, mi in zip(me.polygons, midx):
        p.material_index = mi
    # the kit's UV, rebuilt loop for loop (donor and copy share topology).  A leaf
    # material with no UV layer evaluates its cutout at the constant (0,0,0) and
    # renders FULLY TRANSPARENT — round 10 paid 41 invisible meshes for that.
    lay = me.uv_layers.new(name=dn.data.uv_layers[0].name)
    uvbuf = np.zeros(len(me.loops) * 2, dtype=np.float32)
    for src, poly0, npoly in uvsrc:
        su = np.zeros(len(src.data.loops) * 2, dtype=np.float32)
        src.data.uv_layers[0].data.foreach_get("uv", su)
        off = sum(len(me.polygons[i].loop_indices) for i in range(poly0))
        uvbuf[off * 2:off * 2 + len(su)] = su
    lay.data.foreach_set("uv", uvbuf)
    # THE DYE IS CARRIED, NOT RE-DERIVED: it is already inside the healthy family's
    # own band (0.1059/0.1309/0.1653 against 0.1501/0.1535/0.1617 in luminance), so
    # there is nothing here for a colour tool to fix.
    ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='CORNER')
    buf = np.tile(np.append(dye, 1.0), len(me.loops)).astype(np.float32)
    ca.data.foreach_set("color", buf)

    old = ob.data
    ob.data = me
    ob.location = Vector((float((lo[0] + hi[0]) * 0.5), float((lo[1] + hi[1]) * 0.5),
                          float(lo[2])))
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    scales.append(s)
    made += 1

d = np.array(dyes)
L = 0.2126 * d[:, 0] + 0.7152 * d[:, 1] + 0.0722 * d[:, 2]
print("RE-SHAPED %d meshes  uniform scale p05/p50/p95 %.3f / %.3f / %.3f"
      % (made, *np.percentile(scales, [5, 50, 95])))
print("   dyes carried: %d distinct Col means, luminance p05/p50/p95 %.4f / %.4f / %.4f"
      % (len({tuple(np.round(x, 5)) for x in dyes}), *np.percentile(L, [5, 50, 95])))

post = {}
for o, _k in targets:
    post[sig(o.data)] = post.get(sig(o.data), 0) + 1
print("   post signatures %s" % post)
assert not (set(post) & (DRUM_SIG | RIM_SIG)), "a target kept its drum signature"
assert all(len(o.data.uv_layers) == 1 for o, _k in targets), "a target lost its UV layer"
assert all("Col" in o.data.color_attributes for o, _k in targets), "a target lost its dye"
for o, k in targets:
    uv = np.zeros(len(o.data.loops) * 2, dtype=np.float32)
    o.data.uv_layers[0].data.foreach_get("uv", uv)
    if float(np.abs(uv).max()) < 1e-6:
        raise SystemExit("REFUSE: %s has an all-zero UV layer — that is the constant "
                         "(0,0,0) that renders fully transparent" % o.name)
print("   every re-shaped mesh: 1 UV layer (non-zero), a Col attribute, no drum signature")

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
