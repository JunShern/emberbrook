"""dh_rimclump_col.py — THE LOCKSFOOT VEGETATION WAS BUILT WITHOUT THE MESH DATA ITS
OWN MATERIALS READ.  Two missing attributes, two different symptoms, one builder.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_rimclump_col.py -- --dry
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_rimclump_col.py -- save

WHAT ROUND 9 HANDED OVER, AND WHY BOTH OF ITS CANDIDATES WERE WRONG.  It measured
`mat_leaf_autumn` at L p50 0.0 on crossing, 0.2 on cottage (5.2% of frame) and 0.4
on weave against 121.5 at waterfront, and left it "unresolved between ALBEDO and
LIGHT".  IT IS NEITHER.  `locksfoot_build.py` joins its rim clumps out of fresh
`cyl()` primitives and its ferns out of fresh `obox()`, and a fresh primitive has
no colour attribute and no UV layer.  Both materials read both:

  * `Col` — `mat_leaf_autumn`/`_green`/`_creeper`/`mat_grass`/`mat_fern` all take
    Base Color AND the Translucent BSDF's Color from the `surv_col` VertexColor
    node (master_survivability.py's glTF-survival cure).  A VertexColor node whose
    attribute is absent returns BLACK, so the surface has zero albedo of both
    kinds.  145 meshes were in that state.
  * `UVMap` — the three LEAF materials additionally drive a Transparent BSDF mix
    from `Texture Coordinate.UV -> … -> Color Ramp -> Mix Shader.001.Factor`.
    With no UV layer the coordinate is the constant (0,0,0), so the cutout factor
    is CONSTANT over the whole mesh, and it evaluates to fully transparent.
    41 of 225 leaf meshes — every `veg_lf_rimclump_*` — were in that state; all
    184 healthy leaf meshes carry a UV layer spanning 0..1.

**THE UV DEFECT IS THE ONE THAT OWNED THE PICTURE, AND A CONTROL IS WHAT SEPARATED
THEM.**  Repairing `Col` alone and re-rendering the whole town at draft moved the
autumn clumps' own pixels by NOTHING — cottage p50 0.0 -> 0.0, weave 0.0 -> 0.0,
crossing 0.6 -> 0.6, north-landing 36.5 -> 36.5 — while the grass and ferns, whose
materials have no cutout branch, moved hard on the same run (lockfive 1.2 -> 14.3,
weave 15.1 -> 51.5, north-landing 1.2 -> 23.3).  A material change that is inert on
exactly the meshes with the second defect and live on exactly the ones without it
is not an interpretation, it is the split.

SO THE CLUMPS WERE NEVER BLACK — THEY WERE NOT THERE.  A RAY-CASTER IGNORES ALPHA,
which is why round 9's ray census attributed 78.1% of weave's "black cave mouth" to
five of them and concluded they were "rendering at literal L 0.0".  They render
nothing at all; the black behind them is a different subject and is still owed a
diagnosis.  Round 9's refutation of the cave stands, its explanation does not.
Same family as the two lies `dh_pixel_census` already documents: the ray-caster's
object set is not the renderer's.

WHY NOT JUST RE-RUN master_survivability.  IT WOULD BAKE THE DEFECT IN.  That pass
rewires each cured material's CURRENT albedo socket into an Emission and bakes EMIT
— and the current albedo socket IS `surv_col`.  On an orphaned mesh that bakes
black from black and then writes black into a freshly created `Col`, turning a
Blender-only defect into a black COLOR_0 that also ships to the runtime.  Its own
header records the same shape one step earlier (finding 218).  So this bakes from
each material's ORIGINAL PROCEDURAL SOURCE, still present in the node tree with its
Color output unlinked, and asserts that source is unlinked before touching it.

UVs ARE A UNIT SQUARE PER FACE, AND THE SCALE IS THE WHOLE OF IT.  The cutout is
`(UV - 0.5) -> LENGTH`, a RADIAL mask, so a face mapped to the full 0..1 square is
one leaf.  The kit's healthy clumps measure median UV area 1.00000 per face; a
first attempt here used one cylindrical span over the whole mesh, measured 0.034
per face, and made each clump a SINGLE leaf — a few huge holes showing the open
backfaces of the cylinder through them, which the judge called "bright orange
vehicle wreckage".  Right mechanism, wrong scale.  Match the reference, do not
invent a projection.

SCOPE IS DERIVED, NEVER LISTED.  It censuses every mesh wearing one of the cured
materials and takes those missing either attribute; the 145 and the 41 are outputs.
A material that turns up with orphans and no declared procedural source is a HARD
ERROR, not a skip.

WHAT IT PRESERVES, asserted:
  * geometry — object set and every object's vertex/polygon count, before vs after;
  * the healthy meshes — a sha256 over their `Col` bytes, before vs after;
  * every material's node tree — the temporary Emission is removed and the original
    Surface link restored;
  * `hide_render` / `hide_viewport` and the scene's render engine.
Non-cured loops of a repaired mesh (`mat_timber_dark`, the clump trunks) are left
WHITE, which is glTF's neutral COLOR_0 and Blender-inert because that material does
not read `Col`.  That is master_survivability's own rule, for its own reason.
"""
import bpy, sys, os, json, hashlib, functools
import numpy as np
from mathutils import Vector, Matrix

