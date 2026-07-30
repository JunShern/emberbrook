"""t2_cliff_east.py — CLOSE THE DOWNSTREAM GORGE.  Phase C2 of
docs/plans/cliff-completion.md.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_east.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_east.py -- revert save

THE FINDING THIS ANSWERS.  Of the seventeen solved cameras only TWO leak the
world background once FX cards are skipped, and they are the same hole from two
angles: `lockfive` at 19.96% and `cottage-steps` at 16.26%.  73% and 54% of
those leak rays point DOWNWARD, and a downward ray that hits nothing in a valley
town is unambiguously a hole, not sky.  East of the town the world simply stops:
`lf_ground` ends at x = 112.1, `lf_riverbed_tail` at 131.0, the old `cliff_town`
at 135.0, `cliff_far` at 150.0.  The rays fly out over the downstream gorge and
never come back.

The investigation traced all 10,384 leak rays against candidate closure planes.
A single wall at **x = 140 spanning y -8..54, z -14..22** catches
**10,384 of 10,384 — 100%**.  That is the entire geometric requirement for the
void problem: one panel.

THREE PIECES, and only the first is load-bearing:

  east_closure    x 140, y -13..54, z -16..26, 2.0 m edges — the traced
                  requirement is y -8..54 / z -14..22 and this is that panel
                  with a margin, because the closure carries its own relief and
                  therefore stands up to 9 m EAST of the traced plane, where the
                  same rays arrive slightly lower and wider.  Pure
                  silhouette at 60-100 m from the only two cameras that see it,
                  so it gets a plain lean-and-swell profile, not the south
                  wall's seven octaves.  It wears `mat_rock_farwall` — and here
                  that material is CORRECT: at 60-100 m its blue-grey recession
                  tint is doing exactly the job it was authored for, which is
                  the opposite of the situation on the south wall at 33 m (see
                  tools/t2_cliff_south.py).

  fx_haze_east    a volume-scatter slab at x 124..130, in front of the closure,
                  so the gorge reads as distance rather than as a wall.  Mirrors
                  `fx_haze_mid` exactly — Volume Scatter, no surface, density
                  scaled to hold the same OPTICAL DEPTH across a thinner slab.

  fx_haze_south   the fourth haze card cliff-completion.md calls optional.  It
                  is not optional any more: the south wall is now built in
                  `mat_rock_townwall`, a warm un-hazed rock, precisely so that
                  its recession comes from atmosphere instead of from a tint
                  baked into its albedo.  This is that atmosphere.  A thin slab
                  lying against the wall's face (y -2.4..0.3) over its whole run.

  fx_ridge_upstream_skirt
                  `shelf-east` leaks 22 pixels (0.08%) at azimuth 181-182 deg:
                  the ray passes UNDER `fx_ridge_upstream`, whose bbox bottoms
                  out at z = -9.09 while the ray is at z ~ -34 by then.  The
                  plan says extend that ridge's toe down 15 m.  This adds a
                  SKIRT object below it instead of editing the ridge's vertex
                  data — same closure, and `-- revert` is a delete rather than
                  an inverse transform on a mesh someone else built.

Everything here is new objects only.  Nothing existing is edited, so revert is
exact and total.
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_cliff_east.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

WALL = "cliff_east_closure"
COLL = "CONTEXT"
MAT = "mat_rock_farwall"

# the traced closure plane: 10,384 / 10,384 leak rays caught
EX = 140.0
EY0, EY1 = -13.0, 54.0
EZ0, EZ1 = -16.0, 26.0
EDGE = 2.0

# haze slabs: (name, material, x0,x1, y0,y1, z0,z1, colour, optical depth)
# fx_haze_mid is the reference: density 0.0034 over a 24 m slab = 0.0816 tau.
HAZE = [
    ("fx_haze_east", "mat_haze_east", 124.0, 130.0, -10.0, 56.0, -16.0, 26.0,
     (0.48, 0.50, 0.60), 0.055),
    ("fx_haze_south", "mat_haze_south", -35.0, 137.0, -2.4, 0.3, -15.0, 38.0,
     (0.48, 0.50, 0.60), 0.075),
]

SKIRT = "fx_ridge_upstream_skirt"
SKIRT_SRC = "fx_ridge_upstream"
SKIRT_Z = -62.0

NAMES = [WALL, SKIRT] + [h[0] for h in HAZE]


def new_mesh(name, verts, faces, mat, cname, smooth=True):
    old = bpy.data.objects.get(name)
    if old:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if smooth:
        for poly in me.polygons:
            poly.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    (bpy.data.collections.get(cname) or bpy.context.scene.collection).objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, cname):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
         (2, 6, 7, 3), (3, 7, 4, 0)]
    return new_mesh(name, v, f, mat, cname, smooth=False)


# ================================================================ REVERT ======
if REVERT:
    gone = []
    for n in NAMES:
        o = bpy.data.objects.get(n)
        if o:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
            gone.append(n)
    for _, mn, *_ in HAZE:
        m = bpy.data.materials.get(mn)
        if m is not None and m.users == 0:
            bpy.data.materials.remove(m)
    print("REVERT removed: %s" % (", ".join(gone) or "nothing"))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ============================================================== THE WALL ======
mat = bpy.data.materials[MAT]


def edepth(y, z):
    """how far EAST of x = 140 the closure stands.  Pure silhouette at 60-100 m:
    a lean and two swells, nothing that would repay a seventh octave."""
    d = 0.0
    d += 2.6 * math.sin(y * 0.052 + 0.9) + 1.5 * math.sin(y * 0.021 - 2.1)
    d += 0.9 * math.sin(y * 0.190 + z * 0.06 + 1.7)
    d += 0.35 * math.sin(y * 0.610 - z * 0.31)
    d += 0.14 * max(0.0, z + 4.0)              # leans away as it rises
    return d


ny = max(2, int(round((EY1 - EY0) / EDGE)) + 1)
nz = max(2, int(round((EZ1 - EZ0) / EDGE)) + 1)
verts, faces = [], []
for i in range(ny):
    y = EY0 + (EY1 - EY0) * i / (ny - 1)
    for j in range(nz):
        z = EZ0 + (EZ1 - EZ0) * j / (nz - 1)
        verts.append((EX + edepth(y, z), y, z))
for i in range(ny - 1):
    for j in range(nz - 1):
        a = i * nz + j
        faces.append((a, a + 1, a + nz + 1, a + nz))
# cap the top back to x = 150 so no ray can sail over the sheet's rim, the same
# way the south wall's cap reproduces the placeholder box's top face
base = len(verts)
verts += [(150.0, EY0 + (EY1 - EY0) * i / (ny - 1), EZ1) for i in range(ny)]
for i in range(ny - 1):
    a = i * nz + (nz - 1)
    faces.append((a, base + i, base + i + 1, (i + 1) * nz + (nz - 1)))
w = new_mesh(WALL, verts, faces, mat, COLL)
print("BUILT %-26s %5d verts %5d polys   x %.0f(+relief) y %.0f..%.0f z %.0f..%.0f  edge %.1f m"
      % (WALL, len(verts), len(faces), EX, EY0, EY1, EZ0, EZ1, EDGE))

# =============================================================== THE HAZE =====
for name, mn, x0, x1, y0, y1, z0, z1, col, tau in HAZE:
    m = bpy.data.materials.get(mn)
    if m is None:
        m = bpy.data.materials.new(mn)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nt.nodes.remove(n)
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        vs = nt.nodes.new('ShaderNodeVolumeScatter')
        vs.location = (-220, 0)
        nt.links.new(vs.outputs['Volume'], out.inputs['Volume'])
    vs = next(n for n in m.node_tree.nodes if n.type == 'VOLUME_SCATTER')
    thick = min(x1 - x0, y1 - y0)
    vs.inputs['Color'].default_value = (col[0], col[1], col[2], 1.0)
    vs.inputs['Density'].default_value = tau / thick
    vs.inputs['Anisotropy'].default_value = 0.3
    ob = box(name, x0, x1, y0, y1, z0, z1, m, COLL)
    # SHADOW OFF, and it is not a nicety.  Every haze card the town already
    # carries has visible_shadow = False; the first take of these two did not,
    # and a thin slab lying along the wall is very nearly PARALLEL to the key
    # (SUN_key rakes at (-0.55, 0.73, -0.41)), so the light's path inside it ran
    # tens of metres instead of three.  The slab stopped being atmosphere and
    # became an opaque curtain: the gate frame's whole south wall rendered
    # BLACK.  Matching the kit's flags fixes it.
    ob.visible_shadow = False
    print("BUILT %-26s volume-scatter slab %.1f m thick, density %.5f (tau %.3f), "
          "colour %s" % (name, thick, tau / thick, tau, col))

# ============================================================== THE SKIRT =====
src = bpy.data.objects.get(SKIRT_SRC)
if src is None:
    print("  %s missing — skirt skipped" % SKIRT_SRC)
else:
    bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
    sx0, sx1 = min(v.x for v in bb), max(v.x for v in bb)
    sy0, sy1 = min(v.y for v in bb), max(v.y for v in bb)
    sz = min(v.z for v in bb)
    box(SKIRT, sx0, sx1, sy0, sy1, SKIRT_Z, sz + 0.30,
        bpy.data.materials[src.material_slots[0].material.name], COLL)
    print("BUILT %-26s under %s: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  (closes "
          "shelf-east's 22-pixel hairline)" % (SKIRT, SKIRT_SRC, sx0, sx1, sy0, sy1,
                                               SKIRT_Z, sz + 0.30))

json.dump(dict(
    _doc=("GENERATED by tools/t2_cliff_east.py — the downstream closure, the "
          "east and south haze slabs, and the upstream ridge skirt."),
    generator="tools/t2_cliff_east.py", plan="docs/plans/cliff-completion.md",
    closure=dict(name=WALL, plane_x=EX, y=[EY0, EY1], z=[EZ0, EZ1], edge_m=EDGE,
                 material=MAT, verts=len(verts), polys=len(faces),
                 rays_caught="10384/10384"),
    haze=[dict(name=h[0], material=h[1], x=[h[2], h[3]], y=[h[4], h[5]],
               z=[h[6], h[7]], colour=list(h[8]), tau=h[9]) for h in HAZE],
    skirt=dict(name=SKIRT, under=SKIRT_SRC, to_z=SKIRT_Z),
    objects=NAMES,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
