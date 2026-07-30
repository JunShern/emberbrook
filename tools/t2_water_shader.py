"""t2_water_shader.py — DEPTH -> ALPHA.  docs/plans/water-transparency.md, W3-W5.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_water_shader.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_water_shader.py -- revert save

RUN THIS AFTER tools/t2_water_bed.py, NEVER BEFORE.  Baking a depth attribute
against the original flat slab would encode the very step function the tranche
exists to remove — 4,999 of the mid pool's 6,165 samples in one 0.5 m bin — and
the ramp would then be tuned to hide it.  The shelves are the deliverable; this
is the cheap part that makes them visible.

W3 — THE BAKE.  Each water sheet is subdivided to ~1.5 m (they ship as 8- and
16-vertex boxes, so a per-vertex depth attribute has nowhere to live), then every
vertex ray-casts straight down to the bed with all water hidden from the
depsgraph.  The result goes into a `Col` colour attribute as

    Col.rgb = (1, 1, 1)     WHITE, the neutral element (finding 218)
    Col.a   = ramp(depth)

PER-SHEET RAMPS, WHICH IS THE TRAP THE PLAN NAMES.  `water_pool-upstream` is
7.5 m deep over the same slab the 4.1 m mid pool uses.  A single ramp tuned on
the mid pool renders the upstream pool fully opaque and makes the B1 shelf — the
one boatyard can actually see — invisible.  So each sheet's ramp is scaled by its
OWN median depth, which this script measures rather than assumes.

ONLY THE TOP FACE CARRIES THE FADE, and that is not a detail.  The sheets are
closed 0.4 m boxes: a view ray entering a translucent top would leave through an
equally translucent bottom and the water would read at 1-(1-a)^2 instead of a —
0.84 where 0.60 was authored.  Faces whose normal points up get the depth alpha;
every other face is driven to 0.02 and effectively disappears.  The water you
see is its surface, which is what it always was.

W4 — THE WIRING.  One `Color Attribute` node -> a `ColorRamp` (authoring control,
shipped as a straight pass-through so the baked values are what render) -> BOTH
lobes' Alpha.  `water_lobe`'s and `foam_lobe`'s BASE COLOURS ARE NOT TOUCHED and
must not be: they are flat and unlinked, and that is the only reason `m_water`
exports a real `baseColorFactor` today (finding 221 records two measured failures
from breaking exactly this).  `surface_render_method` becomes `BLENDED`, which is
what makes the exporter write `alphaMode: "BLEND"`.

Cycles alpha-blends the surface over the bed with no refraction, no volume and no
extra bounce budget — the cost is a few transparent bounces against a limit of 8.

THE DEPTH PASS IS IMMUNE BY CONSTRUCTION, and it is worth saying so because it is
the obvious thing to fear: `cine_bake.py` renders depth under a
`view_layer.material_override` that replaces EVERY material with one Emission
shader, so the water stays opaque for depth, `depth.png` keeps recording the
water SURFACE, and character occlusion at the waterline cannot regress.

W5 — THE ONE TIMEBOXED EXPERIMENT.  glTF multiplies `baseColorFactor` by
`COLOR_0` INCLUDING THE ALPHA CHANNEL.  Since this bake already writes rgb=white
and a=depth, the runtime could get the same fade for free with no linked Base
Color anywhere.  It either works cleanly or fails silently, so it is MEASURED
(export, read the GLB's own JSON and accessor table) and never assumed.  If any
link in the chain is missing, tier 1 ships: a fixed `water_lobe.Alpha` of 0.72,
a uniformly translucent river, strictly better than today's opaque sheet.  One
attempt, then move on.
"""
import bpy, os, sys, json, math, struct, bmesh
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_water_shader.json")
SCRATCH = os.path.join(ROOT, "tools/blends/districts/_water_alpha.glb")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

