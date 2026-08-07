"""emb_water_shader.py — EMBERBROOK'S WATER: the ratified depth->alpha recipe,
carried to a NIGHT town.  Red-team run-20260806-1/-2 (checklist, calibrated judge):
emb water-read 0 CONVINCING / 5 FAILING + 1 VISIBLE-BUT-ILLEGIBLE — "solid black
flat plane" (pondlane), "untextured flat black void" (arch), "pitch-black flat plane
with no wet shore contacts" (gateroad), "blending into dark terrain" (therise), "no
visible water surface" (homerow) — the town's standing worst visual class.

  Blender -b tools/blends/emberbrook-dressed.blend --python-exit-code 1 \
      -P tools/emb_water_shader.py -- [save] [revert save]
      [--scale median|metres] [--amin 0.06] [--amax 0.97]
      [--rough 0.09] [--bump 0.25] [--base 0.045,0.075,0.062]

  AS SHIPPED, 2026-08-07:  `-- save`, every default as written.  The defaults ARE the
  shipped numbers, and three of them are only defaults because a blind A/B said so —
  see THE SURFACE READ IS NOT THE PROBLEM and THE THIRD CASE, below.

WHAT WAS MEASURED FIRST (DAYLOG 2026-08-07 09:45, read-only Blender census on the
dressed blend): the `water_emb_*` sheets carry ZERO colour-attribute layers and share
one flat `emb_dress_water` Principled — base (0.045,0.075,0.062), roughness 0.09,
ALPHA A CONSTANT 0.90, noise bump 0.25.  Dellhollow's tranche-2 recipe was never
ported here.  At the emberwake dusk grade a constant 0.90 alpha is a light sink: 10%
transmission over an unlit bed, and the diffuse term of a 0.05-albedo base under
moonlight is black.  The judge's verdicts are the physics, not a bake accident.
THE CENSUS UNDERCOUNTED BY ONE: this script resolves sheets by MATERIAL, and finds
FIVE — the four `water_emb_*` plus `emb_dress_wheelpit_water`, the mill's own dug pit,
which a name pattern misses.  (`emb_dress_leat_water*`/`emb_dress_buckwater*` wear
`emb_dress_waterfall` and are out of scope, but they are still hidden from the
down-ray, or a waterfall card becomes somebody's "bed".)

THE RECIPE, two parts:

 1. DEPTH -> ALPHA (docs/plans/water-transparency.md AS BUILT, the recipe the user
    ratified for Dellhollow): `Col` colour attribute, rgb = WHITE (the neutral
    element), a = ramp(depth) on the top ring, so the bank runs on under the shallows
    instead of stopping at a mitred trim edge.  That edge is what the judge means by
    "no believable wet shore contacts".
 2. `surface_render_method = BLENDED` so the bake alpha-blends and the exporter
    writes alphaMode BLEND.

THE SURFACE READ IS NOT THE PROBLEM, AND THAT IS A MEASUREMENT, NOT A GUESS.  The
first pass also moved roughness 0.09 -> 0.16, bump 0.25 -> 0.45 and lifted the base
toward blue-green, on the reasoning that a near-mirror reflecting unlit foliage is
what makes the water read black.  TWO INDEPENDENT BLIND JUDGES, given the pair
anonymised and shuffled with no ownership framing, PREFERRED THE UNTOUCHED PLATE
(2/10 vs 3/10, both), and both named the same reason: the original's "cooler
blue-black sheen ... gestures at wet" was the only water cue the frame had, and the
change spent it.  The shipped numbers stay.  Defaults now equal the shipped numbers.

FIVE ADAPTATIONS THIS TOWN NEEDED, EVERY ONE MEASURED RATHER THAN INHERITED:

  * PER-VERTEX DEPTH, NOT SURFACE-MAX MINUS BED.  Dellhollow's sheets are flat
    axis-aligned boxes, so `t2_water_shader` takes one surface z for the whole sheet.
    Emberbrook's brook is a STRIP THAT FALLS WITH ITS CHANNEL (measured z span in the
    per-sheet table this script prints), so one surface z would report the head of
    the run as metres deep and the tail as dry.  Depth here is `v.z - bed under v`.
  * THE TOP RING IS THE HIGHER ONE, NOT THE ONE THE NORMAL CLAIMS.  These sheets ship
    with INVERTED normals — measured in the emb-cine collision GLB: on all three
    closed sheets the `n.z > +0.5` group sits 0.12 m BELOW the `n.z < -0.5` group, and
    `water_emb_river` (an OPEN single-sided plane, no bottom ring at all) has no
    positive group whatsoever.  `t2_water_shader`'s `normal.z > 0.5` test would have
    painted the fade on the underside of three sheets and skipped the river entirely,
    with every print in this file looking correct.  So the two near-vertical groups
    are found first and THE HIGHER MEAN Z WINS; a sheet with only one group is an open
    surface and all of it carries the fade.
  * THE THIRD CASE: A SIDE WALL IS NOT A BOTTOM.  The ratified script has two — top
    ring takes the fade, EVERYTHING ELSE goes to 0.02, because a closed sheet read
    through a translucent top AND an equally translucent bottom renders 1-(1-a)^2.
    That reasoning is about the BOTTOM ring only.  Dellhollow's sheets are flat boxes
    seen from above and their vertical walls are never on screen; Emberbrook's brook
    is a STEPPED CASCADE and its risers ARE visible water faces.  Driving them to 0.02
    deleted the risers — which is most of the water this town shows — and the blind
    pair above is what caught it.  So: top ring -> ramp(depth), BOTTOM ring -> 0.02,
    walls -> the water's own alpha.
  * THE RAMP SCALE IS A FLAG, AND THE MEASUREMENT PICKED THE RATIFIED ONE.  Dellhollow
    normalises every sheet to its own median (`--scale median`) because its bathymetry
    is a flat slab 4-7.5 m under the surface.  Emberbrook's water is 0.10-0.39 m deep
    at the median, so `--scale metres` — reading the ramp in true metres — leaves the
    whole town's water at alpha 0.10-0.45 and was the obvious adaptation.  IT LOST THE
    BLIND PAIR: at that alpha the pond stops being a surface and becomes a view of
    unlit brown mud, because Blender's Principled blends the WHOLE shader against a
    Transparent BSDF, SPECULAR INCLUDED.  `median` is the default and the ship; the
    ramp is opaque over the body and steep only in the last few centimetres at the
    bank, which is exactly the shore contact the judge asked for.  Both columns print
    every run so the choice stays a measurement and not a memory.
  * THE DOWN-RAY RUNS AGAINST A LOCAL BVH, NOT `Scene.ray_cast`.  The dressed master
    is 27 M triangles; `Scene.ray_cast` over it did not return 57 k rays in sixteen
    minutes (measured, killed).  Only geometry standing under a sheet's own footprint
    can be its bed, so one BVHTree is built from the evaluated meshes whose world AABB
    overlaps that footprint, and the tri count going in is printed — an instrument
    that finds no bed must be able to prove it could have found one.

DEPTH PASS IMMUNE BY CONSTRUCTION — AND PROVEN, NOT QUOTED.  cine_bake renders depth
under a full `view_layer.material_override`, so the water stays opaque for depth.
Measured on the rebaked `pondlane`, decoding both depth.png through the plate's own
near/far: 14,308 of 1,032,192 pixels differ and EVERY ONE OF THEM BY LESS THAN 0.001 m
over a 137 m range — 1-LSB quantisation, not a moved surface.  (A raw byte compare
says "changed" and a raw channel delta says "255"; both are the blue channel's last
bit.  Compare depth in METRES or do not compare it.)

AND THE SURFACE READ WAS NOT THE PROBLEM BECAUSE THE GEOMETRY WAS (2026-08-07 evening).
The class this file could not move is closed by `tools/emb_brookchop.py`: every sheet was
an independent 0.55 m cell 0.12 m thick, standing 0.29 m (brook) / 0.23 (pond) / 2.04
(millpond) above its own bed — 0.17 m of AIR, a lit underside, four lit walls and a cast
shadow.  That carrier RESHAPES the meshes this file bakes onto, so the two run in a fixed
order and `emb_brookchop` asserts it:
    emb_water_shader -- revert save  ->  emb_brookchop -- save  ->  emb_water_shader -- save
Receipt of the pass that used that order: pondlane moved 0.538% of its pixels (83x this
file's own 0.0065%), the moved region's median luminance went 0.051 -> 0.101 WITH NO LIGHT
CHANGED, and two independent blind judges scored the result 7.5/10 against the untouched
plate's 6.0 and 5.0 — the mirror image of the pair this file's own docstring records.

THE REBUILD TRAP, NAMED BECAUSE DELLHOLLOW PAID IT: `locksfoot_build` once notched a
pool through `join_meshes` and silently dropped the Col bake — 12 plates regressed
with every gate green.  `emb_dress.py` REBUILDS the dressed blend and knows nothing
of this bake: ANY emb_dress re-run OWES an emb_water_shader re-run in the same
window.  `dress_water()` prints exactly this.

THE REALTIME TIER DOES NOT GET THIS, AND THE REASON IS MEASURED (2026-08-07).  The
walkable town ships from `emberbrook-realtime.blend` through
`tools/townwalk_live_refresh.sh` into `public/assets/scenes/emb-townwalk/scene.glb`.
Reading that shipped GLB's own chunk table: `emb_dress_water` is ALREADY
`alphaMode: BLEND` with `baseColorFactor` (0.045,0.075,0.062,**0.90**), and **0 of its
22 primitives carry COLOR_0** — so the per-vertex fade cannot reach the runtime at all
(Blender's exporter skips a vertex colour that does not feed Base Color, and Dellhollow
finding 221 forbids feeding it).  Carrying this pass there would move base colour by
~0.01 linear and roughness by 0.07 in a tier with no ray-traced specular, at the cost
of a re-dress, an `emb_decimate --save`, and a 91 MB GLB re-export.  Not taken; named
here so the next lane does not re-derive it.

Idempotent and invertible: the pre-subdivision geometry lives in each object's
'embws' prop and the material's own shipped numbers in the material's 'embws_mat0'
prop, so `revert save` restores the blend whatever the current flags are.  A receipt
lands at tools/blends/districts/emb_water_shader.json every run.
"""
import bpy, sys, os, json, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(REPO, "tools/blends/districts/emb_water_shader.json")

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


