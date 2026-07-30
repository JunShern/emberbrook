"""t2_hut_paint.py — PAINT THE LOCKFOOT HUTS' WALLS.  The P2 mechanism of
docs/plans/pops-of-color.md, done the way that plan actually defines P2.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_hut_paint.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_hut_paint.py -- revert save

WHY THIS EXISTS AND WHY IT IS NOT NEW GEOMETRY.  pops-of-color.md's rows W3
(hut doors), W4 (hut shutters) and LH5/LH6 are filed under phase P2, which the
plan defines as "material-slot and `Col` edits on EXISTING meshes, not new
geometry".  Built instead as free-standing painted plates they cannot be mounted
at all, and the measurement is unambiguous: the `lf_` kit's nine huts OVERLAP
EACH OTHER IN X while standing at different y, so one 10 m door band crosses
three huts whose north faces are up to 0.9 m apart, and `geometry_audit` catches
the plates 0.08-0.14 m inside `wv_hut_weave-huts_1` and `_2` however they are
snapped — from the centre, from outside, per-panel, at any offset.  So the
plates were dropped and this is the correct mechanism.

WHAT THE HUTS ALREADY HAVE, measured before touching anything, because
house-variety-design.md's finding was that the WALLS already vary and it is
worth checking whether that is still true:

    wv_hut_pilot-cluster_0   lf_deck (0.83, 0.45, 0.34)  terracotta
    wv_hut_pilot-cluster_1   lf_deck (0.58, 0.62, 0.44)  sage
    wv_hut_pilot-cluster_2   lf_deck (0.89, 0.67, 0.37)  ochre
    wv_hut_weave-huts_0      lf_deck (0.60, 0.64, 0.45)  sage      <- clashes
    wv_hut_weave-huts_1      lf_deck (0.94, 0.81, 0.58)  bone
    wv_hut_weave-huts_2      lf_deck (0.55, 0.68, 0.75)  pale blue
    wv_hut_weave-north_0     lf_deck (0.53, 0.66, 0.72)  pale blue <- clashes

They do vary.  So this pass is NOT a rescue, it is a tightening, and it does
three specific things:

  1. RESOLVES THE NEIGHBOUR CLASHES.  Assignment is `sha1(object name)` over the
     six-accent storybook set with a neighbour pass at 9 m in plan — the same
     mechanism, radius and seed discipline `tools/house_variety.py` uses for the
     roofs.  Never `random()`.
  2. PUSHES THE HUES OUT.  Several wall colours sit close to the town's timber.
     Each loop is moved a fixed fraction toward its hut's accent HUE while its
     own LUMINANCE IS HELD exactly, so the golden key keeps doing the unifying
     and no composition needs re-checking.  That is the same rule the green mix
     and the roof pass were built on.
  3. LEAVES THE ROOFS AND THE GLASS ALONE.  Only the `lf_deck` and `lf_stone`
     slots are touched.  The `lf_shingle*` slots carry the four house-variety
     shingle variants and their own `Col`, and rewriting those loops would
     scramble a ratified pass; `lf_glass` is the lit windows.

A MEASUREMENT FINDING WORTH RECORDING, because it partly explains why the
eastern cameras score so low and it is NOT something more paint can fix:
`lf_deck` and `lf_stone` are kit materials, and the chroma metric in
`tools/t2_probe_report.py` counts only the named accent materials
(`mat_*_paint_*`, `mat_flag_*`, the cloths, `mat_pumpkin`).  So the Lockfoot
huts' painted walls DO NOT COUNT as chromatic pixels however bright they are.
The 0.11%-at-crossing figure is therefore part real and part definitional.  The
definition is not changed here — every number in all three tranche-2 plans is
written against it, and moving the goalposts mid-tranche would make them
incomparable — but the flag belongs in the record.

REVERT is exact: every changed loop's original colour is stored on the object
before it is written.
"""
import bpy, os, sys, json, hashlib
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_hut_paint.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

SEED = "dellhollow-hutwall/"
NEIGHBOUR_M = 9.0
WALL_SLOTS = ("lf_deck", "lf_stone")
BLEND = 0.62               # how far a loop moves toward its accent's chroma
PROP = "t2h_paint"

# the six-accent storybook set, as linear RGB, read from the shipped materials
ACCENTS = ["rust", "madder", "ochre", "bone", "teal", "slate", "sage"]
PAINT = {
    "rust": "mat_shelf_paint_rust", "madder": "mat_shelf_paint_madder",
    "ochre": "mat_shelf_paint_ochre", "bone": "mat_shelf_paint_bone",
    "teal": "mat_shelf_paint_teal", "slate": "mat_shelf_paint_slate",
    "sage": "mat_shelf_paint_green",
}
PAINT_NODE, PAINT_SOCK = "Mix.003", "B"
MOSS = (0.09, 0.16, 0.05)


def paint_rgb(key):
    m = bpy.data.materials[PAINT[key]]
    nd = m.node_tree.nodes.get(PAINT_NODE)
    if nd is not None:
        for i in nd.inputs:
            if i.name == PAINT_SOCK and not i.is_linked and hasattr(i.default_value, '__len__') \
                    and len(i.default_value) == 4:
                rgb = tuple(i.default_value[:3])
                if rgb not in ((0.0, 0.0, 0.0), (0.5, 0.5, 0.5)) and rgb != MOSS:
                    return rgb
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    return tuple(b.inputs['Base Color'].default_value[:3]) if b else (0.5, 0.5, 0.5)


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def u01(name, salt=""):
    return int.from_bytes(hashlib.sha1((SEED + salt + name).encode()).digest()[:8],
                          "big") / float(1 << 64)


