"""veg_greenmix.py — blend GREEN back into Dellhollow's autumn canopy.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/veg_greenmix.py
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/veg_greenmix.py -- save
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/veg_greenmix.py -- revert save

THE NOTE THIS ANSWERS.  "The overall town's colour palette skews far too brown —
mix in some greens among the autumn foliage."  A riverside town in which every
single tree turned on the same day is a postcard, not a place.  So this is a
BLEND, not a replacement: the autumn identity stays and stays dominant on the
upper rim, and the water's edge — where "alive" actually matters, because that is
where the town lives — gets late-summer alder and willow greens among it.

WHERE THE COLOUR ACTUALLY LIVES, and why a naive material edit does nothing.
mat_leaf_autumn's Base Color is NOT a value in the material: it is the `surv_col`
VertexColor node reading the mesh's `Col` corner attribute, because the
survivability pass baked the procedural ramps down to vertex colour so the town's
foliage would survive glTF export as COLOR_0 (finding 219; master_survivability.py).
That has a hard consequence for this pass:

  * A green material with a flat green Base Color would export a baseColorFactor
    that the runtime MULTIPLIES by the still-autumn COLOR_0 — muddy, not green.
  * A green material with a hue-shift node would export NOTHING (glTF has no such
    node), so the runtime would keep the autumn COLOR_0 unchanged while Cycles
    rendered green: the backdrop and the walkable town would disagree.

So green is carried where autumn is carried — in `Col` — and the derived material
is the MARKER that says which clumps are green: it makes the conversion a fact in
the file rather than a fact in this script, makes the pass idempotent (a clump
already wearing mat_leaf_green is never recoloured twice), and leaves a future
re-tint able to select the green set without re-deriving it. The green materials
are structural copies of the autumn ones — same node tree, same alpha cutout, same
translucency — so nothing about export survival changes, which is the point.

THE COLOUR TRANSFORM IS A CHANNEL SWAP, and that is a deliberate choice over the
obvious "set them all to green".  Per corner:

    r' = kr * g      g' = kg * r      b' = kb * b

The autumn ramp is not a flat colour — inside one clump R runs 0.26..0.33 while G
runs 0.077..0.18, a hue gradient from the shaded interior to the lit rim.  Moving
the big channel into green and the small one into red PRESERVES that gradient
instead of flattening it, so the green clumps keep the same internal modelling the
autumn ones have.  It is also exactly invertible, which is why `-- revert` can
exist without a sidecar of backed-up vertex data.

The coefficients are tuned so mean LUMINANCE is preserved (autumn 0.153 ->
0.158..0.168): the frame's value structure — what reads as near, far, lit, shaded
— does not move.  Only hue moves.  That is what makes this a palette change you
can ship without re-checking every composition.

DETERMINISTIC, NOT RANDOM.  Which clumps go green is sha1(name), never random(),
so this file re-run on this blend converts exactly the same clumps forever, and a
district rebuild that re-creates a clump under the same name gets the same
decision.  The probability is a function of the clump's distance from the river:

    d = (world zmin - the local water surface) + 0.6 * (horizontal distance to
        the river band)
    p = 0.52 at d <= 12  ->  0.12 at d >= 38   (linear between)

and the waterline is READ FROM THE BLEND (the m_water pools' own heights and
extents), not typed here, so a re-cut river moves the bias with it.

NOT TOUCHED, deliberately:
  * veg_gate_rimclump_1/2/11/12 and veg_gate_rimtreeE_0 — the five surgically
    edited gate occluders. Their vertex data is a hand-authored fix for the
    arrival framing and this pass writes vertex colour, so they are excluded
    outright rather than "excluded from geometry edits". They sit high on the
    gate rim where autumn is dominant anyway.
  * veg_farwallcrown_* — the north wall crown, 49..64 m above the water. That
    skyline IS the autumn identity; it stays whole.
  * mat_grass / mat_fern / mat_leaf_creeper — already green, and this is a
    measured first step, not a repaint.
"""
import bpy, os, sys, json, hashlib, collections

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/veg_greenmix.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = ("save" in argv) or ("--save" in argv)
REVERT = ("revert" in argv) or ("--revert" in argv)

# --------------------------------------------------------------------- the spec
SEED = "dellhollow-greenmix/"
ATTR = "Col"                              # the town's COLOR_0 convention
PAIRS = {                                 # autumn material -> derived green
    "mat_leaf_autumn": "mat_leaf_green",
    "mat_leaf_autumn_far": "mat_leaf_green_far",
}
FAR = "mat_leaf_autumn_far"

P_NEAR, P_FAR_END = 0.52, 0.12            # green probability at the two ends
D_NEAR, D_FAR_END = 12.0, 38.0            # ...of this distance-from-river ramp
P_FARCROWN = 0.25                         # the distant upstream crowns, flat rate
HD_WEIGHT = 0.6                           # horizontal metres per vertical metre