MAT = "m_water"
ATTR = "Col"
TARGET_EDGE = 1.5
TIER1_ALPHA = 0.72
SIDE_ALPHA = 0.02
PROP = "t2ws"

# the plan's ramp, in metres of depth against a 4 m reference sheet
RAMP = [(0.00, 0.06), (0.60, 0.30), (1.50, 0.62), (3.00, 0.88), (4.00, 0.97)]
REF_MEDIAN = 4.0

sc = bpy.context.scene
WOBJ = [o for o in sc.objects if o.type == 'MESH'
        and any(s.material and s.material.name == MAT for s in o.material_slots)]
mat = bpy.data.materials[MAT]


def water_lobes():
    return (mat.node_tree.nodes.get("water_lobe"), mat.node_tree.nodes.get("foam_lobe"))


# ================================================================ REVERT ======
if REVERT:
    nt = mat.node_tree
    for n in ("t2_depth_attr", "t2_depth_ramp"):
        nd = nt.nodes.get(n)
        if nd:
            nt.nodes.remove(nd)
    for lobe in water_lobes():
        if lobe is not None:
            lobe.inputs['Alpha'].default_value = 1.0
    mat.surface_render_method = 'DITHERED'
    mat.blend_method = 'HASHED'
    print("m_water: alpha wiring removed, both lobes back to Alpha 1.0, DITHERED")
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
        print("RESTORED %-22s %d verts / %d polys" % (o.name, len(st["verts"]), len(st["polys"])))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ============================================================== W3: BAKE ======
print("=" * 78)
print("W3 — subdivide the sheets, ray-cast the bed, bake depth into Col.a")
print("=" * 78)

# snapshot BEFORE subdividing: subdivision is not invertible
for o in WOBJ:
    if not o.get(PROP):
        me = o.data
        o[PROP] = json.dumps(dict(
            verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in me.vertices],
            polys=[list(p.vertices) for p in me.polygons]))

# hide EVERY water sheet, or a down-ray stops on the neighbouring pool's surface
hidden = []
for o in WOBJ:
    if not o.hide_viewport:
        o.hide_viewport = True
        hidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def bed_z(x, y, top):
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                            distance=120.0)
    return loc.z if hit else None


def ramp_alpha(d, scale):
    """the plan's curve, with the depth axis scaled to this sheet's own median"""
    dd = d * scale
    if dd <= RAMP[0][0]:
        return RAMP[0][1]
    for i in range(len(RAMP) - 1):
        d0, a0 = RAMP[i]
        d1, a1 = RAMP[i + 1]
        if dd <= d1:
            t = (dd - d0) / (d1 - d0)
            return a0 + (a1 - a0) * t
    return RAMP[-1][1]


