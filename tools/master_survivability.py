"""master_survivability.py — the master-wide cure for glTF-white materials.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_survivability.py -- --save
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_survivability.py -- --dry
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_survivability.py -- --only bunting --save

WHY (canon, MIGRATION.md GLTF-SURVIVAL GATE, 2026-07-29): the user walked the live
townwalk and found 516/1587 primitives rendering WHITE.  Procedural node-tree
materials cannot cross glTF — the exporter writes baseColorFactor, a texture or
COLOR_0, and nothing else — while Blender's own render hides the problem
completely because the nodes simply run there.  A town-wide round trip
(`master_glb_survival.py --prefix "" `) measures **760 white-exporting material
slots across 23 materials**: the whole foliage kit, every rope, ten bunting
cloths and all of Lock Four's dam.

THE PROMISE THIS PASS MAKES: the Blender render look does not change.  That is
not a hope, it is the reason the two mechanisms below were chosen over the
obvious one, and `master_surv_luminance.py` holds it to +-0.5% on five frames.

TWO MECHANISMS, both established by round-trip experiment rather than by reading
the exporter's source:

 [A] RELINK  (`vbake`) — for a material that already HAS a Principled BSDF, even
     one buried behind a Mix Shader.  The exporter DOES traverse Mix Shaders and
     find the Principled (tested: relinking `mat_grass` alone made COLOR_0 arrive
     at mean 0.129 with std 0.055, gradient intact).  So the cure is only to move
     the Base Color link from the procedural chain to a VertexColor node reading
     a baked `Col` attribute.  The Mix Shader, the Translucent BSDF, the noise
     cutout and every Bump chain stay exactly where they are — which is why the
     foliage keeps its soft backlit look and the render does not move.

 [B] EXPORT PROXY (`proxy`) — for a material with NO Principled BSDF at all:
     `MixShader(Diffuse, Translucent)` for the ten bunting cloths,
     `MixShader(Diffuse, Glossy)` for `mat_darkfall`.  A bare Diffuse BSDF is not
     a shader glTF export understands, which is why `mat_flag_red` arrives white
     even though its Diffuse colour is already correct.  Promoting a Principled
     to the output would fix the export and COST THE PENNANTS THEIR TRANSLUCENCY
     in Blender.  Instead the existing mix is nested in an outer Mix Shader at
     factor 0.0 against a Principled that carries the colour: factor 0 renders
     branch A only, so Blender is unchanged, while the exporter finds the
     Principled and writes a real baseColorFactor.  (Tested: `mat_flag_red`
     arrives at 0.235/0.032/0.030, `mat_darkfall` at 0.016/0.042/0.044.)
     The proxy is LABELLED in the node tree, because a colour that exists in two
     places can drift in one of them — see the report's honesty note.

THE BAKE: albedo is captured by temporarily rewiring the material's albedo socket
into an Emission and Cycles-baking EMIT (1 sample, no lighting) to a color
attribute.  EMIT is used rather than DIFFUSE/COLOR because these trees mix
Translucent and Transparent shaders into the surface, and a diffuse-colour pass
folds that mixing INTO the albedo — baking the leaf cutout into the leaf colour.
EMIT of the albedo socket alone is the pure ramp/noise output, which is exactly
what the VertexColor node must then reproduce.

WHAT IS PRESERVED, deliberately:
* Existing `Col` attributes are never overwritten.  Only the loops of faces whose
  material this pass is curing are written; every other loop keeps its value.
  (No object currently carries both a cured material and one of the ten
  `Col`-reading kit materials — verified, 0 of 743 — but the mask is written
  anyway, because that is a fact about today's master, not a rule.)
* `hide_render` / `hide_viewport` are restored EXACTLY.  Baking requires objects
  enabled for rendering, and 5 of the cured objects are render-hidden; the
  manifest-51 ribbon hiding must survive this pass untouched.
* The scene's render engine is restored.  The bake needs Cycles; the render norm
  is EEVEE, and this script SAVES the file.

GEOMETRY IS NOT TOUCHED.  This is a materials-only pass and it asserts that: the
object set and every object's vertex/polygon count are compared before and after,
and a mismatch is a hard failure.

IDEMPOTENT, with one measured caveat.  STRUCTURALLY it is exact: a second run finds
the VertexColor node and the proxy already there and reuses them ("reused" in the
report) rather than stacking a second copy, the relink is a no-op, and the geometry
and COLOR_0-neutrality assertions hold.  Verified by running the whole pass twice
and diffing the reports — identical.

The BAKE, however, is not bit-identity.  On a second run the albedo socket is the
VertexColor node, so it bakes `Col` from `Col`, which ought to be exact and is not:
15.5% of channels move, worst case 8.9e-3, because Cycles samples a CORNER
attribute slightly inside the corner and therefore blends neighbouring corners.
Measured over 965 objects, the drift is symmetric in sign (fraction positive
0.4986, so it does NOT walk the way finding 209's re-split did) but it is a mild
SMOOTHING operator: per-object variance ratio 0.9990, decreasing on 228 objects and
increasing on NONE.  One or two runs are harmless; running the bake repeatedly
would slowly flatten the gradients this pass exists to preserve.
So: **re-apply with `--nobake`** unless the procedural source itself has changed.
That flag exists for exactly this reason, not merely to save the 20 minutes.
"""
import bpy, os, sys, json, collections
import numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
sys.path.insert(0, ROOT + "/tools")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "--save" in argv
DRY = "--dry" in argv
NOBAKE = "--nobake" in argv        # relink/proxy only: the Col data is already
                                   # correct and a re-bake would be an identity