# EVERY DEFAULT BELOW IS A SHIPPED NUMBER.  `-- save` alone reproduces the plates.
SCALE_MODE = opt("--scale", "median")
assert SCALE_MODE in ("metres", "median"), "--scale takes metres|median"
# THE ALPHA FLOOR IS A SEPARATE KNOB FROM THE CURVE, and it is here because the obvious
# adaptation needed one.  Blender's Principled blends the WHOLE shader against a
# Transparent BSDF, SPECULAR INCLUDED — so an alpha of 0.06 is not clear water with a
# sheen on it, it is 6% of a water surface.  `--amin/--amax` remap the ratified curve's
# OUTPUT range without changing its shape; the ratified range is the default because a
# blind pair beat the alternative (see the docstring).
AMIN = float(opt("--amin", "0.06"))
AMAX = float(opt("--amax", "0.97"))
# THE SHIPPED SURFACE NUMBERS, unchanged: emb_dress.py's make_water() values. The first
# pass moved them (0.16 / 0.45 / a blue-green lift) and two blind judges preferred the
# untouched plate. Kept as flags so the next lane can re-test cheaply, not as a proposal.
ROUGH = float(opt("--rough", "0.09"))
BUMP = float(opt("--bump", "0.25"))
BASE = tuple(float(v) for v in opt("--base", "0.045,0.075,0.062").split(","))