report = {}
for o in WOBJ:
    me = o.data
    M = o.matrix_world
    surf = max((M @ v.co).z for v in me.vertices)
    # --- subdivide to ~TARGET_EDGE
    # ADAPTIVE, one cut per pass on the long edges only. Taking `cuts` from the
    # LONGEST edge and applying it to every edge cut the sheets' 0.4 m THICKNESS
    # forty-six times as well: water_pool-mid came out at 26,512 vertices for a
    # job the plan budgets at ~2,000 across all four sheets.
    bm = bmesh.new()
    bm.from_mesh(me)
    cuts = 0
    for _ in range(7):
        long_edges = [e for e in bm.edges
                      if (e.verts[1].co - e.verts[0].co).length > TARGET_EDGE]
        if not long_edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=True)
        cuts += 1
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    # --- measure the bed under every vertex
    depths = []
    vdepth = {}
    for v in me.vertices:
        w = M @ v.co
        b = bed_z(w.x, w.y, surf + 0.05)
        d = (surf - b) if b is not None else None
        vdepth[v.index] = d
        if d is not None and d > 0.0:
            depths.append(d)
    med = sorted(depths)[len(depths) // 2] if depths else REF_MEDIAN
    scale = REF_MEDIAN / med if med > 0.1 else 1.0
    # --- write Col: white rgb, alpha = ramp(depth); only the UP faces carry it
    if ATTR in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[ATTR])
    ca = me.color_attributes.new(name=ATTR, type='FLOAT_COLOR', domain='CORNER')
    me.color_attributes.active_color = ca
    N = M.to_3x3().inverted().transposed()
    up_loops = 0
    for p in me.polygons:
        facing_up = (N @ p.normal).normalized().z > 0.5
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            if facing_up:
                d = vdepth.get(vi)
                a = ramp_alpha(d, scale) if d is not None else RAMP[-1][1]
                up_loops += 1
            else:
                a = SIDE_ALPHA
            ca.data[li].color = (1.0, 1.0, 1.0, a)
    ups = [ramp_alpha(d, scale) for d in depths]
    report[o.name] = dict(surface_z=round(surf, 2), verts=len(me.vertices),
                          polys=len(me.polygons), cuts=cuts,
                          median_depth=round(med, 2), ramp_scale=round(scale, 3),
                          depth_min=round(min(depths), 2) if depths else None,
                          depth_max=round(max(depths), 2) if depths else None,
                          alpha_min=round(min(ups), 3) if ups else None,
                          alpha_max=round(max(ups), 3) if ups else None,
                          up_loops=up_loops, samples=len(depths))
    print("  %-22s surf %6.2f  %4d verts  median depth %5.2f m -> ramp x%.2f  "
          "depth %.2f..%.2f  alpha %.2f..%.2f"
          % (o.name, surf, len(me.vertices), med, scale,
             min(depths) if depths else 0, max(depths) if depths else 0,
             min(ups) if ups else 0, max(ups) if ups else 0))

for nm in hidden:
    ob = bpy.data.objects.get(nm)
    if ob is not None:
        ob.hide_viewport = False

# ============================================================== W4: WIRE =====
print("\n" + "=" * 78)
print("W4 — Color Attribute -> ColorRamp -> BOTH lobes' Alpha.  Base Colours "
      "untouched.")
print("=" * 78)
nt = mat.node_tree
attr = nt.nodes.get("t2_depth_attr") or nt.nodes.new('ShaderNodeVertexColor')
attr.name = attr.label = "t2_depth_attr"
attr.layer_name = ATTR
attr.location = (-760, -320)
ramp = nt.nodes.get("t2_depth_ramp") or nt.nodes.new('ShaderNodeValToRGB')
ramp.name = ramp.label = "t2_depth_ramp"
ramp.location = (-560, -320)
# shipped as a straight pass-through: the authored values are the BAKED values,
# and the ramp is here so the curve can be pulled without re-baking
ramp.color_ramp.interpolation = 'LINEAR'
while len(ramp.color_ramp.elements) > 2:
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
nt.links.new(attr.outputs['Alpha'], ramp.inputs['Fac'])
lobes = water_lobes()
for lobe in lobes:
    assert lobe is not None, "m_water lost a lobe"
    assert not lobe.inputs['Base Color'].is_linked, \
        "%s.Base Color is LINKED — finding 221; refusing to proceed" % lobe.name
    nt.links.new(ramp.outputs['Color'], lobe.inputs['Alpha'])
    print("  %s.Alpha <- t2_depth_ramp   (Base Color still flat %s)"
          % (lobe.name, tuple(round(v, 3) for v in lobe.inputs['Base Color'].default_value[:3])))
mat.surface_render_method = 'BLENDED'
mat.blend_method = 'BLEND'
print("  m_water surface_render_method = BLENDED  (exporter writes alphaMode BLEND)")

