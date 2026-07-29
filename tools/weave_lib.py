"""weave_lib.py — glTF-safe material + mesh finishing for the Weave pass.

  from weave_lib import MAT, PAL, finish, tint

WHY THIS EXISTS (canon, 2026-07-29): the user walked the live townwalk and found
516 primitives rendering WHITE.  Procedural node-tree materials — the whole
`mat_rock` / `mat_deck` family the Boatyard, Waterfront and Locksfoot build with
— are object-space box projection plus noise, and the glTF exporter carries
neither, so they ship as default white.  Blender's own render hides it
completely.  Every material this pass touches must therefore survive a round
trip: vertex colour, image texture with real UVs, or a flat baseColorFactor.

Rather than invent a fourth material language, this reuses the LOCKSFOOT KIT's
eight materials, which were built to exactly that contract (`locksfoot_kit.py`,
findings 80-82) and are already in the master — and, since the kit dedup, are
now eight datablocks rather than 2000.  The kit's shape is
`ImageTexture x VertexColor -> Base Color`, which the exporter writes as
`baseColorTexture * COLOR_0`.

That contract has one obligation: **every mesh must carry a `Col` FLOAT_COLOR
CORNER attribute and a `UVMap`**, or the VertexColor node returns white and an
untextured material renders as blown white — the very failure this is here to
avoid.  `finish()` is the one call that discharges it, applied to the FINAL
joined object (not to the parts, because `join_meshes` round-trips through
bmesh and a colour layer is not guaranteed across that).

A textured material's vertex colour is pre-divided by the map's mean luminance
(finding 81): `weathered_planks` means 0.269, so deck colours carry a x1.64
gain, and without it every textured part comes back a value under the untextured
parts beside it.  The gain is MEASURED from the image in the file, not
hard-coded, so it cannot drift away from the map it belongs to.
"""
import bpy, math

# --------------------------------------------------------------------- colour
def srgb(h):
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# The town palette (Boatyard/Waterfront/Locksfoot, read off the map's style
# block) plus the Weave's own three: a weaver's tier is defined by its DYE, and
# indigo / madder / weld are the three a river town would actually have.
# PALETTE, revised on the user's steer (2026-07-29): the first pass inherited the
# Locksfoot kit's values directly, and against the cliff the houses read TOO DARK
# and out of key with the landscape.  Re-grounded by MEASURING the accepted
# districts' own rendered frames rather than by eye — the warm painted timber in
# `boatyard_v10`, `locksfoot_v3_crestwalk` and `gate_v6_gate` lands at sRGB
# #74481d .. #be845b on screen, with Locksfoot (lit by the same rig as this tier)
# at #b17853.  This tier receives 78% of that district's key, so its albedos have
# to sit ABOVE the kit's to land in the same screen family: the painted family is
# lifted ~1.6x in linear and warmed, keeping the map's own three hues (oxblood
# red / moss green / faded blue) and adding a cream, which is what actually makes
# a cluster of small houses read as a village rather than as one dark mass.
PAL = {k: srgb(v) for k, v in {
    "oxblood":   "a85a44", "mossgreen": "78815a", "fadeblue":  "6c8794",
    "cream":     "c4a878", "ochre":     "b08447",
    "timber":    "8b6f4b", "timberdk":  "6a5236", "deck":      "9c8258",
    "freshwood": "bda079", "stonegrey": "7a7160", "stoneblk":  "24211f",
    "iron":      "3a322c", "irondk":    "241f1c", "rust":      "6b452a",
    "rope":      "8d7a53", "canvas":    "9a8a6a", "glass":     "ffc27a",
    "shingle":   "6e7455", "mosswood":  "5c6a49", "leaf":      "4c6340",
    "leafdry":   "7a7048", "leafturn":  "9c6428",
    "cloth_r":   "a24a3c", "cloth_g":   "5c7a52", "cloth_b":   "51707f",
    "cloth_y":   "b09140", "cloth_w":   "b4ad9c", "cloth_gy":  "8e8a7e",
    # the Weave's own: the dye pots the district is named for
    "dye_indigo": "3a4c72", "dye_madder": "8e3c2e", "dye_weld": "94842e",
    "reed":      "a08a5c",            # woven screens, baskets, drying frames
    "net":       "8a836a",
    "water":     "1b4344", "foam": "8e9a94",
    # the masonry the houses now actually stand on
    "rockwall":  "6d6455", "rockwall2": "5d5648",
}.items()}