ONLY = argv[argv.index("--only") + 1] if "--only" in argv else None

ATTR = "Col"                       # the town's COLOR_0 convention (locksfoot kit,
                                   # overworld, weave: FLOAT_COLOR / CORNER)
VC_NODE = "surv_col"
PROXY_NODE = "surv_proxy"
PROXY_MIX = "surv_proxy_mix"

# --------------------------------------------------------------------- the spec
# group: lets a taste-sensitive subset be applied and committed on its own
# (--only bunting), which is what the brief asks for the pennants.
SPEC = [
    # ---- foliage: object-space Z ramps and noise ramps behind a Principled ----
    dict(mat="mat_grass",            method="vbake", group="foliage"),
    dict(mat="mat_fern",             method="vbake", group="foliage"),
    dict(mat="mat_leaf_autumn",      method="vbake", group="foliage"),
    dict(mat="mat_leaf_creeper",     method="vbake", group="foliage"),
    dict(mat="mat_leaf_autumn_far",  method="vbake", group="foliage"),
    # ---- cordage: a UV wave texture, and 47 of its 48 objects have no UVMap,
    #      so what it renders today is already a constant.  The bake captures
    #      whatever it actually evaluates to, degenerate UVs included, which is
    #      why this needs no separate decision: the bake IS the measurement.
    dict(mat="mat_rope",             method="vbake", group="rigging"),
    # ---- dark stone: voronoi blocks x noise, the family Lock Four must match ---
    dict(mat="mat_blackstone",       method="vbake", group="stone"),
    # ---- Lock Four's dark spill face: flat Diffuse + Glossy, no Principled -----
    dict(mat="mat_darkfall",         method="proxy", group="stone"),
    # ---- the ten bunting cloths: no Principled BSDF anywhere ------------------
    # the gate's six drive colour through an object-space noise weave (finding
    # 207) -> proxy carries the BAKED weave, so the runtime gets the variation
    dict(mat="mat_gate_flag_blue",   method="vbake+proxy", group="bunting"),
    dict(mat="mat_gate_flag_blue2",  method="vbake+proxy", group="bunting"),
    dict(mat="mat_gate_flag_bone",   method="vbake+proxy", group="bunting"),
    dict(mat="mat_gate_flag_ochre",  method="vbake+proxy", group="bunting"),
    dict(mat="mat_gate_flag_red",    method="vbake+proxy", group="bunting"),
    dict(mat="mat_gate_flag_red2",   method="vbake+proxy", group="bunting"),
    # the town's four are FLAT constants -> the proxy reads the Diffuse colour
    # straight out of the file rather than repeating it as a literal here
    dict(mat="mat_flag_blue",        method="proxy", group="bunting"),
    dict(mat="mat_flag_green",       method="proxy", group="bunting"),
    dict(mat="mat_flag_ochre",       method="proxy", group="bunting"),
    dict(mat="mat_flag_red",         method="proxy", group="bunting"),
]

