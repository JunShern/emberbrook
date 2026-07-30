"""water_flow.py — make Dellhollow's river read as MOVING water in a still frame.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/water_flow.py
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/water_flow.py -- save
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/water_flow.py -- revert save

THE NOTE THIS ANSWERS: "it is a river."  Before this, `m_water` was a bare
Principled — Base Color (0.04, 0.105, 0.12), Roughness 0.10, nothing else.  At
roughness 0.1 that is very nearly a mirror, and a mirror is why it read as a
pond: a still frame of moving water is DEFINED by its broken reflection, and a
mirror has none.  There is no animation to hide behind here; the stills have to
carry it.

THREE THINGS SELL CURRENT, and this tree does each one.

 1. ANISOTROPY — the whole trick.  Ripples on a river are long along the flow and
    short across it.  World position is pushed through a Mapping scaled
    (FLOW_SQUASH, 1, 1) before the noise is sampled, so features stretch ~9x
    along +x.  Sampling in WORLD space, not object space, is deliberate: the four
    pools are four separate objects at four heights and the ripple must not
    restart at each seam.
 2. OBSTACLE RESPONSE — an Ambient Occlusion node with a short distance is really
    a "how close is other geometry" probe: 1.0 in open water, falling off against
    the weir, the lock walls, the mooring piles, the hulls and the slipway.
    Inverted, ramped and roughened by a cross-flow noise so the band is ragged
    rather than a clean offset, it drives BOTH a whitening of the albedo and a
    roughness rise.  Foam where the water meets the town, with no hand-placed
    foam geometry and nothing to re-sync when the town moves — which matters in a
    blend where the districts are still being rebuilt.
 3. REFLECTION BREAKUP — the same two noises drive a Bump.  Vertical streaking of
    the lantern and window reflections falls out of the anisotropy for free: a
    ripple that is long along x tilts the surface ACROSS x, and that is the axis
    that smears a reflection vertically in these cameras.

THE FLOW AXIS IS MEASURED, NOT TYPED.  The pools' own surface heights step down
from upstream to downstream (+3.4 -> 0.0 -> -1.55 -> -4.0 as x increases), so the
river runs +x through the whole town and one direction serves every pool.  The
script reads those heights out of the blend and asserts the monotone step rather
than trusting this paragraph.

THE TURQUOISE IS NOT TOUCHED.  The base colour stays exactly (0.04, 0.105, 0.12);
its saturation was ruled on separately tonight and goes to the user's taste board
as its own knob.  This pass changes how the surface BEHAVES, not what colour it is.

GLTF SURVIVAL — the one real hazard, and it took two measured failures to get
right.  cine_bake.py's GLB export takes EVERY camera-visible mesh, not just
walk_, so the water surfaces really are in scene.glb, and m_water carries no
texture and no COLOR_0 — nothing to multiply a missing factor against.

  ATTEMPT 1, the obvious build: one Principled whose Base Color is a Mix of deep
  water and foam.  The exporter cannot express the Mix, so it writes NO
  baseColorFactor, and the glTF default makes the river literally WHITE in the
  runtime.  master_glb_albedo.py flagged it.
  ATTEMPT 2, master_survivability.py's export proxy: nest the render tree in an
  outer MixShader against a Principled carrying the flat turquoise.  Still white.
  That cure works for mat_darkfall and the pennants because THEIR render branch
  holds no Principled at all, so the exporter cannot help but find the proxy.
  Here the render branch holds one, and the exporter took it from both branch
  orders.
  WHAT SHIPS: no proxy, and no linked Base Color anywhere.  Water and foam are
  two Principled lobes with FLAT colours mixed by the foam mask — which is what a
  mixed albedo physically is anyway.  The exporter finds a real colour whichever
  lobe it reaches, the render is identical, and m_water now exports
  baseColorFactor (0.04, 0.105, 0.12).  Verified by master_glb_albedo.py reading
  the GLB's own JSON, not a re-import.

An image texture would also work, and is the right answer the day the water needs
to survive as ART in the runtime rather than as a depth-tested blocker under a
baked plate.  It is not the right answer today, and it would add binary assets to
carry.

IDEMPOTENT BY REBUILD.  The tree is generated, so the honest way to be idempotent
is to clear and regenerate it every run rather than to patch it in place and hope
the patch is exact.  `-- revert` restores the original bare Principled.
"""
import bpy, os, sys

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = ("save" in argv) or ("--save" in argv)
REVERT = ("revert" in argv) or ("--revert" in argv)