# ------------------------------------------------------------------ materials
_GAIN = {}


def _gain(m):
    """Vertex-colour pre-gain for a textured material (finding 81), MEASURED."""
    if m.name in _GAIN:
        return _GAIN[m.name]
    g = 1.0
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.bl_idname == "ShaderNodeTexImage" and n.image:
                try:
                    import numpy as np
                    px = np.array(n.image.pixels[:]).reshape(-1, 4)[:, :3]
                    g = float(min(max(0.44 / max(px.mean(), 0.03), 1.0), 3.2))
                except Exception:
                    g = 1.0
                break
    _GAIN[m.name] = g
    return g


def MAT(name):
    """The kit material by canonical name — never a `.NNN` copy."""
    m = bpy.data.materials.get(name)
    assert m is not None, ("%s is not in this blend: run the Locksfoot kit append "
                           "first, or the Weave has no glTF-safe material" % name)
    assert not name.endswith(tuple(".%03d" % i for i in range(1000))), name
    return m


def uvscale(m):
    return float(m.get("uvscale", 0.45))


def textured(m):
    if not m.use_nodes:
        return False
    return any(n.bl_idname == "ShaderNodeTexImage" and n.image for n in m.node_tree.nodes)


# ------------------------------------------------------------------ finishing
def finish(ob, tints, jitter=0.06, rng=None):
    """Give a finished object its `UVMap` and its `Col`, per material slot.

    `tints` maps a material NAME to a linear RGB (usually a PAL entry).  Faces on
    a material with no entry get PAL['timber'] so nothing can silently ship white.
    """
    if ob is None:
        return ob
    me = ob.data
    if not me.polygons:
        return ob
    mats = [s for s in me.materials]
    assert mats, "%s has no material slot — it would export as default white" % ob.name

    # ---- UVs: world box projection, per polygon, at the material's own scale
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    Mw = ob.matrix_basis
    for p in me.polygons:
        m = mats[min(p.material_index, len(mats) - 1)]
        s = uvscale(m) if m else 0.45
        n = (Mw.to_3x3() @ p.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        iu, iv = (1, 2) if ax == 0 else ((0, 2) if ax == 1 else (0, 1))
        for li in p.loop_indices:
            w = Mw @ me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (w[iu] * s, w[iv] * s)

    # ---- Col: one tint per material slot, with a little per-face variation so a
    #      50 m run of decking is not one flat sheet (manifest 95's real lesson —
    #      what the eye reads as "computer" is the absence of variation)
    att = me.color_attributes.get("Col")
    if att is None:
        att = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    me.color_attributes.active_color = att
    me.color_attributes.render_color_index = 0
    import random
    R = rng or random.Random(hash(ob.name) & 0xffff)
    fallback = PAL["timber"]
    for p in me.polygons:
        m = mats[min(p.material_index, len(mats) - 1)]
        base = tints.get(m.name if m else "", fallback)
        g = _gain(m) if (m and textured(m)) else 1.0
        k = 1.0 + (R.random() - 0.5) * 2.0 * jitter
        c = (min(base[0] * g * k, 1.0), min(base[1] * g * k, 1.0),
             min(base[2] * g * k, 1.0), 1.0)
        for li in p.loop_indices:
            att.data[li].color = c
    return ob


def audit_gltf_safe(objs):
    """Every object must carry Col + UVMap and a material the exporter can write.

    This is the gate the 516 white primitives would have failed.
    """
    bad = []
    for ob in objs:
        if ob is None or ob.type != 'MESH' or not ob.data.polygons:
            continue
        me = ob.data
        if "Col" not in me.color_attributes:
            bad.append((ob.name, "no Col attribute"))
        if "UVMap" not in me.uv_layers:
            bad.append((ob.name, "no UVMap"))
        if not [s for s in me.materials if s]:
            bad.append((ob.name, "no material"))
            continue
        for s in me.materials:
            if s is None:
                continue
            if not s.use_nodes:
                continue
            names = {n.bl_idname for n in s.node_tree.nodes}
            illegal = names - {"ShaderNodeBsdfPrincipled", "ShaderNodeOutputMaterial",
                               "ShaderNodeTexImage", "ShaderNodeUVMap",
                               "ShaderNodeVertexColor", "ShaderNodeMix"}
            if illegal:
                bad.append((ob.name, "%s has procedural nodes %s"
                            % (s.name, sorted(illegal))))
    return bad