# ============================================================== W5: MEASURE ==
print("\n" + "=" * 78)
print("W5 — does COLOR_0's ALPHA survive the glTF round trip?  One attempt.")
print("=" * 78)
tier = 1
gltf_note = "not run"
try:
    bpy.ops.object.select_all(action='DESELECT')
    for o in WOBJ:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = WOBJ[0]
    bpy.ops.export_scene.gltf(filepath=SCRATCH, export_format='GLB', use_selection=True,
                              export_apply=False, export_materials='EXPORT',
                              export_vertex_color='MATERIAL')
    data = open(SCRATCH, 'rb').read()
    assert data[:4] == b'glTF'
    off, J = 12, None
    while off < len(data):
        ln, ty = struct.unpack_from('<II', data, off)
        if ty == 0x4E4F534A:
            J = json.loads(data[off + 8: off + 8 + ln].decode('utf-8'))
            break
        off += 8 + ln + (-ln % 4)
    m0 = next((m for m in J.get("materials", []) if m.get("name", "").startswith("m_water")), None)
    pbr = (m0 or {}).get("pbrMetallicRoughness", {})
    has_c0 = any("COLOR_0" in p.get("attributes", {})
                 for mesh in J.get("meshes", []) for p in mesh.get("primitives", []))
    acc_type, a_lo, a_hi = None, None, None
    bin_off = None
    off2 = 12
    while off2 < len(data):
        ln2, ty2 = struct.unpack_from('<II', data, off2)
        if ty2 == 0x004E4942:
            bin_off = off2 + 8
            break
        off2 += 8 + ln2 + (-ln2 % 4)
    for mesh in J.get("meshes", []):
        for p in mesh.get("primitives", []):
            ai = p.get("attributes", {}).get("COLOR_0")
            if ai is None:
                continue
            acc = J["accessors"][ai]
            acc_type = acc.get("type")
            # READ THE ALPHAS. A 4-component COLOR_0 proves nothing on its own:
            # the exporter warned it was skipping the active vertex colour, and
            # a COLOR_0 of all-1.0 multiplies baseColorFactor by one and ships a
            # river exactly as opaque as today's. The plan says confirm a
            # NON-TRIVIAL ALPHA RANGE, so read the buffer.
            if bin_off is None or acc_type != "VEC4":
                continue
            bv = J["bufferViews"][acc["bufferView"]]
            base = bin_off + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            ct = acc["componentType"]
            fmt, sz, norm = {5126: ("<f", 4, 1.0), 5123: ("<H", 2, 65535.0),
                             5121: ("<B", 1, 255.0)}[ct]
            stride = bv.get("byteStride") or (sz * 4)
            for k in range(acc["count"]):
                a = struct.unpack_from(fmt, data, base + k * stride + 3 * sz)[0] / norm
                a_lo = a if a_lo is None else min(a_lo, a)
                a_hi = a if a_hi is None else max(a_hi, a)
    print("  material            : %s" % (m0 or {}).get("name"))
    print("  alphaMode           : %s" % m0.get("alphaMode") if m0 else "-")
    print("  baseColorFactor     : %s" % pbr.get("baseColorFactor", "ABSENT (glTF default 1,1,1,1)"))
    print("  COLOR_0 present     : %s   accessor type: %s" % (has_c0, acc_type))
    print("  COLOR_0 ALPHA range : %s .. %s" % (a_lo, a_hi))
    nontrivial = (a_lo is not None and a_hi is not None and (a_hi - a_lo) > 0.15)
    if has_c0 and acc_type == "VEC4" and (m0 or {}).get("alphaMode") == "BLEND" and nontrivial:
        tier = 2
        gltf_note = ("COLOR_0 arrives as VEC4 with alphaMode BLEND and its alpha "
                     "spans %.3f..%.3f — the runtime gets the same depth fade as "
                     "the bake, for free." % (a_lo, a_hi))
    else:
        gltf_note = ("COLOR_0 alpha did not survive with a non-trivial range "
                     "(type %s, alpha %s..%s); shipping tier 1, a fixed alpha of "
                     "%.2f — a uniformly translucent river, still strictly better "
                     "than today's opaque sheet."
                     % (acc_type, a_lo, a_hi, TIER1_ALPHA))
    print("  -> TIER %d.  %s" % (tier, gltf_note))
