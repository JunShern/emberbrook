"""house_variety.py — give Dellhollow's houses more than one roof.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/house_variety.py
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/house_variety.py -- save
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/house_variety.py -- revert save

THE NOTE THIS ANSWERS: "a lot of the town buildings seem to be baked in green
colour."  The full topology is in docs/plans/house-variety-design.md; the short
version is that the brief's assumption was wrong in a useful way.

The WALLS already vary.  Measured before touching anything: the nine weave huts
carry five distinct wall colours in their lf_deck vertex Col and no two adjacent
huts match today; the shelf shop row already runs five paints across seven
buildings.  What does NOT vary is the roof — Dellhollow has exactly two roof
materials and both are green:

    mat_shingle_mossy   tint literal (0.125, 0.215, 0.080)   17 objects
    lf_shingle          vertex Col   (0.155, 0.174, 0.090)   10 objects

Twenty-seven roofs in one colour.  In a 3/4 top-down FF-grammar camera the roof
is most of what you see of a building, so one roof colour reads as one TOWN
colour.  That is the whole finding, and roofs are therefore the whole pass.

TWO MECHANISMS, because the town has two kits.
  * mat_shingle_mossy is the standard kit template: a greyscale photo texture
    under one literal RGB in a Mix node.  A variant is a material copy with that
    one socket changed — the cheapest possible edit, and reviewable at a glance.
  * lf_shingle is the Lockfoot kit, whose Mix sits at factor 1.0 so the image is
    fully overridden and the colour is the mesh's `Col` attribute (the same
    survivability shape the foliage uses).  A variant here means recolouring Col,
    exactly as tools/veg_greenmix.py does, by a FIXED per-variant channel scale
    against the kit's canonical mean — fixed, not per-object, so the transform is
    exactly invertible and every roof keeps its own baked variation.

LUMINANCE IS HELD (0.144..0.202 against moss's 0.186; the lf_ set lands within
1% of the kit's 0.164).  Same principle as the green mix: the golden-hour key
does the unifying, so only hue moves and no composition needs re-checking.  A
dark slate roof reading darker than a bleached shake roof is the point, not drift.

ASSIGNMENT IS DETERMINISTIC AND NEIGHBOUR-AWARE.  sha1(object name), never
random().  Moss is weighted 2-in-5 so green stays the town's primary colour per
the ruling rather than becoming one flavour among four.  Then a neighbour pass
walks the roofs in name order and bumps any roof matching an already-assigned
roof within NEIGHBOUR_M metres in plan — two building widths, which is the
distance at which two roofs share a frame.  The weave hut row and the shelf shop
row are the visible test cases; both are inside that radius.

ALSO HERE, because it is two sockets and it completes the palette: the shelf row
had five paints across seven buildings, doubling up on green and teal.  The two
duplicates become madder and slate blue, giving the row seven distinct panels and
completing the six-accent storybook set the brief asks for — of which the kit
already contained five.  Neither repainted building has an interior scene, so no
exterior/interior door-and-trim divergence is created.

NOT TOUCHED, deliberately: the moss overlay literal (0.09, 0.16, 0.05) that a
dozen materials spray on every up-facing surface.  It is the town's second green
and the reason even repainted walls trend green, but it is a cross-cutting change
to a dozen materials and belongs in its own pass with its own taste gate.  The
dam, the gate arch, the gate yard and the notice board keep their moss roofs:
they are terrain and props, not houses.
"""
import bpy, os, sys, json, hashlib, collections
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/house_variety.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = ("save" in argv) or ("--save" in argv)
REVERT = ("revert" in argv) or ("--revert" in argv)

SEED = "dellhollow-houseroof/"
ATTR = "Col"
NEIGHBOUR_M = 9.0

# moss twice: green stays the town's primary roof, not one flavour among four
WEIGHTED = ["moss", "moss", "cedar", "slate", "shake"]
VARIANTS = ["moss", "cedar", "slate", "shake"]

# --- kit A: the tint-literal roof (mat_shingle_mossy) --------------------------
TINT_BASE = "mat_shingle_mossy"
TINT_NODE, TINT_SOCK = "Mix.001", "B"
TINT = {                                   # linear RGB, luminance in the docstring
    "moss":  (0.125, 0.215, 0.080),        # unchanged — the original
    "cedar": (0.245, 0.145, 0.080),        # weathered warm cedar
    "slate": (0.130, 0.145, 0.175),        # dark blue-grey slate
    "shake": (0.225, 0.200, 0.150),        # sun-bleached shake
}
TINT_MAT = {"moss": TINT_BASE, "cedar": "mat_shingle_cedar",
            "slate": "mat_shingle_slate", "shake": "mat_shingle_shake"}