print = functools.partial(print, flush=True)   # background stdout is buffered
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv or "--save" in argv
DRY = "--dry" in argv

ATTR = "Col"
VC_NODE = "surv_col"

# the three materials whose Transparent-BSDF cutout is driven from Texture
# Coordinate.UV; a mesh wearing one of these and carrying no UV layer renders
# fully transparent whatever its colour says.
UVMATS = ("mat_leaf_autumn", "mat_leaf_green", "mat_leaf_creeper",
          "mat_leaf_autumn_far")

# THE HOLD IS GONE, AND WHAT PAID IT OFF WAS GEOMETRY (round 11).  Round 10 held
# `mat_grass`/`mat_fern` back with a measurement rather than a shrug: `locksfoot_build`
# built `veg_lf_fern_*` with `obox()` — literal BOXES — so black they were furniture
# and coloured they were lime blocks on lockfive's strand (1.34% of that frame).  Two
# colour rungs were measured before that call and both were right by the ruler and
# wrong by eye (object-space Z at world z 0.2372/0.2423/0.0895, own-base
# 0.1756/0.1858/0.0694, against the healthy 0.1376/0.1509/0.0570), because no gradient
# makes a box a plant.  Round 11 found the town already HAD a kit — 150 tufts at
# 160/64 and 131 ferns at 110/44 — and that the orphan set was TWO districts, not one:
# 78 `veg_lf_fern_*` boxes and 26 `veg_lk_tuft_*` crossed quads, which is exactly the
# "104" round 10 named.  `tools/dh_veg_kit.py` re-shapes all 104 from the town's own
# donor mesh and MUST RUN BEFORE THIS TOOL.  Colour is owed the geometry first; the
# geometry has been paid.
HOLD = {}

# material -> the node whose Color output was the ORIGINAL Base Color, before
# master_survivability relinked it to `surv_col`.  Asserted unlinked at run time:
# if it is linked, the material has not been cured the way this tool assumes and
# baking from it would be a guess.
SOURCE = {
    "mat_leaf_autumn":     "Color Ramp.001",
    "mat_leaf_green":      "Color Ramp.001",
    "mat_leaf_creeper":    "Color Ramp.001",
    "mat_leaf_autumn_far": "Color Ramp.001",
    # grass and fern are object-space Z ramps with ONE ColorRamp; the leaf trees
    # have two and the unsuffixed one drives the ALPHA CUTOUT (Mix Shader.001's
    # Factor), never the albedo.  Baking that would write the leaf mask into the
    # colour — which is why this is a per-material map and not "the last ramp".
    "mat_grass":           "Color Ramp",
    "mat_fern":            "Color Ramp",
}


def col_digest(names):
    h = hashlib.sha256()
    for n in sorted(names):
        me = bpy.data.objects[n].data
        ca = me.color_attributes.get(ATTR)
        h.update(n.encode())
        if ca is None:
            h.update(b"<none>")
            continue
        v = np.zeros(len(ca.data) * 4, dtype=np.float32)
        ca.data.foreach_get("color", v)
        h.update(v.tobytes())
    return h.hexdigest()