# DELIBERATELY LEFT — with the reason, so the remainder in the gate report is
# explained rather than merely tolerated.
LEAVE = {
    "mat_haze_far": "fx_ volume, no surface shader; town_export.py strips fx_*",
    "mat_haze_mid": "fx_ volume, no surface shader; town_export.py strips fx_*",
    "mat_haze_rim": "fx_ volume, no surface shader; town_export.py strips fx_*",
    "mat_smoke":    "fx_ volume, no surface shader; town_export.py strips fx_*",
    "mat_spray":    "fx_ volume, no surface shader; town_export.py strips fx_*",
}

if ONLY:
    groups = set(ONLY.split(","))
    unknown = groups - {s["group"] for s in SPEC}
    assert not unknown, "unknown group(s) %s; have %s" % (sorted(unknown),
                                                          sorted({s["group"] for s in SPEC}))
    SPEC = [s for s in SPEC if s["group"] in groups]
    assert SPEC, "no spec rows in group(s) %r" % ONLY
NAMES = [s["mat"] for s in SPEC]

print("=" * 78)
print("MASTER SURVIVABILITY PASS   %s%s"
      % ("(DRY RUN) " if DRY else "", "group=%s " % ONLY if ONLY else ""))
print("=" * 78)
print("blend: %s" % bpy.data.filepath)
print("curing %d materials: %s" % (len(NAMES), ", ".join(NAMES)))


# ------------------------------------------------------------------ census
def census():
    return {o.name: (len(o.data.vertices), len(o.data.polygons))
            for o in bpy.data.objects if o.type == 'MESH'}


CEN0 = census()
print("census before: %d meshes, %d verts, %d polys"
      % (len(CEN0), sum(v[0] for v in CEN0.values()), sum(v[1] for v in CEN0.values())))


# ------------------------------------------------------------------ helpers
def real_nodes(nt):
    """Every node that is not part of this script's own scaffolding."""
    return [n for n in nt.nodes if n.name not in (VC_NODE, PROXY_NODE, PROXY_MIX)]


def main_bsdfs(mat):
    """The colour-bearing BSDFs the render actually uses (proxy excluded)."""
    out = []
    for n in real_nodes(mat.node_tree):
        if n.bl_idname in ('ShaderNodeBsdfPrincipled', 'ShaderNodeBsdfDiffuse',
                          'ShaderNodeBsdfTranslucent'):
            key = "Base Color" if n.bl_idname.endswith("Principled") else "Color"
            if key in n.inputs:
                out.append((n, n.inputs[key]))
    return out


def albedo_socket(mat):
    """The socket feeding this material's albedo today (post-cure: the VC node)."""
    for n, i in main_bsdfs(mat):
        if i.is_linked:
            return i.links[0].from_socket
    return None


def flat_albedo(mat):
    """The albedo of a material whose colour inputs are unlinked constants."""
    for n, i in main_bsdfs(mat):
        if not i.is_linked and n.bl_idname == 'ShaderNodeBsdfDiffuse':
            return tuple(i.default_value)[:3]
    for n, i in main_bsdfs(mat):
        if not i.is_linked:
            return tuple(i.default_value)[:3]
    return None