# --- kit B: the Lockfoot vertex-colour roof (lf_shingle) -----------------------
VCOL_BASE = "lf_shingle"
KIT_MEAN = (0.1550, 0.1740, 0.0900)        # measured; the fixed reference
VCOL_TARGET = {
    "moss":  (0.1550, 0.1740, 0.0900),
    "cedar": (0.2500, 0.1460, 0.0830),
    "slate": (0.1480, 0.1650, 0.2000),
    "shake": (0.1850, 0.1650, 0.1240),
}
VCOL_MAT = {"moss": VCOL_BASE, "cedar": "lf_shingle_cedar",
            "slate": "lf_shingle_slate", "shake": "lf_shingle_shake"}
VCOL_K = {v: tuple(VCOL_TARGET[v][i] / KIT_MEAN[i] for i in range(3)) for v in VARIANTS}

# terrain and props, not houses — they keep their moss
NOT_A_HOUSE = {"lock_four_dam", "gate_arch", "gate_yard", "qm_notice_board"}

# --- the shelf row's two duplicate paints -------------------------------------
PAINT_NODE, PAINT_SOCK = "Mix.003", "B"
PAINT_DERIVE = {                           # new name: (template, tint)
    "mat_shelf_paint_madder": ("mat_shelf_paint_rust", (0.46, 0.19, 0.17)),
    "mat_shelf_paint_slate":  ("mat_shelf_paint_teal", (0.24, 0.30, 0.41)),
}
REPAINT = {                                # object: (from, to)
    "shelf_home_a": ("mat_shelf_paint_green", "mat_shelf_paint_madder"),
    "shelf_home_c": ("mat_shelf_paint_teal",  "mat_shelf_paint_slate"),
}


def u01(name, salt=""):
    return int.from_bytes(hashlib.sha1((SEED + salt + name).encode()).digest()[:8],
                          "big") / 2.0 ** 64


def color_input(node, sock):
    """ShaderNodeMix carries A/B three times over (float, vector, colour). Only
    the 4-component one is the colour, and picking by name alone gets the float."""
    for i in node.inputs:
        if i.name == sock and hasattr(i, "default_value"):
            try:
                if len(i.default_value) == 4:
                    return i
            except TypeError:
                continue
    raise KeyError("no colour input %r on %s" % (sock, node.name))


