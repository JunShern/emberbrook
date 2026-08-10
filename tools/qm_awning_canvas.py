"""qm_awning_canvas.py — THE AWNING IS THE NEAREST SURFACE IN CROSSING AND THE ONLY
ONE IN THE FRAME WITH NO TEXTURE AT ALL.  Give it the town's own textured-material
shape, with a cloth the town does not yet own.

  # 1. write the three maps (no Blender, deterministic, tileable)
  python3 tools/qm_awning_canvas.py maps

  # 2. wire mat_qm_awning to them
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/qm_awning_canvas.py -- wire [save] [--scale 1.9] [--dry]

WHAT WAS MEASURED FIRST, AND WHAT IT REFUTED (round 11).  `qm_awning` is **1.45% of
the crossing frame at 5.3 m — the nearest significant surface in it — and the plate
resolves it at 1.9 mm per pixel.**  Median local SD of luminance by box scale, with
silhouette and depth-step pixels dropped:

    subject          dist   mm/px |  SD 3px    SD 5px    SD 9px   SD 17px
    qm_awning         5.3     1.9 |   0.00      3.56      5.06      6.64
    mat_qm_paving    10.5     3.9 |   4.26      6.40      7.54      8.63
    mat_deck         30.1    11.3 |   6.09      8.34     12.33     19.62
    mat_timber       20.3     8.5 |   3.53      5.27     11.13     20.99
    mat_rock         91.3    35.4 |   1.21      1.66      2.18      2.87

It is the ONLY surface in the frame whose median 3x3 SD is exactly zero, and it is
the surface the plate samples two to eighteen times more finely than any other.  So
Emberbrook round 2's sibling finding — "untextured" can mean "textured below the
plate's Nyquist" — DOES NOT APPLY HERE: below Nyquist looks like signal at coarse
scales and none at fine, and this is none at 6 mm on a surface that could carry
detail down to about 4 mm.  It is untextured, full stop.

AND BOTH OF THE CONSTRAINTS THE HANDOVER CARRIED ARE FALSE, which is why this is a
material edit and not "a job and not a cheap round":

  * "it needs an image texture WITH UVs" — the town's 61 textured materials do not
    use UVs at all.  Every one of them is `Texture Coordinate.Object -> Mapping
    (scale 1.9) -> Image Texture` x4 (Diffuse / AO / Rough / nor_gl).  This copies
    that shape exactly, with BOX projection because an awning is a shallow tent and
    a flat XY projection would streak its end faces.
  * "a procedural weave would be Blender-only and make the plate and the runtime
    disagree" — Dellhollow's runtime NEVER DRAWS THIS MATERIAL.  `del-cine` is a
    pre-rendered bg.png + depth.png bundle and its `scene.glb` is collision; the
    plate IS the art.  (The constraint is real for `emb-townwalk`, which ships a
    dressed realtime tier.  It is not real here.)

THE VERTEX COLOUR IS PRESERVED, AND THAT IS THE POINT.  `mat_qm_awning`'s only signal
today is `Col`, which carries the thirteen alternating stripe columns round 8 built
and round 9 re-derived.  The image MULTIPLIES it, so the stripes are untouched and
what is added is the 4 mm weave and the 20-180 mm wear the surface has never had.
The map's own mean is held near 0.90 on purpose: round 9 spent a whole round pulling
this canvas's value down (albedo 0.320 -> 0.144, specular 0.50 -> 0.15) to clear the
judge's "white", and a texture that brightened it would undo that.  A multiply can
only darken.

WHAT THE PLATE CAN ACTUALLY SHOW, which is what the maps are designed for: at
1.9 mm/px a real canvas weave at 3-4 mm is two pixels and the denoiser will take most
of it (that is exactly Emberbrook's lesson, applied forward instead of backward).  So
the weave is there for the roughness and normal to bite on, and the READABLE signal is
the wear field at 20-180 mm, which is the band where every other surface in the frame
has its texture.
"""
import os, sys, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXDIR = os.path.join(ROOT, "tools/textures")
NAMES = {"d": "canvas_awning_Diffuse.jpg",
         "r": "canvas_awning_Rough.jpg",
         "n": "canvas_awning_nor_gl.jpg"}
N = 1024
SEED = 20260810


# --------------------------------------------------------------- the maps ------
def _tile_noise(n, cells, rng):
    """Value noise that WRAPS: a cells x cells lattice, smoothstep-interpolated,
    indexed modulo `cells`, so the image tiles by construction."""
    import numpy as np
    g = rng.random((cells, cells)).astype(np.float32)
    t = (np.arange(n, dtype=np.float32) + 0.5) * cells / n
    i0 = np.floor(t).astype(int) % cells
    i1 = (i0 + 1) % cells
    f = t - np.floor(t)
    f = f * f * (3.0 - 2.0 * f)
    a = g[np.ix_(i0, i0)] * (1 - f)[:, None] + g[np.ix_(i1, i0)] * f[:, None]
    b = g[np.ix_(i0, i1)] * (1 - f)[:, None] + g[np.ix_(i1, i1)] * f[:, None]
    return a * (1 - f)[None, :] + b * f[None, :]