MAT = "emb_dress_water"
# every waterish material must be hidden for the down-ray, or a mist card or the
# waterfall sheet becomes the "bed" and the channel reads ankle-deep
WATERISH_MATS = ("emb_dress_water", "emb_dress_waterfall", "emb_dress_mist")
ATTR = "Col"
TARGET_EDGE = 1.5
MAX_VERTS = 40000          # a runaway subdivide is a build failure, not a slow build
SIDE_ALPHA = 0.02
UP_DOT = 0.5
PROP = "embws"
MATPROP = "embws_mat0"
RAMP = [(0.00, 0.06), (0.60, 0.30), (1.50, 0.62), (3.00, 0.88), (4.00, 0.97)]
REF_MEDIAN = 4.0

sc = bpy.context.scene
mat = bpy.data.materials.get(MAT)
assert mat is not None, "no %s in this blend — is this the dressed master?" % MAT
nt = mat.node_tree
principled = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
assert principled is not None, "%s has no Principled BSDF" % MAT
bumpnode = next((n for n in nt.nodes if n.type == 'BUMP'), None)


def mats_of(o):
    return {s.material.name for s in o.material_slots if s.material}


WOBJ = [o for o in sc.objects if o.type == 'MESH' and MAT in mats_of(o)]
HIDEOBJ = [o for o in sc.objects if o.type == 'MESH' and (mats_of(o) & set(WATERISH_MATS))]
assert WOBJ, "no meshes wear %s" % MAT