def plan_xy(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (sum(v.x for v in bb) / 8.0, sum(v.y for v in bb) / 8.0)


def faces_of(ob, slot):
    return [li for p in ob.data.polygons if p.material_index == slot
            for li in p.loop_indices]


# ------------------------------------------------------------ derive materials
def derive_tint(variant):
    name = TINT_MAT[variant]
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials[TINT_BASE].copy()
        m.name = name
        color_input(m.node_tree.nodes[TINT_NODE], TINT_SOCK).default_value = \
            TINT[variant] + (1.0,)
        print("  derived %s (tint %s)" % (name, TINT[variant]))
    return m


def derive_vcol(variant):
    name = VCOL_MAT[variant]
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials[VCOL_BASE].copy()
        m.name = name
        print("  derived %s (Col scale %s)"
              % (name, tuple(round(k, 3) for k in VCOL_K[variant])))
    return m


def derive_paints():
    for name, (template, tint) in PAINT_DERIVE.items():
        if bpy.data.materials.get(name) is None:
            m = bpy.data.materials[template].copy()
            m.name = name
            color_input(m.node_tree.nodes[PAINT_NODE], PAINT_SOCK).default_value = \
                tint + (1.0,)
            print("  derived %s from %s (tint %s)" % (name, template, tint))


# ------------------------------------------------------------------ the roofs
def roof_objects():
    """Every object with REAL roof faces in one of the two roof kits, tagged with
    the kit and its current variant (read from the material it wears)."""
    tint_names = {v: k for k, v in TINT_MAT.items()}
    vcol_names = {v: k for k, v in VCOL_MAT.items()}
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name in NOT_A_HOUSE:
            continue
        for slot, m in enumerate(ob.data.materials):
            if m is None:
                continue
            if m.name in tint_names:
                if any(p.material_index == slot for p in ob.data.polygons):
                    out.append((ob, "tint", slot, tint_names[m.name]))
            elif m.name in vcol_names:
                if faces_of(ob, slot):
                    out.append((ob, "vcol", slot, vcol_names[m.name]))
    return sorted(out, key=lambda r: r[0].name)


def assign(roofs):
    """Deterministic per name, then a neighbour-difference pass. Nothing here
    reads the CURRENT state, so the target assignment is a pure function of the
    town's names and positions — a re-run cannot drift."""
    chosen, placed = {}, []
    for ob, kit, slot, _cur in roofs:
        n = ob.name
        order = [WEIGHTED[int(u01(n) * len(WEIGHTED))]]
        order += sorted(VARIANTS, key=lambda v: u01(n, "pick/" + v))
        x, y = plan_xy(ob)

        def nearest_same(cand):
            d = [((px - x) ** 2 + (py - y) ** 2) ** 0.5
                 for px, py, v in placed if v == cand]
            return min(d) if d else float("inf")

        pick = next((c for c in order if nearest_same(c) >= NEIGHBOUR_M), None)
        if pick is None:
            # A dense cluster can surround a roof with all four colours inside the
            # radius — the weave-north knot does exactly that. Then the constraint
            # is unsatisfiable and the honest move is to maximise separation
            # rather than fall back to an arbitrary first choice.
            pick = max(order, key=nearest_same)
        chosen[n] = pick
        placed.append((x, y, pick))
    return chosen


def recolour(ob, slot, k, inverse=False):
    a = ob.data.color_attributes.get(ATTR)
    assert a is not None, "%s has no %r" % (ob.name, ATTR)
    n = 0
    for li in faces_of(ob, slot):
        c = a.data[li].color
        if inverse:
            a.data[li].color = (c[0] / k[0], c[1] / k[1], c[2] / k[2], c[3])
        else:
            a.data[li].color = (min(1.0, c[0] * k[0]), min(1.0, c[1] * k[1]),
                                min(1.0, c[2] * k[2]), c[3])
        n += 1
    return n


print("=" * 78)
print("HOUSE VARIETY — roofs  %s" % ("(REVERT)" if REVERT else ""))
print("=" * 78)
print("blend: %s" % bpy.data.filepath)

roofs = roof_objects()
target = {ob.name: "moss" for ob, _, _, _ in roofs} if REVERT else assign(roofs)

changed, kept = [], 0
for ob, kit, slot, cur in roofs:
    want = target[ob.name]
    if want == cur:
        kept += 1
        continue
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    if kit == "tint":
        ob.data.materials[slot] = derive_tint(want)
    else:
        # via the base: fixed coefficients make the chain exactly invertible
        recolour(ob, slot, VCOL_K[cur], inverse=True)
        recolour(ob, slot, VCOL_K[want], inverse=False)
        ob.data.materials[slot] = derive_vcol(want)
    changed.append((ob.name, kit, cur, want))

# ------------------------------------------------------------- the two paints
paint_changed = []
if not REVERT:
    derive_paints()
for obname, (frm, to) in REPAINT.items():
    ob = bpy.data.objects.get(obname)
    if ob is None:
        continue
    want, other = (frm, to) if REVERT else (to, frm)
    names = [m.name if m else None for m in ob.data.materials]
    if want in names:
        continue
    if other in names:
        ob.data.materials[names.index(other)] = bpy.data.materials[want]
        paint_changed.append((obname, other, want))

# ------------------------------------------------------------------- report
print("\nroof objects: %d   changed: %d   already correct: %d"
      % (len(roofs), len(changed), kept))
for n, kit, a, b in changed:
    print("   %-24s %-5s %-6s -> %s" % (n, kit, a, b))
dist = collections.Counter(target.values())
print("\nROOF DISTRIBUTION")
for v in VARIANTS:
    print("   %-6s %2d/%2d  %3.0f%%" % (v, dist[v], len(roofs),
                                        100.0 * dist[v] / max(1, len(roofs))))
print("\nPAINT: %s" % (", ".join("%s %s->%s" % p for p in paint_changed) or "no change"))

# Neighbour audit — measured, not asserted. With four colours a roof surrounded
# by four differently-roofed neighbours inside the radius cannot be satisfied, so
# the number to report is how CLOSE the closest same-colour pair ends up, and
# where. Zero pairs under the radius is the goal; the residue is named.
pos = {ob.name: plan_xy(ob) for ob, _, _, _ in roofs}
names = sorted(pos)
close = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if target[a] == target[b]:
            d = ((pos[a][0] - pos[b][0]) ** 2 + (pos[a][1] - pos[b][1]) ** 2) ** 0.5
            if d < NEIGHBOUR_M:
                close.append((d, a, b, target[a]))
viol = len(close)
print("\nNEIGHBOUR AUDIT (target: no same-colour pair inside %.0f m)" % NEIGHBOUR_M)
for d, a, b, v in sorted(close):
    print("   %.1f m  %s / %s  both %s  (cluster over-subscribed)" % (d, a, b, v))
print("   %d same-colour pair(s) inside the radius, of %d roofs"
      % (viol, len(roofs)))

if not REVERT:
    json.dump(dict(
        _doc=("GENERATED by tools/house_variety.py — the deterministic roof "
              "assignment. Pure function of object names and positions; committed "
              "so the palette is reviewable without opening the blend."),
        generator="tools/house_variety.py",
        params=dict(seed=SEED, weighted=WEIGHTED, neighbour_m=NEIGHBOUR_M,
                    tint=TINT, vcol_target=VCOL_TARGET, kit_mean=KIT_MEAN),
        roofs={n: target[n] for n in sorted(target)},
        distribution={v: dist[v] for v in VARIANTS},
        repaint={k: v[1] for k, v in REPAINT.items()},
        not_a_house=sorted(NOT_A_HOUSE),
        neighbour_clashes=viol,
    ), open(MANIFEST, "w"), indent=1)
    print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `-- save` to write the master)")