MAT = "m_water"
VERSION = 1
DEEP = (0.04, 0.105, 0.12)        # ruled: unchanged
FOAM = (0.55, 0.60, 0.62)         # aerated white, not paper white
FLOW_SQUASH = 0.11                # ~9x longer along the flow than across it
RIPPLE_SCALE = 2.2                # the long swells
CHOP_SCALE = 9.0                  # the cross-flow chop
BUMP_STRENGTH = 0.26
ROUGH_OPEN = 0.09                 # glassy but not a mirror
ROUGH_FOAM = 0.62                 # aerated water scatters
AO_DIST = 1.6                     # "near the town" in metres


def flow_axis_check():
    """Assert the +x flow the anisotropy assumes, from the pools themselves."""
    pools = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if not any(m and m.name == MAT for m in ob.data.materials):
            continue
        ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
        pools.append((sum(p.x for p in ws) / len(ws), sum(p.z for p in ws) / len(ws),
                      ob.name))
    assert pools, "no %s objects — nothing to flow" % MAT
    pools.sort()
    zs = [z for _, z, _ in pools]
    mono = all(zs[i] >= zs[i + 1] for i in range(len(zs) - 1))
    print("flow axis: %d pools, downstream = +x, surface z %s  monotone=%s"
          % (len(pools), [round(z, 2) for z in zs], mono))
    for x, z, n in pools:
        print("   %-24s x=%7.1f  z=%6.2f" % (n, x, z))
    assert mono, ("the pools do not step DOWN with +x (%s) — the flow direction "
                  "this shader stretches along is wrong for this river" % zs)
    return pools


def build(mat):
    nt = mat.node_tree
    nt.nodes.clear()

    def n(t, name, **kw):
        node = nt.nodes.new(t)
        node.name = name
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def link(a, sa, b, sb):
        nt.links.new(a.outputs[sa], b.inputs[sb])

    def cin(node, sock):
        """ShaderNodeMix carries A/B three times (float, vector, colour)."""
        for i in node.inputs:
            if i.name == sock:
                try:
                    if len(i.default_value) == 4:
                        return i
                except TypeError:
                    continue
        raise KeyError(sock)

    def fin(node, sock):
        for i in node.inputs:
            if i.name == sock and isinstance(i.default_value, float):
                return i
        raise KeyError(sock)

    out = n('ShaderNodeOutputMaterial', "Material Output")

    # --- world position, squashed along the flow -------------------------------
    geo = n('ShaderNodeNewGeometry', "geo")
    mapping = n('ShaderNodeMapping', "flow_map")
    mapping.inputs['Scale'].default_value = (FLOW_SQUASH, 1.0, 1.0)
    link(geo, 'Position', mapping, 'Vector')

    ripple = n('ShaderNodeTexNoise', "flow_ripple")
    ripple.inputs['Scale'].default_value = RIPPLE_SCALE
    ripple.inputs['Detail'].default_value = 6.0
    ripple.inputs['Roughness'].default_value = 0.55
    link(mapping, 'Vector', ripple, 'Vector')

    # a second, finer, LESS squashed noise: chop riding on the swells
    chop_map = n('ShaderNodeMapping', "chop_map")
    chop_map.inputs['Scale'].default_value = (0.35, 1.5, 1.0)
    link(geo, 'Position', chop_map, 'Vector')
    chop = n('ShaderNodeTexNoise', "flow_chop")
    chop.inputs['Scale'].default_value = CHOP_SCALE
    chop.inputs['Detail'].default_value = 4.0
    link(chop_map, 'Vector', chop, 'Vector')

    surf = n('ShaderNodeMix', "surface_mix")           # swells + chop
    surf.data_type = 'FLOAT'
    fin(surf, 'Factor').default_value = 0.35
    link(ripple, 'Fac', surf, 'A')
    link(chop, 'Fac', surf, 'B')

    # --- obstacle proximity ----------------------------------------------------
    ao = n('ShaderNodeAmbientOcclusion', "obstacle_ao")
    ao.samples = 8
    ao.inside = False
    ao.only_local = True
    ao.inputs['Distance'].default_value = AO_DIST

    inv = n('ShaderNodeMath', "ao_invert", operation='SUBTRACT')
    inv.inputs[0].default_value = 1.0
    link(ao, 'AO', inv, 1)

    band = n('ShaderNodeValToRGB', "foam_band")        # tighten the falloff
    band.color_ramp.elements[0].position = 0.18
    band.color_ramp.elements[1].position = 0.72
    link(inv, 'Value', band, 'Fac')

    ragged = n('ShaderNodeMath', "foam_ragged", operation='MULTIPLY')
    link(band, 'Color', ragged, 0)
    link(chop, 'Fac', ragged, 1)

    foam = n('ShaderNodeMath', "foam_gain", operation='MULTIPLY')
    foam.inputs[1].default_value = 2.4
    link(ragged, 'Value', foam, 0)
    foam_c = n('ShaderNodeClamp', "foam_clamp")
    link(foam, 'Value', foam_c, 'Value')

    # --- normal: the reflection breakup ---------------------------------------
    bump = n('ShaderNodeBump', "ripple_bump")
    bump.inputs['Strength'].default_value = BUMP_STRENGTH
    bump.inputs['Distance'].default_value = 0.12
    link(surf, 'Result', bump, 'Height')

    # --- TWO FLAT-COLOURED LOBES, mixed by the foam mask -----------------------
    # This is the shape that survives glTF, and getting here cost two measured
    # failures worth recording. The obvious build — one Principled whose Base
    # Color is a Mix of deep water and foam — exports NO baseColorFactor at all,
    # because the exporter cannot express the Mix; on a material with no texture
    # and no COLOR_0 the glTF default then makes the river literally WHITE in the
    # runtime (master_glb_albedo.py flags exactly this, and flagged it here).
    # master_survivability's export-proxy cure does NOT rescue it either: that
    # trick works for mat_darkfall and the pennants because their render branch
    # holds no Principled, so the exporter's search cannot help but find the
    # proxy. Here the render branch holds one, and the exporter took it from
    # BOTH branch orders — measured, twice.
    # So: no proxy, and no linked Base Color anywhere. Water and foam are two
    # Principleds with FLAT colours mixed by the foam mask, which is what a mixed
    # albedo physically is anyway. The exporter finds a real colour whichever
    # lobe it picks, and the render is unchanged.
    water = n('ShaderNodeBsdfPrincipled', "water_lobe")
    water.inputs['Base Color'].default_value = DEEP + (1.0,)
    water.inputs['Roughness'].default_value = ROUGH_OPEN
    water.inputs['IOR'].default_value = 1.33
    link(bump, 'Normal', water, 'Normal')

    foam_lobe = n('ShaderNodeBsdfPrincipled', "foam_lobe")
    foam_lobe.inputs['Base Color'].default_value = FOAM + (1.0,)
    foam_lobe.inputs['Roughness'].default_value = ROUGH_FOAM
    foam_lobe.inputs['IOR'].default_value = 1.33
    link(bump, 'Normal', foam_lobe, 'Normal')

    mx = n('ShaderNodeMixShader', "foam_mix")
    mx.label = "0 = open water, 1 = foam against the town"
    link(foam_c, 'Result', mx, 'Fac')
    link(water, 'BSDF', mx, 1)
    link(foam_lobe, 'BSDF', mx, 2)
    link(mx, 'Shader', out, 'Surface')

    mat["water_flow_version"] = VERSION
    mat["surv_method"] = "flat-lobes"