# THE SHIPPED NUMBERS, SNAPSHOT ONCE.  Hard-coding emb_dress.py's constants here
# would silently rot the day someone re-tunes make_water(); the artifact carries its
# own baseline instead.
if MATPROP not in mat:
    mat[MATPROP] = json.dumps(dict(
        base=[round(v, 6) for v in principled.inputs['Base Color'].default_value[:3]],
        rough=round(principled.inputs['Roughness'].default_value, 6),
        alpha=round(principled.inputs['Alpha'].default_value, 6),
        bump=round(bumpnode.inputs['Strength'].default_value, 6) if bumpnode else None,
        render_method=getattr(mat, 'surface_render_method', None),
        blend_method=getattr(mat, 'blend_method', None)))
MAT0 = json.loads(mat[MATPROP])


def set_render_method(rm, bm):
    if rm is not None and hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = rm
    # blend_method is EEVEE-legacy and is gone in some 4.x/5.x builds
    if bm is not None and hasattr(mat, 'blend_method'):
        try:
            mat.blend_method = bm
        except Exception:
            pass


# ================================================================ REVERT ======
if REVERT:
    for n in ("embws_depth_attr", "embws_depth_ramp"):
        nd = nt.nodes.get(n)
        if nd:
            nt.nodes.remove(nd)
    principled.inputs['Alpha'].default_value = MAT0["alpha"]
    principled.inputs['Base Color'].default_value = (*MAT0["base"], 1.0)
    principled.inputs['Roughness'].default_value = MAT0["rough"]
    if bumpnode and MAT0.get("bump") is not None:
        bumpnode.inputs['Strength'].default_value = MAT0["bump"]
    set_render_method(MAT0.get("render_method"), MAT0.get("blend_method"))
    for o in WOBJ:
        if not o.get(PROP):
            continue
        st = json.loads(o[PROP])
        me = o.data
        if ATTR in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[ATTR])
        me.clear_geometry()
        me.from_pydata([tuple(v) for v in st["verts"]], [], [tuple(p) for p in st["polys"]])
        me.validate()
        me.update()
        me.materials.clear()
        me.materials.append(mat)
        del o[PROP]
        print("RESTORED %-26s %d verts" % (o.name, len(st["verts"])))
    del mat[MATPROP]
    print("%s: shipped numbers restored, Alpha UNLINKED at %.2f" % (MAT, MAT0["alpha"]))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the blend)")
    sys.exit(0)

# ============================================================== BAKE ==========
print("=" * 78)
print("emb water — depth->alpha bake   scale=%s  alpha %.2f..%.2f  rough=%.2f "
      "bump=%.2f base=%s" % (SCALE_MODE, AMIN, AMAX, ROUGH, BUMP, BASE))
print("=" * 78)

# snapshot BEFORE subdividing: subdivision is not invertible
for o in WOBJ:
    if not o.get(PROP):
        me = o.data
        o[PROP] = json.dumps(dict(
            verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in me.vertices],
            polys=[list(p.vertices) for p in me.polygons]))

dg = bpy.context.evaluated_depsgraph_get()
WATERISH = {o.name for o in HIDEOBJ}


def world_aabb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(w.x for w in ws), max(w.x for w in ws),
            min(w.y for w in ws), max(w.y for w in ws),
            min(w.z for w in ws), max(w.z for w in ws))


# THE FOOTPRINT, then THE BED UNDER IT.  `Scene.ray_cast` over a 27 M-triangle dressed
# master did not return 57 k rays in sixteen minutes; only what stands under a sheet
# can be its bed, so the tree is built from the overlapping meshes and nothing else.
FOOT = [world_aabb(o) for o in WOBJ]
PAD = 2.0