# r' = kr*g, g' = kg*r, b' = kb*b — t=0 fresh willow, t=1 olive/sage
KR = (0.72, 0.98)
KG = (0.66, 0.58)
KB = (1.40, 1.80)

PROTECTED = {"veg_gate_rimclump_1", "veg_gate_rimclump_2", "veg_gate_rimclump_11",
             "veg_gate_rimclump_12", "veg_gate_rimtreeE_0"}
SKIP_PREFIX = ("v10_src_", "veg_farwallcrown_")


def u01(name, salt=""):
    """Deterministic [0,1) from the object's name. Never random()."""
    h = hashlib.sha1((SEED + salt + name).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2.0 ** 64


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def fam(name):
    p = name.split("_")
    return "_".join(p[:2]) if len(p) > 1 else name


# ------------------------------------------------------- the river, read from the blend
def river_geometry():
    """The water surface heights and the river's plan band, measured off the
    m_water pools themselves so a re-cut river moves the palette bias with it."""
    segs, ymin, ymax = [], None, None
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if not any(m and m.name == "m_water" for m in ob.data.materials):
            continue
        ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
        if not ws:
            continue
        xs = [p.x for p in ws]; ys = [p.y for p in ws]; zs = [p.z for p in ws]
        segs.append((min(xs), max(xs), sum(zs) / len(zs)))
        ymin = min(ys) if ymin is None else min(ymin, min(ys))
        ymax = max(ys) if ymax is None else max(ymax, max(ys))
    assert segs, "no m_water pools found — cannot measure the waterline"
    segs.sort()
    return segs, ymin, ymax


SEGS, RY0, RY1 = river_geometry()


def water_z(x):
    for x0, x1, z in SEGS:
        if x0 <= x <= x1:
            return z
    return min(SEGS, key=lambda s: min(abs(x - s[0]), abs(x - s[1])))[2]


def river_dist(ob):
    bb = [ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box]
    zmin = min(v.z for v in bb)
    cx = sum(v.x for v in bb) / 8.0
    cy = sum(v.y for v in bb) / 8.0
    hd = 0.0 if RY0 <= cy <= RY1 else (RY0 - cy if cy < RY0 else cy - RY1)
    return (zmin - water_z(cx)) + HD_WEIGHT * hd, round(zmin - water_z(cx), 2), round(hd, 1)


# --------------------------------------------------------------- derived materials
def green_of(autumn_name):
    """Derive-by-name: a structural copy of the autumn material. Same node tree,
    same alpha cutout, same translucency — so glTF survival is unchanged by
    construction. The NAME is the payload."""
    gname = PAIRS[autumn_name]
    g = bpy.data.materials.get(gname)
    if g is None:
        src = bpy.data.materials[autumn_name]
        g = src.copy()
        g.name = gname
        print("  derived %s from %s" % (gname, autumn_name))
    return g


# --------------------------------------------------------------------- the pass
def leaf_objects():
    out, excluded = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        names = [m.name for m in ob.data.materials if m]
        au = [n for n in names if n in PAIRS]
        gr = [n for n in names if n in PAIRS.values()]
        if not (au or gr):
            continue
        if ob.name.startswith(SKIP_PREFIX) or ob.name in PROTECTED:
            excluded.append(ob.name)
            continue
        out.append((ob, au, gr))
    return sorted(out, key=lambda r: r[0].name), sorted(excluded)


def recolour(ob, slot_idx, kr, kg, kb, inverse=False):
    """Rewrite `Col` on the loops of the polygons wearing this material slot only —
    a clump that is half trunk (veg_gate_rimtreeE_0 carries mat_timber too) must
    not have its bark repainted."""
    me = ob.data
    a = me.color_attributes.get(ATTR)
    assert a is not None, "%s has no %r attribute" % (ob.name, ATTR)
    assert a.domain == 'CORNER', "%s: %r is %s, expected CORNER" % (ob.name, ATTR, a.domain)
    loops = []
    for poly in me.polygons:
        if poly.material_index == slot_idx:
            loops.extend(poly.loop_indices)
    n = 0
    for li in loops:
        c = a.data[li].color
        r, g, b, al = c[0], c[1], c[2], c[3]
        if inverse:
            nr, ng, nb = g / kg, r / kr, b / kb
        else:
            nr, ng, nb = kr * g, kg * r, kb * b
        a.data[li].color = (min(1.0, nr), min(1.0, ng), min(1.0, nb), al)
        n += 1
    return n


print("=" * 78)
print("VEG GREEN MIX  %s" % ("(REVERT)" if REVERT else ""))
print("=" * 78)
print("blend: %s" % bpy.data.filepath)
print("river: y band [%.1f, %.1f], %d water pools at z %s"
      % (RY0, RY1, len(SEGS), [round(s[2], 2) for s in SEGS]))
print("ramp:  p=%.2f at d<=%.0f  ->  p=%.2f at d>=%.0f ; far crowns flat %.2f"
      % (P_NEAR, D_NEAR, P_FAR_END, D_FAR_END, P_FARCROWN))

objs, excluded = leaf_objects()
tot = collections.Counter(); grn = collections.Counter()
band_t = collections.Counter(); band_g = collections.Counter()
converted, reverted, already, singled = [], [], 0, 0
BANDS = (("riverside d<18", 18.0), ("mid 18-30", 30.0), ("rim d>=30", 1e9))

for ob, au, gr in objs:
    f = fam(ob.name)
    tot[f] += 1
    is_far = (FAR in au) or (PAIRS[FAR] in gr)
    d, above, hd = river_dist(ob)
    p = P_FARCROWN if is_far else lerp(P_NEAR, P_FAR_END, (d - D_NEAR) / (D_FAR_END - D_NEAR))
    want_green = u01(ob.name) < p
    if REVERT:
        want_green = False
    if not is_far:
        for label, hi in BANDS:
            if d < hi:
                band_t[label] += 1
                band_g[label] += 1 if want_green else 0
                break

    t = u01(ob.name, "tone/")
    kr, kg, kb = lerp(*KR, t), lerp(*KG, t), lerp(*KB, t)

    if want_green and gr:
        already += 1
        grn[f] += 1
        continue
    if (not want_green) and au:
        continue                                   # already autumn, nothing to do

    # this object's mesh must not be shared, or its autumn siblings change too
    if ob.data.users > 1:
        ob.data = ob.data.copy()
        singled += 1

    names = [m.name if m else None for m in ob.data.materials]
    if want_green:
        for idx, src in [(i, n) for i, n in enumerate(names) if n in PAIRS]:
            recolour(ob, idx, kr, kg, kb, inverse=False)
            ob.data.materials[idx] = green_of(src)
        converted.append(dict(name=ob.name, family=f, d=round(d, 2), above=above,
                              hdist=hd, p=round(p, 3), tone=round(t, 3)))
        grn[f] += 1
    else:
        inv = {v: k for k, v in PAIRS.items()}
        for idx, src in [(i, n) for i, n in enumerate(names) if n in inv]:
            recolour(ob, idx, kr, kg, kb, inverse=True)
            ob.data.materials[idx] = bpy.data.materials[inv[src]]
        reverted.append(ob.name)

# ------------------------------------------------------------------------ report
town_t = sum(v for k, v in tot.items() if not k.startswith("veg_far"))
town_g = sum(v for k, v in grn.items() if not k.startswith("veg_far"))
print("\ncandidate clumps: %d   excluded: %d (%s)"
      % (len(objs), len(excluded),
         ", ".join("%s x%d" % (k, v) for k, v in
                   sorted(collections.Counter(
                       ("PROTECTED" if n in PROTECTED else fam(n)) for n in excluded).items()))))
print("converted this run: %d   already green: %d   reverted: %d   meshes un-shared: %d"
      % (len(converted), already, len(reverted), singled))
print("\nGREEN BY FAMILY")
for f in sorted(tot, key=lambda k: -tot[k]):
    print("   %-22s %3d/%3d  %3.0f%%" % (f + "_*", grn[f], tot[f], 100.0 * grn[f] / tot[f]))
print("   %-22s %3d/%3d  %3.0f%%   <- the town" % ("TOWN (excl. far)", town_g, town_t,
                                                   100.0 * town_g / max(1, town_t)))
print("\nRIVERSIDE BIAS (town clumps by distance from the water)")
for label, _ in BANDS:
    if band_t[label]:
        print("   %-16s %3d/%3d  %3.0f%%" % (label, band_g[label], band_t[label],
                                             100.0 * band_g[label] / band_t[label]))

if not REVERT:
    json.dump(dict(
        _doc=("GENERATED by tools/veg_greenmix.py — the deterministic green set. "
              "Re-derived from sha1(object name) on every run; committed so the "
              "assignment is reviewable without opening the blend."),
        generator="tools/veg_greenmix.py",
        params=dict(seed=SEED, p_near=P_NEAR, p_far=P_FAR_END, d_near=D_NEAR,
                    d_far=D_FAR_END, p_farcrown=P_FARCROWN, hd_weight=HD_WEIGHT,
                    kr=KR, kg=KG, kb=KB),
        river=dict(y_band=[round(RY0, 2), round(RY1, 2)],
                   pools=[[round(a, 2), round(b, 2), round(z, 2)] for a, b, z in SEGS]),
        protected=sorted(PROTECTED),
        counts=dict(candidates=len(objs), town_green=town_g, town_total=town_t,
                    by_family={k: [grn[k], tot[k]] for k in sorted(tot)},
                    by_band={k: [band_g[k], band_t[k]] for k, _ in BANDS if band_t[k]}),
        green=sorted([c["name"] for c in converted] +
                     [o.name for o, au, gr in objs if gr and o.name not in
                      {c["name"] for c in converted}]),
    ), open(MANIFEST, "w"), indent=1)
    print("\nmanifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `-- save` to write the master)")