def revert(mat):
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = DEEP + (1.0,)
    b.inputs['Roughness'].default_value = 0.1
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    if "water_flow_version" in mat:
        del mat["water_flow_version"]


print("=" * 78)
print("RIVER FLOW  %s" % ("(REVERT)" if REVERT else ""))
print("=" * 78)
print("blend: %s" % bpy.data.filepath)

mat = bpy.data.materials.get(MAT)
assert mat is not None, "%s missing" % MAT
pools = flow_axis_check()

had = mat.get("water_flow_version")
if REVERT:
    revert(mat)
    print("\nreverted %s to the bare Principled (was version %s)" % (MAT, had))
else:
    build(mat)
    print("\n%s rebuilt: %d nodes, %d links  (was version %s, now %d)"
          % (MAT, len(mat.node_tree.nodes), len(mat.node_tree.links), had, VERSION))
    print("  anisotropy   world position x %.2f  -> ~%.0fx longer along the flow"
          % (FLOW_SQUASH, 1.0 / FLOW_SQUASH))
    print("  ripple/chop  noise %.1f / %.1f, bump strength %.2f"
          % (RIPPLE_SCALE, CHOP_SCALE, BUMP_STRENGTH))
    print("  obstacles    AO distance %.1f m -> albedo %s..%s, roughness %.2f..%.2f"
          % (AO_DIST, DEEP, FOAM, ROUGH_OPEN, ROUGH_FOAM))
    print("  base colour  %s  UNCHANGED (its saturation is a separate ruling)" % (DEEP,))
    print("  export shape two flat-coloured Principled lobes mixed by the foam\n"
          "               mask — no linked Base Color anywhere, so glTF gets a real colour")
print("  wears it     %s" % ", ".join(sorted(n for _, _, n in pools)))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `-- save` to write the master)")