HUTS = sorted(o.name for o in bpy.data.objects
              if o.type == 'MESH' and o.name.startswith("wv_hut"))

# ================================================================ REVERT ======
if REVERT:
    n = 0
    for hn in HUTS:
        ob = bpy.data.objects.get(hn)
        if ob is None or not ob.get(PROP):
            continue
        ca = ob.data.color_attributes.active_color
        for idx, col in json.loads(ob[PROP]):
            ca.data[idx].color = col
        del ob[PROP]
        n += 1
        print("REVERTED %s" % hn)
    print("REVERT restored %d huts" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ============================================================== ASSIGN ========
def plan_xy(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (sum(v.x for v in bb) / 8.0, sum(v.y for v in bb) / 8.0)


pos = {h: plan_xy(bpy.data.objects[h]) for h in HUTS}
target = {}
for h in HUTS:
    pick = ACCENTS[int(u01(h) * len(ACCENTS)) % len(ACCENTS)]
    # neighbour pass: bump any hut matching an already-assigned hut inside 9 m
    for _ in range(len(ACCENTS)):
        clash = any(target.get(o) == pick and
                    ((pos[h][0] - pos[o][0]) ** 2 + (pos[h][1] - pos[o][1]) ** 2) ** 0.5 < NEIGHBOUR_M
                    for o in target)
        if not clash:
            break
        pick = ACCENTS[(ACCENTS.index(pick) + 3) % len(ACCENTS)]
    target[h] = pick

print("=" * 78)
print("HUT WALL ASSIGNMENT — sha1(name), neighbour-difference at %.0f m" % NEIGHBOUR_M)
print("=" * 78)
report = {}
for h in HUTS:
    ob = bpy.data.objects[h]
    if ob.get(PROP):
        print("  %-24s already painted" % h)
        continue
    key = target[h]
    acc = paint_rgb(key)
    acc_l = lum(acc)
    ca = ob.data.color_attributes.active_color
    if ca is None:
        print("  %-24s no Col" % h)
        continue
    slots = [s.material.name if s.material else None for s in ob.material_slots]
    wall_idx = {i for i, m in enumerate(slots) if m in WALL_SLOTS}
    me = ob.data
    undo, n = [], 0
    seen = set()
    for p in me.polygons:
        if p.material_index not in wall_idx:
            continue
        for li in p.loop_indices:
            k = li if ca.domain == 'CORNER' else me.loops[li].vertex_index
            if k in seen:
                continue
            seen.add(k)
            c = list(ca.data[k].color)
            L = lum(c)
            if acc_l < 1e-5:
                continue
            # the accent's HUE at THIS loop's luminance — the roof pass's rule
            tgt = [acc[i] * (L / acc_l) for i in range(3)]
            new = [c[i] * (1.0 - BLEND) + tgt[i] * BLEND for i in range(3)]
            # renormalise so luminance is held EXACTLY, not approximately
            nl = lum(new)
            if nl > 1e-5:
                new = [v * (L / nl) for v in new]
            undo.append([k, list(c)])
            ca.data[k].color = (min(1.0, new[0]), min(1.0, new[1]), min(1.0, new[2]), c[3])
            n += 1
    if n:
        ob[PROP] = json.dumps(undo)
    report[h] = dict(accent=key, rgb=[round(v, 3) for v in acc], loops=n,
                     at=[round(v, 1) for v in pos[h]])
    print("  %-24s %-7s %-22s %4d wall loops (%s)"
          % (h, key, str(tuple(round(v, 3) for v in acc)), n, ",".join(sorted(WALL_SLOTS))))

# neighbour audit — measured, not asserted, exactly as house_variety reports it
close = []
for i, a in enumerate(HUTS):
    for b in HUTS[i + 1:]:
        if target[a] == target[b]:
            d = ((pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2) ** 0.5
            if d < NEIGHBOUR_M:
                close.append((d, a, b, target[a]))
print("\nNEIGHBOUR AUDIT (target: no same-accent pair inside %.0f m)" % NEIGHBOUR_M)
for d, a, b, v in sorted(close):
    print("   %.1f m  %s / %s  both %s" % (d, a, b, v))
print("   %d same-accent pair(s) inside the radius, of %d huts" % (len(close), len(HUTS)))

json.dump(dict(
    _doc=("GENERATED by tools/t2_hut_paint.py — the Lockfoot huts' wall accents. "
          "Pure function of object names and positions; luminance is held per "
          "loop, so only hue moves."),
    generator="tools/t2_hut_paint.py", plan="docs/plans/pops-of-color.md",
    seed=SEED, neighbour_m=NEIGHBOUR_M, blend=BLEND, wall_slots=list(WALL_SLOTS),
    accents=ACCENTS, huts=report, neighbour_clashes=len(close),
    _metric_note=("lf_deck / lf_stone are KIT materials and are NOT in the chroma "
                  "probe's accent set, so these walls do not register as chromatic "
                  "pixels however bright they are. The definition is deliberately "
                  "left unchanged: all three tranche-2 plans are written against it."),
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