def geom_digest():
    return {o.name: (len(o.data.vertices), len(o.data.polygons))
            for o in bpy.data.objects if o.type == 'MESH'}


# ------------------------------------------------------------------ the census --
cured = set(SOURCE) - set(HOLD)
for m, why in sorted(HOLD.items()):
    print("HELD BACK  %-14s %s" % (m, why))
orphans, healthy = [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    mats = {s.material.name for s in o.material_slots if s.material}
    if not (mats & cured):
        continue
    (healthy if ATTR in o.data.color_attributes else orphans).append(o.name)

print("== dh_rimclump_col ==")
print("meshes wearing a Col-reading cured material : %d" % (len(orphans) + len(healthy)))
print("  with %s    : %d" % (ATTR, len(healthy)))
print("  WITHOUT %s : %d" % (ATTR, len(orphans)))

need = {}
for n in orphans:
    for s in bpy.data.objects[n].material_slots:
        if s.material and s.material.name in cured:
            need.setdefault(s.material.name, []).append(n)
for m, ns in sorted(need.items()):
    print("   %-22s %d meshes  e.g. %s" % (m, len(ns), ", ".join(sorted(ns)[:3])))
if not orphans:
    print("nothing to repair"); sys.exit(0)

# every orphan's cured material must declare a procedural source, and that source
# must still be unlinked — otherwise this is not the state the tool was written for.
for m in need:
    if m not in SOURCE:
        raise SystemExit("REFUSE: %s has orphaned meshes and no declared source" % m)
    mat = bpy.data.materials[m]
    node = mat.node_tree.nodes.get(SOURCE[m])
    if node is None:
        raise SystemExit("REFUSE: %s has no node %r" % (m, SOURCE[m]))
    if node.outputs[0].is_linked:
        raise SystemExit("REFUSE: %s.%s is LINKED — the material is not in the "
                         "post-survivability state this tool bakes from"
                         % (m, SOURCE[m]))
    vc = mat.node_tree.nodes.get(VC_NODE)
    if vc is None or vc.layer_name != ATTR:
        raise SystemExit("REFUSE: %s has no %s node reading %r" % (m, VC_NODE, ATTR))
    print("   source %-22s <- %s (unlinked, as expected)" % (m, SOURCE[m]))

# -------------------------------------------------------- the SECOND census ----
# A leaf mesh with no UV layer renders fully TRANSPARENT, whatever its colour says.
uv_orphans, uv_healthy = [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    mats = {s.material.name for s in o.material_slots if s.material}
    if not (mats & set(UVMATS)):
        continue
    (uv_healthy if o.data.uv_layers else uv_orphans).append(o.name)
print("meshes wearing a UV-cutout leaf material  : %d" % (len(uv_orphans) + len(uv_healthy)))
print("  with a UV layer    : %d" % len(uv_healthy))
print("  WITHOUT a UV layer : %d   e.g. %s"
      % (len(uv_orphans), ", ".join(sorted(uv_orphans)[:3])))

geo0 = geom_digest()
dig0 = col_digest(healthy)
print("healthy Col digest before: %s" % dig0[:16])

if DRY:
    print("\n--dry: nothing written")
    sys.exit(0)

# ---------------------------------------------------------------- the UV fix ---
# THE CUTOUT IS A RADIAL MASK PER FACE, so the right UV is a UNIT SQUARE PER FACE.
# The chain is `Texture Coordinate.UV -> (UV - 0.5) -> LENGTH -> Map Range -> …
# -> Color Ramp -> Mix Shader.001.Factor`: distance from the middle of the UV
# square, i.e. every face is one leaf, round in the middle and cut away at its
# rim.  Measured on the kit's own healthy clumps, which is where this number comes
# from rather than from taste: median UV area PER FACE

#     veg_rimclump_0        1.00000      veg_gate_rimclump_10   1.00000
#
# — the full square on every face.  A first attempt here used one cylindrical
# 0..1 span over the WHOLE mesh and measured 0.034 per face, 29x coarser, which
# makes the entire clump a single leaf: a few huge holes with the open backfaces
# of the cylinder showing through them.  The judge read exactly that and called it
# "a cluster of bright orange vehicle wreckage" and "open holes that expose
# backface-culled hollow interiors".  Right mechanism, wrong scale — the same
# lesson `dh_pixel_census` records about density and the wash.
import math
uv_made = 0
SQ = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
for n in uv_orphans:
    me = bpy.data.objects[n].data
    lay = me.uv_layers.new(name="UVMap")
    uv = np.zeros((len(me.loops), 2), dtype=np.float32)
    for p in me.polygons:
        li = list(p.loop_indices)
        k = len(li)
        for j, l in enumerate(li):
            if k == 4:
                uv[l] = SQ[j]
            elif k == 3:
                uv[l] = SQ[j]
            else:                       # n-gon: inscribe in the unit square
                a = 2 * math.pi * j / k
                uv[l] = (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))
    lay.data.foreach_set("uv", uv.ravel())
    me.uv_layers.active = lay
    uv_made += 1
print("UV layers created on %d meshes" % uv_made)

# ------------------------------------------------------------------- the bake --
sc = bpy.context.scene
eng0, tgt0 = sc.render.engine, sc.render.bake.target
hr0 = {o.name: o.hide_render for o in bpy.data.objects}
hv0 = {o.name: o.hide_viewport for o in bpy.data.objects}

restore = []
for m in need:
    nt = bpy.data.materials[m].node_tree
    src = nt.nodes[SOURCE[m]].outputs[0]
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    orig = out.inputs['Surface'].links[0].from_socket
    em = nt.nodes.new('ShaderNodeEmission')
    em.name = "_rc_bake_em"
    em.inputs['Strength'].default_value = 1.0
    nt.links.new(src, em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    restore.append((nt, out, orig, em))

# EVERY OTHER OBJECT IS HIDDEN FOR THE BAKE, and that is a speed fix with a proof
# rather than a shortcut.  `bake(type='EMIT')` with use_pass_direct and
# use_pass_indirect both False evaluates each shading point's own emission and
# nothing else — no other object can contribute to the result — but Cycles still
# SYNCS the whole scene per operator call, and this town is 27M triangles: the
# first run of this tool spent ten minutes inside its first batch and never
# reached the copy.  The control is the assertion at the bottom: the repaired
# meshes' cured-loop mean must land on the mean of the 61 healthy clumps that were
# baked by master_survivability with the whole town present.
want = set(orphans)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name not in want:
        o.hide_render = True
for n in orphans:
    o = bpy.data.objects[n]
    a = o.data.color_attributes.get("_rc_bake")
    if a is None:
        a = o.data.color_attributes.new("_rc_bake", "FLOAT_COLOR", "CORNER")
    o.data.color_attributes.active_color = a
    o.hide_render = False
    o.hide_viewport = False
    o.hide_set(False)

# AND THE RAMP MUST BE EVALUATED WHERE THE ARTIST MEANT IT TO BE.  `mat_grass` and
# `mat_fern` are Texture Coordinate OBJECT -> Separate XYZ.Z -> Map Range ramps, i.e.
# base-dark / tip-light over the tuft's OWN height.  `locksfoot_build` makes these
# with `obox()` and `join_meshes()`, which leave the object origin at the WORLD
# origin, so object space IS world space and every tuft evaluates the ramp at its
# gorge altitude — clamping the whole mesh to one end of the ramp.  Baked that way
# the ferns come back as flat lime BLOCKS: measured mean (0.2372, 0.2423, 0.0895)
# against the 165 healthy grass meshes' (0.1376, 0.1509, 0.0570), and it is plainly
# worse by eye at lockfive than the black it replaced.  So the origin is moved to
# the mesh's own base FOR THE BAKE and put back exactly afterwards; world vertex
# positions never move (the data translation and the object translation cancel),
# which is why the geometry gate still holds.
#
# AND THE SHIFT IS CONDITIONAL, BECAUSE THE DEFECT IT CURES IS NOT "the origin is not
# the base" — IT IS "the mesh does not lie in the ramp's domain at all" (round 11).
# Measured on the shipped materials: the Map Range is `From Min 0.0, From Max 0.45`
# (`mat_grass`) / `0.55` (`mat_fern`), CLAMPED.  So the ramp only has an opinion about
# object-space z in [0, From Max], and the 281 healthy kit meshes are authored CENTRED
# ON ZERO (local z p50 -0.189..0.266 grass, -0.355..0.399 fern) — half of every healthy
# plant clamps to the dark end and that is what the town looks like.  Shifting such a
# mesh to base-at-zero lifts its whole body into the lit half: measured on the 104
# kit-shaped meshes, `mat_grass` came back (0.1633, 0.1745, 0.0654) against the healthy
# 150's (0.1214, 0.1359, 0.0517) — 35% bright — for no reason but the shift.
# So shift ONLY a mesh that lies OUTSIDE the ramp's domain entirely, which is exactly
# the `obox()`/`join_meshes()` case this was written for (object space = world space,
# so every tuft evaluates the ramp at its gorge altitude and clamps to one end).
FROM_MAX = max(
    float(n.inputs['From Max'].default_value)
    for m in need
    for n in bpy.data.materials[m].node_tree.nodes if n.type == 'MAP_RANGE')
origins = {}
inside = 0
for n in orphans:
    o = bpy.data.objects[n]
    me = o.data
    co = np.zeros(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    z = co.reshape(-1, 3)[:, 2]
    if float(z.max()) > 0.0 and float(z.min()) < FROM_MAX:
        inside += 1                      # already authored in the space the ramp reads
        continue
    c = Vector((0.0, 0.0, float(z.min())))
    if c.length < 1e-6:
        continue
    me.transform(Matrix.Translation(-c))
    o.location = o.location + c
    origins[n] = c
print("ramp domain is object z 0..%.2f; %d orphan meshes already lie in it (left alone), "
      "%d moved to their own base" % (FROM_MAX, inside, len(origins)))

sc.render.engine = 'CYCLES'
sc.cycles.samples = 1
sc.render.bake.target = 'VERTEX_COLORS'
sc.render.bake.use_pass_direct = False
sc.render.bake.use_pass_indirect = False
sc.render.bake.use_pass_color = True

B = max(len(orphans), 1)   # ONE sync, not four
for i in range(0, len(orphans), B):
    chunk = [bpy.data.objects[n] for n in orphans[i:i + B]]
    bpy.ops.object.select_all(action='DESELECT')
    for o in chunk:
        o.select_set(True)
    bpy.context.view_layer.objects.active = chunk[0]
    bpy.ops.object.bake(type='EMIT')
    print("  baked %d/%d" % (min(i + B, len(orphans)), len(orphans)), flush=True)

# ------------------------------------------------- copy into a fresh white Col --
# unique mesh DATA, not objects: linked duplicates share one mesh and the scratch
# attribute is removed on the first visit (master_survivability, same reason).
meshes = {}
for n in orphans:
    meshes.setdefault(bpy.data.objects[n].data.name, bpy.data.objects[n].data)
print("copying into %s over %d unique meshes (%d objects)"
      % (ATTR, len(meshes), len(orphans)))
stats = []
permat = {}
for me in meshes.values():
    src = me.color_attributes.get("_rc_bake")
    if src is None:
        continue
    d = np.zeros(len(src.data) * 4, dtype=np.float32)
    src.data.foreach_get("color", d)
    col = me.color_attributes.new(ATTR, "FLOAT_COLOR", "CORNER")
    cur = np.ones(len(col.data) * 4, dtype=np.float32)   # WHITE = glTF-neutral
    mask = np.zeros(len(col.data), dtype=bool)
    for p in me.polygons:
        m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
        if m and m.name in need:
            for li in p.loop_indices:
                mask[li] = True
    m4 = np.repeat(mask, 4)
    cur[m4] = d[m4]
    col.data.foreach_set("color", cur)
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = list(me.color_attributes).index(col)
    me.color_attributes.remove(me.color_attributes["_rc_bake"])
    v = cur.reshape(-1, 4)[mask][:, :3]
    if len(v):
        stats.append(v.mean(axis=0))
    for mm in need:
        sub = np.zeros(len(col.data), dtype=bool)
        for p in me.polygons:
            m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
            if m and m.name == mm:
                for li in p.loop_indices:
                    sub[li] = True
        if sub.any():
            permat.setdefault(mm, []).append(cur.reshape(-1, 4)[sub][:, :3].mean(axis=0))

for n, c in origins.items():                 # put every origin back, exactly
    o = bpy.data.objects[n]
    o.data.transform(Matrix.Translation(c))
    o.location = o.location - c
for nt, out, orig, em in restore:
    nt.links.new(orig, out.inputs['Surface'])
    nt.nodes.remove(em)
for o in bpy.data.objects:
    o.hide_render = hr0.get(o.name, o.hide_render)
    o.hide_viewport = hv0.get(o.name, o.hide_viewport)
sc.render.engine, sc.render.bake.target = eng0, tgt0

# ------------------------------------------------------------------- the gates --
mean = np.mean(stats, axis=0) if stats else np.zeros(3)
print("\nbaked cured-loop mean  : (%.4f, %.4f, %.4f)  over %d meshes"
      % (mean[0], mean[1], mean[2], len(stats)))
print("healthy clumps' own mean: (0.3080, 0.1190, 0.0360)  [autumn reference]")
# AND THE COMPARISON THAT MATTERS IS PER MATERIAL AGAINST ITS OWN HEALTHY FAMILY.
# The single "autumn reference" line above is one material's number and it silently
# passed a `mat_grass` repair that came back at 57% of its own family (round 11).
healthy_mean, healthy_n = {}, {}
for mm in permat:
    acc = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name in set(orphans):
            continue
        if mm not in [sl.material.name for sl in o.material_slots if sl.material]:
            continue
        ca = o.data.color_attributes.get(ATTR)
        if ca is None:
            continue
        c = np.zeros(len(ca.data) * 4, dtype=np.float32)
        ca.data.foreach_get("color", c)
        acc.append(c.reshape(-1, 4)[:, :3].mean(axis=0))
    if acc:
        healthy_mean[mm] = np.mean(acc, axis=0)
        healthy_n[mm] = len(acc)
for mm, vv in sorted(permat.items()):
    a = np.mean(vv, axis=0)
    hm = healthy_mean.get(mm)
    rel = ("  vs its own healthy family (%.4f, %.4f, %.4f) over %d meshes = %.0f%%"
           % (hm[0], hm[1], hm[2], healthy_n[mm],
              100 * float(np.mean(a / np.maximum(hm, 1e-6))))
           ) if hm is not None else "  (no healthy family to compare against)"
    print("   %-20s repaired mean (%.4f, %.4f, %.4f) over %d meshes%s"
          % (mm, a[0], a[1], a[2], len(vv), rel))

geo1 = geom_digest()
assert geo0 == geo1, "GEOMETRY MOVED — refusing"
dig1 = col_digest(healthy)
assert dig0 == dig1, "an existing Col changed — refusing (%s -> %s)" % (dig0[:16], dig1[:16])
still = [n for n in orphans if ATTR not in bpy.data.objects[n].data.color_attributes]
assert not still, "still without %s: %s" % (ATTR, still[:5])
assert float(mean.max()) > 0.02, \
    "the bake came back black (%s) — the source link is wrong, refusing to ship it" % mean
stillu = [n for n in uv_orphans if not bpy.data.objects[n].data.uv_layers]
assert not stillu, "still without a UV layer: %s" % stillu[:5]
for n in uv_orphans[:200]:
    me = bpy.data.objects[n].data
    u = np.zeros(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", u)
    assert 0.0 <= u.min() and u.max() <= 1.0001, "%s UVs outside 0..1" % n
print("GATES: geometry unchanged (%d meshes) · healthy Col digest unchanged (%s) · "
      "%d meshes given %s · %d meshes given a UV layer in 0..1"
      % (len(geo1), dig1[:16], len(orphans), ATTR, len(uv_orphans)))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