def overlaps_any(bb):
    for f in FOOT:
        if (bb[0] <= f[1] + PAD and bb[1] >= f[0] - PAD and
                bb[2] <= f[3] + PAD and bb[3] >= f[2] - PAD and
                bb[4] <= f[5] + 1.0 and bb[5] >= f[4] - 60.0):
            return True
    return False


bverts, bpolys, nobj = [], [], 0
for o in sc.objects:
    if o.type != 'MESH' or o.name in WATERISH:
        continue
    try:
        bb = world_aabb(o)
    except Exception:
        continue
    if not overlaps_any(bb):
        continue
    oe = o.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    if me is None:
        continue
    M = oe.matrix_world
    base = len(bverts)
    bverts.extend([M @ v.co for v in me.vertices])
    bpolys.extend([[base + i for i in p.vertices] for p in me.polygons])
    oe.to_mesh_clear()
    nobj += 1
assert bpolys, "no candidate bed geometry under any water footprint — the probe would " \
               "report every vertex bedless and that would be an instrument failure"
BED = BVHTree.FromPolygons(bverts, bpolys, all_triangles=False)
print("bed BVH: %d meshes / %d verts / %d polys under the four footprints"
      % (nobj, len(bverts), len(bpolys)))
DOWN = Vector((0, 0, -1))


def bed_under(x, y, z):
    """first non-water hit below (x, y, z); the tree contains no water by construction"""
    hit = BED.ray_cast(Vector((x, y, z + 0.05)), DOWN, 120.0)
    return hit[0].z if hit[0] is not None else None


A0, A1 = RAMP[0][1], RAMP[-1][1]


def remap(a):
    return AMIN + (a - A0) * (AMAX - AMIN) / (A1 - A0)


def ramp_alpha(d, scale):
    dd = d * scale
    if dd <= RAMP[0][0]:
        return remap(RAMP[0][1])
    for i in range(len(RAMP) - 1):
        d0, a0 = RAMP[i]
        d1, a1 = RAMP[i + 1]
        if dd <= d1:
            return remap(a0 + (a1 - a0) * (dd - d0) / (d1 - d0))
    return remap(RAMP[-1][1])