def objs_using(name):
    return [o for o in bpy.data.objects if o.type == 'MESH'
            and any(m and m.name == name for m in o.data.materials)]


# ------------------------------------------------------------------ the bake
BAKE = [s for s in SPEC if "vbake" in s["method"]]
bake_stats = {}

if BAKE and NOBAKE:
    print("\n--nobake: skipping the Cycles bake; Col is left as it stands and only\n"
          "the relink / proxy / export-factor step runs.  Safe because a re-bake of\n"
          "an already-cured material bakes Col from Col (identity).")
if BAKE and not DRY and not NOBAKE:
    sc = bpy.context.scene
    eng0 = sc.render.engine
    tgt0 = sc.render.bake.target
    hr0 = {o.name: o.hide_render for o in bpy.data.objects}
    hv0 = {o.name: o.hide_viewport for o in bpy.data.objects}
    he0 = {o.name: o.hide_get() for o in bpy.data.objects}

    # 1. rewire every baking material's output to an Emission of its albedo socket
    restore = []
    for s in BAKE:
        mat = bpy.data.materials.get(s["mat"])
        if mat is None:
            print("  !! %s missing" % s["mat"]); continue
        nt = mat.node_tree
        src = albedo_socket(mat)
        if src is None:
            print("  !! %s has no linked albedo to bake" % s["mat"]); continue
        out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
        orig = out.inputs['Surface'].links[0].from_socket
        em = nt.nodes.new('ShaderNodeEmission')
        em.name = "_surv_bake_em"
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(src, em.inputs['Color'])
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        restore.append((nt, out, orig, em))

    # 2. every object carrying a baking material gets a scratch attribute, and is
    #    made bakeable.  Cycles refuses an object that is not enabled for
    #    rendering, and 5 of these are render-hidden.
    targets = sorted({o.name for s in BAKE for o in objs_using(s["mat"])})
    print("\nbaking %d materials over %d objects" % (len(restore), len(targets)))
    prev_active = {}
    for n in targets:
        o = bpy.data.objects[n]
        me = o.data
        prev_active[n] = me.color_attributes.active_color_name
        a = me.color_attributes.get("_surv_bake")
        if a is None:
            a = me.color_attributes.new("_surv_bake", "FLOAT_COLOR", "CORNER")
        me.color_attributes.active_color = a
        o.hide_render = False
        o.hide_viewport = False
        o.hide_set(False)

    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    sc.render.bake.target = 'VERTEX_COLORS'
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True

    # bake in batches: one operator call over ~1600 objects is a single long
    # opaque stall, and a batch that fails says WHICH batch
    B = 60
    for i in range(0, len(targets), B):
        chunk = [bpy.data.objects[n] for n in targets[i:i + B]]
        bpy.ops.object.select_all(action='DESELECT')
        for o in chunk:
            o.select_set(True)
        bpy.context.view_layer.objects.active = chunk[0]
        bpy.ops.object.bake(type='EMIT')
        print("  baked %d/%d" % (min(i + B, len(targets)), len(targets)))

    # 3. copy the masked loops into Col, creating it where absent.
    #    Iterate unique MESH DATA, not objects: the vegetation is largely linked
    #    duplicates, so hundreds of these objects share one mesh, and doing this
    #    per object removes the scratch attribute on the first pass and then
    #    cannot find it for the object's 40 siblings.  (Baking shared data twice
    #    is harmless here because every one of these chains reads Texture
    #    Coordinate OBJECT — local space, identical for every instance.  A
    #    world-space chain could not be baked to shared data at all.)
    cured_mats = {s["mat"] for s in BAKE}
    meshes = {}
    for n in targets:
        meshes.setdefault(bpy.data.objects[n].data.name, bpy.data.objects[n].data)
    print("  copying into %s over %d unique meshes (%d objects)"
          % (ATTR, len(meshes), len(targets)))
    for me in meshes.values():
        src = me.color_attributes.get("_surv_bake")
        if src is None:
            continue
        d = np.zeros(len(src.data) * 4, dtype=np.float32)
        src.data.foreach_get("color", d)
        fresh = ATTR not in me.color_attributes
        col = me.color_attributes.get(ATTR)
        if col is None:
            col = me.color_attributes.new(ATTR, "FLOAT_COLOR", "CORNER")
        if fresh:
            # WHITE, not the bake.  COLOR_0 is a MULTIPLIER in glTF
            # (baseColorFactor x baseColorTexture x COLOR_0), so white is the
            # neutral value and a fresh attribute must start there.  Copying the
            # whole baked attribute instead is a trap that cost this pass a full
            # re-run: an EMIT bake of a material that is NOT being cured returns
            # BLACK (it emits nothing), so every co-resident material — 117k loops
            # of mat_vine, all the gate/shelf/waterfront clutter, lock_four_dam's
            # timber and iron — inherited a black COLOR_0 and would have shipped
            # BLACK to the runtime.  Blender never showed it, because those
            # materials do not read Col there, and the survival gate never showed
            # it either, because the gate looks for WHITE.  Finding 218.
            cur = np.ones(len(col.data) * 4, dtype=np.float32)
        else:
            cur = np.zeros(len(col.data) * 4, dtype=np.float32)
            col.data.foreach_get("color", cur)
        # ALWAYS masked: only the loops of faces whose material this pass cures.
        mask = np.zeros(len(col.data), dtype=bool)
        for p in me.polygons:
            m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
            if m and m.name in cured_mats:
                for li in p.loop_indices:
                    mask[li] = True
        m4 = np.repeat(mask, 4)
        cur[m4] = d[m4]
        col.data.foreach_set("color", cur)
        me.color_attributes.active_color = col
        me.color_attributes.render_color_index = list(me.color_attributes).index(col)
        me.color_attributes.remove(me.color_attributes["_surv_bake"])
        me.update()

    # 4. per-material bake statistics: what a vertex bake BUYS over a flat factor.
    #    Per unique mesh again, so 40 instances of one tuft count once and do not
    #    flatter the numbers by repetition.
    for s in BAKE:
        name = s["mat"]
        allv, within = [], []
        seen = {}
        for o in objs_using(name):
            seen.setdefault(o.data.name, o.data)
        for me in seen.values():
            col = me.color_attributes.get(ATTR)
            if col is None:
                continue
            d = np.zeros(len(col.data) * 4, dtype=np.float32)
            col.data.foreach_get("color", d)
            rgb = d.reshape(-1, 4)[:, :3]
            idx = [li for p in me.polygons
                   if p.material_index < len(me.materials)
                   and me.materials[p.material_index]
                   and me.materials[p.material_index].name == name
                   for li in p.loop_indices]
            if not idx:
                continue
            sub = rgb[idx]
            allv.append(sub)
            if len(sub) > 1:
                within.append(float(sub.std()))
        if allv:
            A = np.concatenate(allv)
            bake_stats[name] = dict(
                loops=int(len(A)), mean=[round(float(x), 4) for x in A.mean(axis=0)],
                std=round(float(A.std()), 4),
                within=round(float(np.mean(within)), 5) if within else 0.0)

    # 5. restore the node trees, visibility and the render engine
    for nt, out, orig, em in restore:
        nt.links.new(orig, out.inputs['Surface'])
        nt.nodes.remove(em)
    for n, v in hr0.items():
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = v
    for n, v in hv0.items():
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_viewport = v
    for n, v in he0.items():
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_set(v)
    sc.render.engine = eng0
    sc.render.bake.target = tgt0
    print("restored: engine=%s, hide_render/hide_viewport/eye reinstated" % eng0)