def make_maps():
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(SEED)
    u = (np.arange(N, dtype=np.float32) + 0.5) / N
    U, V = np.meshgrid(u, u)

    # PLAIN WEAVE.  128 warps and 128 wefts over one tile; at the shipped mapping
    # scale that is a ~4 mm thread, i.e. two plate pixels at the awning's distance.
    W = 128
    warp = 0.5 + 0.5 * np.sin(2 * math.pi * W * U)
    weft = 0.5 + 0.5 * np.sin(2 * math.pi * W * V)
    over = ((np.floor(W * U) + np.floor(W * V)) % 2).astype(np.float32)
    weave = over * warp + (1.0 - over) * weft            # 0..1

    # WEAR.  Four wrapped octaves at 341 / 170 / 85 / 42 texels — 180 / 88 / 44 /
    # 22 mm at the shipped scale, which is the band every other surface in the
    # frame carries its texture in and the only band the plate can resolve here.
    wear = np.zeros((N, N), np.float32)
    amp = 0.0
    for cells, a in ((3, 1.0), (6, 0.55), (12, 0.30), (24, 0.16)):
        wear += a * _tile_noise(N, cells, rng)
        amp += a
    wear /= amp
    wear = (wear - wear.min()) / max(float(wear.max() - wear.min()), 1e-6)

    d = 1.0 - 0.085 * (1.0 - weave) - 0.20 * (wear - 0.5)
    d *= 0.90 / float(d.mean())                          # a multiply may only darken
    d = np.clip(d, 0.0, 1.0)
    r = np.clip(0.76 + 0.14 * (1.0 - weave) + 0.06 * (wear - 0.5), 0.0, 1.0)

    # tangent-space normal from a height field, central differences with WRAP.
    #
    # THE WEAVE IS **NOT** IN THE HEIGHT FIELD, AND THE PLATE IS WHY (round 13).
    # This file used to read `h = 0.65 * weave + 0.35 * wear` on the reasoning above
    # that "a 3-4 mm weave is two pixels and the denoiser will take most of it".  IT
    # DID NOT.  An FFT of a 128 px patch of the awning inside its own ray-derived mask
    # on the SHIPPED plate puts a peak at **k = 62 of a possible 64 — period 2.06 plate
    # px = 4.5 mm on the cloth, reproducing this file's own 4.11 mm thread to 10%** —
    # carrying **8.4e5 of power against 1-5e4 in every neighbouring high-band bin, i.e.
    # forty times its own band.**  A REGULAR LATTICE AT EXACTLY NYQUIST DOES NOT
    # AVERAGE OUT, IT ALIASES, and it aliased into a diamond gauze that photographs as
    # wire screen: the surface reads as a grey mesh panel, which is half of what four
    # rounds of judges have been calling "an untextured grey polygon".
    #
    # A NORMAL MAP IS A SLOPE, AND A SLOPE AT NYQUIST IS THE LIGHTING AMPLIFYING THE
    # ALIAS.  The weave stays in the DIFFUSE (0.085 amplitude) and the ROUGHNESS (0.14),
    # where it is a sub-visible modulation of two quantities the eye integrates; it is
    # removed only from the quantity that turns it into a lit pattern.  The wear field
    # at 22-180 mm — 10 to 80 plate px — is the band this surface can actually carry
    # relief in, and it is now the whole of the height field.
    h = wear
    STRENGTH = 6.0
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * STRENGTH
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * STRENGTH
    nz = np.ones_like(h)
    ln = np.sqrt(dx * dx + dy * dy + nz * nz)
    nrm = np.stack([(-dx / ln * 0.5 + 0.5), (-dy / ln * 0.5 + 0.5), (nz / ln * 0.5 + 0.5)], -1)

    os.makedirs(TEXDIR, exist_ok=True)
    out = {}
    for key, arr in (("d", np.repeat(d[..., None], 3, -1)),
                     ("r", np.repeat(r[..., None], 3, -1)),
                     ("n", nrm)):
        p = os.path.join(TEXDIR, NAMES[key])
        Image.fromarray((np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8)).save(
            p, quality=94, subsampling=0)
        out[key] = p
        print("WROTE %s  %dx%d  mean %.4f  sd %.4f" % (p, N, N, float(arr.mean()),
                                                       float(arr.std())))
    # the numbers the material's behaviour depends on, printed rather than assumed
    print("weave period %d texels · wear octaves 3/6/12/24 cells · diffuse mean %.3f"
          % (N // W, float(d.mean())))
    return out


# --------------------------------------------------------------- the wiring ----
def wire():
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    SAVE = "save" in argv
    DRY = "--dry" in argv
    SCALE = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else 1.9

    for k, n in NAMES.items():
        p = os.path.join(TEXDIR, n)
        if not os.path.exists(p):
            raise SystemExit("REFUSE: %s missing — run `python3 %s maps` first"
                             % (p, os.path.basename(__file__)))

    mat = bpy.data.materials["mat_qm_awning"]
    nt = mat.node_tree
    have = [n.name for n in nt.nodes if n.name.startswith("cv_")]
    if have and not DRY:
        print("removing %d existing cv_* node(s) — this is a replace, not a stack" % len(have))
        for n in list(nt.nodes):
            if n.name.startswith("cv_"):
                nt.nodes.remove(n)

    bsdf = nt.nodes["Principled BSDF"]
    vc = nt.nodes["Color Attribute"]
    assert vc.layer_name == "Col", "the vertex colour this multiplies is not Col"
    base0 = bsdf.inputs["Base Color"].links[0].from_node
    print("mat_qm_awning before: Base Color <- %s ; albedo default %s ; spec %.3f"
          % (base0.name, tuple(round(v, 4) for v in vc.outputs[0].default_value)
             if not vc.outputs[0].is_linked else "-",
             bsdf.inputs["Specular IOR Level"].default_value))
    if DRY:
        print("--dry: nothing wired")
        return

    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.name = "cv_texco"
    mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "cv_map"
    mp.inputs["Scale"].default_value = (SCALE, SCALE, SCALE)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def tex(key, cs, name):
        t = nt.nodes.new("ShaderNodeTexImage"); t.name = name
        img = bpy.data.images.get(NAMES[key])
        if img is None:
            img = bpy.data.images.load("//../textures/" + NAMES[key])
        t.image = img
        t.image.colorspace_settings.name = cs
        t.projection = 'BOX'          # an awning is a shallow tent, not a plane
        t.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    td = tex("d", "sRGB", "cv_diffuse")
    tr = tex("r", "Non-Color", "cv_rough")
    tnm = tex("n", "Non-Color", "cv_normal")

    mix = nt.nodes.new("ShaderNodeMix"); mix.name = "cv_mul"
    mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs["Factor"].default_value = 1.0
    # ShaderNodeMix carries one A/B pair PER data type and their indices move
    # between Blender versions — address them by name AND socket type, never by
    # ordinal.  (The first cut used 6/7, linked into the float pair, and the
    # assertion below is what caught it.)
    ain, bin_ = [i for i in mix.inputs if i.name == "A" and i.type == 'RGBA'][0], \
                [i for i in mix.inputs if i.name == "B" and i.type == 'RGBA'][0]
    aout = [o for o in mix.outputs if o.type == 'RGBA'][0]
    nt.links.new(vc.outputs["Color"], ain)
    nt.links.new(td.outputs["Color"], bin_)
    nt.links.new(aout, bsdf.inputs["Base Color"])

    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.name = "cv_nmap"
    nm.inputs["Strength"].default_value = 1.0
    nt.links.new(tnm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(tr.outputs["Color"], bsdf.inputs["Roughness"])

    # bpy RNA wrappers are recreated per access, so `is` between two handles on one
    # node is FALSE — compare names.  (This assertion fired on a correctly wired
    # graph, which is its own small lesson about asserting on identity in Blender.)
    print("   base <- %s · mix A <- %s · mix B <- %s · rough <- %s · normal <- %s"
          % ([l.from_node.name for l in bsdf.inputs["Base Color"].links],
             [l.from_node.name for l in ain.links], [l.from_node.name for l in bin_.links],
             [l.from_node.name for l in bsdf.inputs["Roughness"].links],
             [l.from_node.name for l in bsdf.inputs["Normal"].links]))
    assert bsdf.inputs["Base Color"].links[0].from_node.name == mix.name
    assert ain.links[0].from_node.name == vc.name, "the stripe columns were dropped"
    print("WIRED mat_qm_awning: Col x %s (BOX, scale %.2f) -> Base Color; "
          "%s -> Roughness; %s -> Normal"
          % (NAMES["d"], SCALE, NAMES["r"], NAMES["n"]))
    n_aw = [o.name for o in bpy.data.objects
            if o.type == 'MESH' and any(s.material and s.material.name == "mat_qm_awning"
                                        for s in o.material_slots)]
    print("   worn by %d meshes: %s" % (len(n_aw), ", ".join(sorted(n_aw))))
    if SAVE:
        bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
    else:
        print("not saved (pass `save`)")


if __name__ == "__main__":
    mode = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else (
        sys.argv[1] if len(sys.argv) > 1 else "")
    if mode == "maps":
        make_maps()
    elif mode == "wire":
        wire()
    else:
        raise SystemExit("modes: maps | wire")