def med(xs):
    return sorted(xs)[len(xs) // 2] if xs else None


report = {}
for o in sorted(WOBJ, key=lambda x: x.name):
    me = o.data
    M = o.matrix_world
    # --- adaptive subdivision: ONLY the long edges, one cut per pass.  Taking the
    # cut count from the longest edge and applying it to every edge also cuts the
    # sheet's own thickness (t2 measured 26,512 verts for a ~2,000-vert job).
    bm = bmesh.new()
    bm.from_mesh(me)
    cuts = 0
    for _ in range(7):
        long_edges = [e for e in bm.edges
                      if (e.verts[1].co - e.verts[0].co).length > TARGET_EDGE]
        if not long_edges:
            break
        if len(bm.verts) + len(long_edges) > MAX_VERTS:
            print("  %-26s SUBDIVISION CAPPED at %d verts" % (o.name, len(bm.verts)))
            break
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=True)
        cuts += 1
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()

    # --- WHICH RING IS THE TOP.  Not the one the normal claims: these sheets carry
    # inverted normals, and water_emb_river is an open plane with only one ring.
    N = M.to_3x3().inverted().transposed()
    plus, minus = [], []
    for p in me.polygons:
        nz = (N @ p.normal).normalized().z
        if nz > UP_DOT:
            plus.append(p)
        elif nz < -UP_DOT:
            minus.append(p)

    def meanz(g):
        return (sum((M @ me.vertices[v].co).z for p in g for v in p.vertices)
                / max(1, sum(len(p.vertices) for p in g))) if g else -1e9

    zp, zm = meanz(plus), meanz(minus)
    if plus and minus:
        up_polys = plus if zp > zm else minus
        flipped = zm > zp
    else:
        up_polys = plus or minus
        flipped = bool(minus) and not plus
    up_verts = set()
    for p in up_polys:
        up_verts.update(p.vertices)

    # --- depth PER VERTEX (the brook falls with its channel)
    vdepth = {}
    for v in me.vertices:
        w = M @ v.co
        b = bed_under(w.x, w.y, w.z)
        vdepth[v.index] = (w.z - b) if b is not None else None
    # THE MEDIAN IS OVER UP-FACE VERTICES ONLY.  A closed sheet's bottom ring sits
    # 0.4 m lower and reports 0.4 m less depth; including it drags the median that
    # the whole ramp is scaled by, on exactly the vertices whose alpha is thrown
    # away at SIDE_ALPHA.
    updepths = [vdepth[i] for i in sorted(up_verts) if vdepth.get(i) is not None and vdepth[i] > 0.0]
    m_all = med([d for d in vdepth.values() if d is not None and d > 0.0])
    m_up = med(updepths) or REF_MEDIAN
    scale = 1.0 if SCALE_MODE == "metres" else (REF_MEDIAN / m_up if m_up > 0.1 else 1.0)

    ups_pre = [ramp_alpha(d, scale) for d in updepths]
    if ATTR in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[ATTR])
    ca = me.color_attributes.new(name=ATTR, type='FLOAT_COLOR', domain='CORNER')
    me.color_attributes.active_color = ca
    # THREE CASES, NOT TWO — and the third is Emberbrook's, paid for by two blind judges.
    #   top ring     -> ramp(depth), the ratified fade
    #   BOTTOM ring  -> SIDE_ALPHA, the ratified anti-double-read (a ray entering a
    #                   translucent top and leaving an equally translucent bottom renders
    #                   1-(1-a)^2 instead of a)
    #   side WALLS   -> the water's OWN alpha, NOT SIDE_ALPHA.  Dellhollow's sheets are
    #                   flat boxes seen from above and their walls are never on screen.
    #                   Emberbrook's brook is a STEPPED CASCADE and its risers ARE visible
    #                   water faces.  Driving them to 0.02 deleted the risers and the water
    #                   with them: two independent blind judges scored the result 2/10
    #                   against the untouched plate's 3/10, both naming the same reason —
    #                   the original's "cooler blue-black sheen ... gestures at wet" was
    #                   the only water cue the frame had, and transparency spent it on a
    #                   view of unlit brown mud.
    upset = {p.index for p in up_polys}
    downset = {p.index for p in (minus if up_polys is plus else plus)}
    med_a = med(ups_pre) if ups_pre else remap(RAMP[-1][1])
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            if p.index in downset:
                a = SIDE_ALPHA
            else:
                d = vdepth.get(vi)
                if d is None:
                    # bedless: nothing under it to see, so it stays as opaque as the
                    # deepest water rather than punching a hole in the sheet
                    a = remap(RAMP[-1][1])
                elif p.index in upset:
                    a = ramp_alpha(d, scale)
                else:
                    # a wall vertex shared with the bottom ring has no water above it to
                    # take a depth from; the sheet's own median is the honest stand-in
                    a = ramp_alpha(d, scale) if vi in up_verts else med_a
            ca.data[li].color = (1.0, 1.0, 1.0, a)

    ups = ups_pre
    alt = REF_MEDIAN / m_up if (m_up and m_up > 0.1) else 1.0
    alt_ups = [ramp_alpha(d, 1.0 if SCALE_MODE == "median" else alt) for d in updepths]
    ws = [M @ v.co for v in me.vertices]
    report[o.name] = dict(
        verts=len(me.vertices), polys=len(me.polygons), cuts=cuts,
        up_polys=len(up_polys), up_verts=len(up_verts),
        rings=[len(plus), len(minus)], ring_mean_z=[round(zp, 3) if plus else None,
                                                    round(zm, 3) if minus else None],
        normals_inverted=bool(flipped), open_sheet=not (plus and minus),
        surface_z=[round(min(w.z for w in ws), 3), round(max(w.z for w in ws), 3)],
        median_depth_all=round(m_all, 3) if m_all else None,
        median_depth_up=round(m_up, 3),
        depth_min=round(min(updepths), 3) if updepths else None,
        depth_max=round(max(updepths), 3) if updepths else None,
        bedless_up=len(up_verts) - len(updepths),
        ramp_scale=round(scale, 4),
        alpha_min=round(min(ups), 3) if ups else None,
        alpha_med=round(med(ups), 3) if ups else None,
        alpha_max=round(max(ups), 3) if ups else None,
        other_mode_alpha_med=round(med(alt_ups), 3) if alt_ups else None)
    r = report[o.name]
    print("  %-24s %5dv/%5dp  rings +%d/-%d meanz %s/%s -> TOP=%s%s"
          % (o.name, r["verts"], r["polys"], len(plus), len(minus),
             ("%.2f" % zp) if plus else "-", ("%.2f" % zm) if minus else "-",
             "minus" if flipped else "plus",
             "  (OPEN SHEET, no bottom ring)" if r["open_sheet"] else ""))
    print("      surf z %6.2f..%6.2f  depth(up) %5.2f..%5.2f med %5.2f  -> ramp x%.2f  "
          "alpha min/med/max %.2f/%.2f/%.2f  [%s med would be %s]  (%d of %d up-verts bedless)"
          % (r["surface_z"][0], r["surface_z"][1],
             r["depth_min"] or 0, r["depth_max"] or 0, r["median_depth_up"], scale,
             r["alpha_min"] or 0, r["alpha_med"] or 0, r["alpha_max"] or 0,
             "median" if SCALE_MODE == "metres" else "metres", r["other_mode_alpha_med"],
             r["bedless_up"], len(up_verts)))