# ------------------------------------------------------------------ the relink
report = []
for s in SPEC:
    name, method = s["mat"], s["method"]
    mat = bpy.data.materials.get(name)
    if mat is None:
        report.append((name, method, "MISSING", "-")); continue
    nt = mat.node_tree
    nslots = len(objs_using(name))
    if DRY:
        report.append((name, method, "would cure", "%d objects" % nslots)); continue

    notes = []
    if "vbake" in method:
        vc = nt.nodes.get(VC_NODE)
        if vc is None:
            vc = nt.nodes.new('ShaderNodeVertexColor')
            vc.name = VC_NODE
            vc.label = "baked procedural albedo -> COLOR_0"
            notes.append("VC node added")
        else:
            notes.append("VC node reused")
        vc.layer_name = ATTR
        nrelink = 0
        for n, i in main_bsdfs(mat):
            if not i.is_linked or i.links[0].from_node is not vc:
                nt.links.new(vc.outputs['Color'], i)
                nrelink += 1
            # Neutralise the socket default too.  NOT because the exporter uses
            # it — verified against the GLB's own JSON, a linked Base Color
            # exports `baseColorFactor` ABSENT, i.e. 1.0, whatever the default
            # says.  It is set to 1.0 so the node graph cannot be MISREAD: a
            # 0.8 grey sitting behind a live link invites exactly the wrong
            # conclusion, and it cost this pass a wasted round of investigation
            # (finding 219).  Harmless in Blender; a linked socket ignores it.
            i.default_value = (1.0, 1.0, 1.0, 1.0)
        notes.append("%d colour input(s) relinked, default -> 1.0" % nrelink)

    if "proxy" in method:
        out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
        p = nt.nodes.get(PROXY_NODE)
        mx = nt.nodes.get(PROXY_MIX)
        if p is None:
            p = nt.nodes.new('ShaderNodeBsdfPrincipled')
            p.name = PROXY_NODE
            p.label = ("glTF EXPORT PROXY — Mix factor 0, contributes NOTHING to the "
                       "Blender render; it exists so the exporter finds a Principled")
            p.inputs['Roughness'].default_value = 0.9
            notes.append("proxy added")
        else:
            notes.append("proxy reused")
        if mx is None:
            inner = out.inputs['Surface'].links[0].from_socket
            mx = nt.nodes.new('ShaderNodeMixShader')
            mx.name = PROXY_MIX
            mx.label = "factor 0 -> branch A only"
            nt.links.new(inner, mx.inputs[1])
            nt.links.new(p.outputs['BSDF'], mx.inputs[2])
            nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
        mx.inputs[0].default_value = 0.0
        # colour: the baked vertex colour for the noise-woven gate flags, the
        # material's own flat Diffuse colour for the town's four
        if "vbake" in method:
            vc = nt.nodes.get(VC_NODE)
            nt.links.new(vc.outputs['Color'], p.inputs['Base Color'])
            p.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)   # see above
            notes.append("proxy reads %s, default -> 1.0" % ATTR)
        else:
            col = flat_albedo(mat)
            if col is None:
                notes.append("NO FLAT COLOUR FOUND")
            else:
                p.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
                notes.append("proxy flat=(%.3f, %.3f, %.3f)" % col)
        # mat_darkfall's render is 72% Glossy: give the proxy a matching
        # roughness so the runtime reads as wet stone, not as matte paint
        if name == "mat_darkfall":
            p.inputs['Roughness'].default_value = 0.25
            notes.append("rough=0.25 (wet)")

    mat["surv_method"] = method
    report.append((name, method, "cured", "; ".join(notes)))