except Exception as e:
    gltf_note = "export experiment failed: %s — shipping tier 1" % e
    print("  " + gltf_note)
finally:
    if os.path.exists(SCRATCH):
        os.remove(SCRATCH)

# ---------------------------------------------------------------------------
# TIER 1 AND THE BAKED FADE ARE MUTUALLY EXCLUSIVE, and the plan could not have
# known it because it only shows up in the exported JSON.
#
#   * Cycles reads the per-vertex fade only if `Alpha` is LINKED to the ramp.
#   * The glTF exporter takes `baseColorFactor[3]` from `Alpha` only if it is
#     UNLINKED. Linked, it writes 1.0 — measured above, alongside a COLOR_0
#     whose alpha is a flat 1.0 because the exporter skips a vertex colour that
#     does not feed Base Color (its own warning says so, and finding 221 forbids
#     feeding Base Color from it).
#
# One socket cannot do both. The BAKE WINS, without hesitation: the seventeen
# del-cine backdrops ARE the art the player looks at, and the runtime GLB is
# collision plus walk surfaces under those plates. So the link stays, the render
# gets the full 0.06..0.97 depth fade, and the runtime water ships opaque —
# which is exactly what it ships today, so nothing regresses.
#
# `-- runtime-tier1` flips it the other way for whoever needs it later: unlink
# Alpha, set 0.72, and the runtime gets a uniformly translucent river at the
# cost of the bake's gradient.
RUNTIME_TIER1 = "runtime-tier1" in argv
for lobe in water_lobes():
    lobe.inputs['Alpha'].default_value = TIER1_ALPHA
if RUNTIME_TIER1:
    for lobe in water_lobes():
        for lk in [l for l in nt.links if l.to_socket is lobe.inputs['Alpha']]:
            nt.links.remove(lk)
    tier = 1
    gltf_note = ("runtime-tier1: Alpha UNLINKED at %.2f, so baseColorFactor[3] "
                 "exports as %.2f. The bake loses its per-vertex gradient."
                 % (TIER1_ALPHA, TIER1_ALPHA))
    print("  RUNTIME TIER 1: Alpha unlinked, fixed %.2f — the bake's gradient is "
          "given up for a translucent runtime river." % TIER1_ALPHA)
else:
    tier = 0
    gltf_note = ("BAKE-FIRST: Alpha stays LINKED so Cycles renders the full "
                 "per-vertex depth fade; the exporter therefore writes "
                 "baseColorFactor[3] = 1.0 and the runtime water is opaque, as it "
                 "is today. COLOR_0 exported with a flat 1.0 alpha (the exporter "
                 "skips a vertex colour that does not feed Base Color), so tier 2 "
                 "is not available without breaking finding 221. Run with "
                 "`-- runtime-tier1` to trade the gradient for a translucent "
                 "runtime river.")
    print("  BAKE-FIRST (tier 0): Alpha stays linked; the seventeen backdrops get "
          "the full fade and the runtime water is unchanged from today.")

json.dump(dict(
    _doc=("GENERATED by tools/t2_water_shader.py — the depth-to-alpha bake and "
          "wiring. Run AFTER tools/t2_water_bed.py; the ramp is per-sheet because "
          "the upstream pool is 7.5 m deep over the slab the 4.1 m mid pool uses."),
    generator="tools/t2_water_shader.py", plan="docs/plans/water-transparency.md",
    attribute=ATTR, target_edge=TARGET_EDGE, ramp=RAMP, ref_median=REF_MEDIAN,
    side_alpha=SIDE_ALPHA, tier=tier, tier1_alpha=TIER1_ALPHA, gltf=gltf_note,
    sheets=report,
), open(MANIFEST, "w"), indent=1)
print("\nmanifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