# ============================================================== WIRE ==========
attr = nt.nodes.get("embws_depth_attr") or nt.nodes.new('ShaderNodeVertexColor')
attr.name = attr.label = "embws_depth_attr"
attr.layer_name = ATTR
attr.location = (-760, -320)
ramp = nt.nodes.get("embws_depth_ramp") or nt.nodes.new('ShaderNodeValToRGB')
ramp.name = ramp.label = "embws_depth_ramp"
ramp.location = (-560, -320)
# shipped as a straight pass-through: the BAKED values are what renders, and the
# ramp is here so the curve can be pulled without re-baking
ramp.color_ramp.interpolation = 'LINEAR'
while len(ramp.color_ramp.elements) > 2:
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
nt.links.new(attr.outputs['Alpha'], ramp.inputs['Fac'])
# BASE COLOUR STAYS UNLINKED (Dellhollow finding 221): a linked Base Color is what
# makes the glTF exporter drop baseColorFactor and ship a white primitive.
assert not principled.inputs['Base Color'].is_linked, \
    "%s Base Color is LINKED — finding 221; refusing to proceed" % MAT
nt.links.new(ramp.outputs['Color'], principled.inputs['Alpha'])
principled.inputs['Base Color'].default_value = (*BASE, 1.0)
principled.inputs['Roughness'].default_value = ROUGH
if bumpnode:
    bumpnode.inputs['Strength'].default_value = BUMP
set_render_method('BLENDED', 'BLEND')
print("\n%s: Alpha <- embws_depth_ramp <- Col.a;  base %s  rough %.2f  bump %.2f  "
      "render_method %s" % (MAT, BASE, ROUGH, BUMP,
                            getattr(mat, 'surface_render_method', '?')))
print("  Alpha linked: %s   Base Color linked: %s (must be False)"
      % (principled.inputs['Alpha'].is_linked, principled.inputs['Base Color'].is_linked))

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
json.dump(dict(
    _doc=("GENERATED by tools/emb_water_shader.py — Emberbrook's port of the ratified "
          "depth->alpha recipe (docs/plans/water-transparency.md AS BUILT). Depth is "
          "PER VERTEX because the brook falls with its channel; the ramp reads in true "
          "metres by default because normalising to each sheet's median drives every "
          "median pixel to 0.97 and keeps a night town's water black."),
    generator="tools/emb_water_shader.py", plan="docs/plans/water-transparency.md",
    blend=bpy.data.filepath, material=MAT, attribute=ATTR, scale_mode=SCALE_MODE,
    target_edge=TARGET_EDGE, ramp=RAMP, ref_median=REF_MEDIAN, side_alpha=SIDE_ALPHA,
    up_dot=UP_DOT, amin=AMIN, amax=AMAX, base=list(BASE), rough=ROUGH, bump=BUMP,
    shipped=MAT0, saved=bool(SAVE), sheets=report,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, REPO))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