# ------------------------------------------------------------------ report
print("\n" + "=" * 78)
print("CURE TABLE")
print("=" * 78)
print("%-24s %-13s %-10s %s" % ("material", "method", "status", "notes"))
for name, method, status, notes in report:
    print("%-24s %-13s %-10s %s" % (name, method, status, notes))

if bake_stats:
    print("\n" + "=" * 78)
    print("BAKE STATISTICS — 'within' is the mean per-object std of the baked albedo:")
    print("it is what a VERTEX BAKE buys over a single flat baseColorFactor.")
    print("=" * 78)
    print("%-24s %8s %-22s %8s %9s" % ("material", "loops", "mean albedo", "std", "within"))
    for n in sorted(bake_stats):
        b = bake_stats[n]
        print("%-24s %8d %-22s %8.4f %9.5f  %s"
              % (n, b["loops"], str(b["mean"]), b["std"], b["within"],
                 "gradient" if b["within"] > 0.004 else "~flat"))

print("\nDELIBERATELY LEFT:")
for n, why in sorted(LEAVE.items()):
    print("  %-16s %s" % (n, why))

# ------------------------------------------------------------------ assertions
CEN1 = census()
fails = []

# COLOR_0 NEUTRALITY — every material that this pass did NOT cure but which shares
# a mesh with one that it did must sit on NEUTRAL (white) COLOR_0 loops, because
# glTF multiplies by COLOR_0 and the runtime will apply it whether the material
# asked for it or not.  This is the gate for finding 218: the white-export gate
# cannot see a black regression, and the Blender render cannot see either, so the
# only place it can be caught is here, on the data.
cured_all = {s["mat"] for s in SPEC}
dark = collections.Counter()
seen_m = set()
for o in bpy.data.objects:
    if o.type != 'MESH' or o.data.name in seen_m:
        continue
    seen_m.add(o.data.name)
    me = o.data
    col = me.color_attributes.get(ATTR)
    if col is None or not ({m.name for m in me.materials if m} & cured_all):
        continue
    d = np.zeros(len(col.data) * 4, dtype=np.float32)
    col.data.foreach_get("color", d)
    rgb = d.reshape(-1, 4)[:, :3]
    for p in me.polygons:
        m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
        if m is None or m.name in cured_all:
            continue
        for li in p.loop_indices:
            if rgb[li].max() < 0.02:
                dark[m.name] += 1
if dark:
    fails.append("non-cured materials on near-BLACK COLOR_0: %s"
                 % dict(dark.most_common(8)))
print("\nCOLOR_0 NEUTRALITY: %s"
      % ("OK — every co-resident material sits on neutral or its own colour"
         if not dark else "FAILED — %d materials on black loops" % len(dark)))
if set(CEN0) != set(CEN1):
    fails.append("object set changed: +%s -%s"
                 % (sorted(set(CEN1) - set(CEN0))[:5], sorted(set(CEN0) - set(CEN1))[:5]))
for n in CEN0:
    if n in CEN1 and CEN0[n] != CEN1[n]:
        fails.append("%s geometry changed %s -> %s" % (n, CEN0[n], CEN1[n]))
print("\nGEOMETRY ASSERTION: %d meshes, %d verts, %d polys  ->  %s"
      % (len(CEN1), sum(v[0] for v in CEN1.values()), sum(v[1] for v in CEN1.values()),
         "UNCHANGED" if not fails else "CHANGED (%d)" % len(fails)))
for f in fails[:10]:
    print("  !! %s" % f)

st = ROOT + "/docs/qa/districts/surv_report%s.json" % (("_" + ONLY) if ONLY else "")
os.makedirs(os.path.dirname(st), exist_ok=True)
with open(st, "w") as fh:
    json.dump(dict(report=[dict(mat=a, method=b, status=c, notes=d) for a, b, c, d in report],
                   bake=bake_stats, leave=LEAVE,
                   census=dict(meshes=len(CEN1), verts=sum(v[0] for v in CEN1.values()),
                               polys=sum(v[1] for v in CEN1.values()))), fh, indent=1)
print("wrote %s" % st)

if fails:
    sys.exit("GEOMETRY CHANGED — refusing to save a materials-only pass that moved geometry")
if SAVE and not DRY:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("NOT SAVED (pass --save)")
