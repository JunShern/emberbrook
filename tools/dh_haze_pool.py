"""dh_haze_pool.py — THE ONE FAR SURFACE IN THIS TOWN WITH NO AERIAL PERSPECTIVE IS THE
WATER.  Dellhollow graphics round 7.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_haze_pool.py -- census
  Blender -b … -P tools/dh_haze_pool.py -- reflect --shots crossing,lockfive,weave
  Blender -b … -P tools/dh_haze_pool.py -- [--dens D] [--z1 Z] [--x0 X] [save|restore]

  SHIPPED:  `--dens <D> save`  (see the sweep in DAYLOG round 7)

WHAT ROUND 6 HANDED OVER, AND WHAT MEASUREMENT SAYS ABOUT IT.
Round 6 named two items.  ONE OF THEM IS REFUTED AT THE JUDGE'S OWN BOX.

  (A) "THE FAR FIELD IS GREYBOX" — the two plates it named do not show one.  `gate`'s
      surviving frame-edge box (u 0.00..0.47, v 0.00..0.40, 18.78% of frame) is 83.2%
      `cliff_east_closure | mat_rock_gorgewall` at 168 m — a TEXTURED rock wearing round
      4's own named veining residual, not a placeholder.  `shelf-east`'s round-6 box
      moved to u 0.00..0.26, v 0.50..0.99, and that box is 42.1% `shelf_cliffface` +
      45.6% `shelf_home_b/_c` roof shingle AT 8..14 m — NEAR-FIELD HOUSING.  The judge's
      WORDS there say "background rock and sky geometries ... at upper margins" and its
      BOX is the bottom-left corner; `quality:frame-edge-world` is the one row `aimOf`
      is deliberately not allowed to gate, so nothing caught it.
      The greybox materials are real — `mat_rock_far` / `mat_silhouette` own 5.52% of
      shelf-east, 2.99% of north-landing and 1.81% of waterfront, at L p50 51.7..90.1
      with 5x5 sd 0.32..2.55 — but NO LIVE JUDGE FINDING POINTS AT THEM: north-landing
      and waterfront both cleared to CONVINCING in round 6, and shelf-east's box is
      somewhere else entirely.  Named for a later round on the measurement, not on a
      verdict.

  (B) "THE FRAME-EDGE QUESTION HAS MOVED ONTO `m_water`" — CONFIRMED, and BIGGER than
      the two boxes that carry it.  Object census of the judge's own boxes: lockfive
      64.1% `water_pool-downstream | m_water` at 69 m, weave 54.9% at 90 m.  But the
      same subject — the downstream pool seen past 55 m — owns 12.96% OF CROSSING at
      L p50 18.2, 5x5 sd 0.47, 65.5% crushed, on a plate whose own `quality:water-read`
      row is CONVINCING.  The near water and the far water are the same sheet.

THE MECHANISM, MEASURED, AND IT IS NOT THE SHADER.  `m_water` HAS the ratified
depth->alpha bake (`t2_depth_attr` -> `t2_depth_ramp` -> Alpha on both lobes) and it is
intact.  What the far water is doing is REFLECTING: Roughness 0.09 is a near-mirror and
at grazing incidence Fresnel is ~1, so the sheet reads as whatever is in its mirror
direction.  A reflected-ray census over the sheet says exactly what changes with
distance:

    crossing  <30 m   reflects <bg> (the world sky) 94%      plate L 204
    crossing  30-60 m reflects cliff_east_closure 53%        plate L  97
    crossing  60-100m reflects cliff_east_closure 65%        plate L  18
    lockfive  60-100m reflects cliff_east_closure 100%       plate L  24
    weave     60-100m reflects cliff_east_closure 77%        plate L  16

THE NEAR WATER MIRRORS THE BRIGHT SKY AND THE FAR WATER MIRRORS THE DARKEST WALL IN
TOWN, ACROSS 60 m OF ONE SHEET.  That is round 4's inverted depth cue again, arriving on
the water by reflection — and it is why the judge's word for it is "void".

THE MATERIAL LEVER IS REFUSED WITH NUMBERS (draft A/B, 1008x576/28 spp, far-water mask
>= 55 m derived from the ray census, four plates).  Roughening the water to widen that
mirror lobe DOES NOTHING TO THE DARK AND BLOWS OUT THE GLINT:

    variant            crossing p05/p50/p95      lockfive p05/p50 crushed%
    shipped  r 0.09    10.0 / 18.2 / 113.9       18.6 / 24.9   34.1
    r 0.22             10.3 / 18.1 / 140.4       19.4 / 23.7   50.5
    r 0.35             10.4 / 17.6 / 176.2       18.1 / 21.1   78.0
    bump 0.26 -> 0.60  10.4 / 18.7 / 190.8       19.6 / 24.9   35.6

  The median does not move at all and the p95 climbs 68% while lockfive's CRUSHED
  fraction DOUBLES: a wider lobe averages in more dark wall exactly where it is already
  dark and more sun exactly where it is already bright.  IT INCREASES THE CONTRAST
  BETWEEN THE GLINT AND THE VOID, which is the opposite of the complaint.  Do not ship a
  roughness change here.

SO THE CLASS IS ATMOSPHERE, AND THE MEASUREMENT THAT NAMES THE LEVER IS ONE LINE.
Optical depth collected by the camera rays that land on far water, against the optical
depth collected by the rays that land on the wall BEHIND it:

    far water   crossing 0.042 · lockfive 0.075 · weave 0.055 · gate 0.016
    far wall    0.612 (fx_haze_east at its full crossing)

THE WATER IS THE ONE FAR SURFACE IN DELLHOLLOW WITH NO AERIAL PERSPECTIVE, and the
reason is structural: every haze card in this town is a VERTICAL CURTAIN ACROSS THE
GORGE at some x (`fx_haze_east` x 124..130, `fx_haze_mid` -47..-23, `fx_haze_far`
-74..-50, `fx_haze_rim` -122..-78) or a thin skin along the south bank (`fx_haze_south`
y -2.4..0.3).  A camera ray to the far water runs ALONG the gorge floor and reaches its
target before any curtain, while the ray to the wall 40 m behind it crosses one.

WHY NOT JUST GROW `fx_haze_east` WEST: ROUND 6 ALREADY REFUSED THAT WITH NUMBERS
(`dh_haze_medium --x1`), on two independent grounds — a medium moved against a wall
moves into its shadow, and `north-landing`'s eye sits 2.88 m in front of the card's near
face, so growing it toward the town swallows a camera.  This card is a DIFFERENT SHAPE
IN A DIFFERENT PLACE: a LOW SLAB lying over the downstream pool, under every camera that
sees it, and its whole design problem is `north-landing` — which looks straight down the
gorge from x = 121 and would have its entire frame milked by a slab that reached its
eye.  Hence the two bounds that are not free parameters:

  * the slab's TOP (`--z1`, default -0.5) is BELOW north-landing's sight line for the
    first 30 m of its view, and
  * the slab's FAR FACE is `fx_haze_east`'s NEAR face (x = 124.0) — abutting, never
    overlapping, so no ray is ever taxed twice.

`census` prints, with no bake: every camera's frame share of the new card, the median
tau it collects, the split of those rays into WATER (the intended subject) and SPILL
(anything else), and the camera-inside-a-card margin.  Run it before every level change.
"""
import bpy, os, sys, json, math
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/dh_haze_pool.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv and not argv[0].startswith("--") else ""
SAVE = "save" in argv
RESTORE = "restore" in argv
NAME = "fx_haze_pool"
MAT = "mat_haze_pool"
WATER = {"water_pool-downstream", "water_pool-mid", "water_pool-upstream", "lf_lock_water"}


def opt(f, d):
    return float(argv[argv.index(f) + 1]) if f in argv else d


X0 = opt("--x0", 88.0)
X1 = opt("--x1", 124.0)       # == fx_haze_east's near face: abut, never overlap
Y0 = opt("--y0", 8.0)
Y1 = opt("--y1", 86.0)
Z0 = opt("--z0", -9.0)
Z1 = opt("--z1", -0.5)
DENS = opt("--dens", 0.0)
ANISO = opt("--aniso", -0.25)  # the round-6 constant: these cameras look WITH the sun


def build(dens):
    """Create or update the card.  Idempotent by REBUILDING the box from the bounds it
    is given and printing what it found — never by trusting what is there."""
    mat = bpy.data.materials.get(MAT)
    if mat is None:
        mat = bpy.data.materials.new(MAT)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        vs = nt.nodes.new('ShaderNodeVolumeScatter')
        vs.inputs['Color'].default_value = (0.48, 0.50, 0.60, 1.0)
        nt.links.new(vs.outputs['Volume'], out.inputs['Volume'])
        print("CREATED material %s" % MAT)
    vs = [n for n in mat.node_tree.nodes if n.type == 'VOLUME_SCATTER'][0]
    old_d = float(vs.inputs['Density'].default_value)
    old_a = float(vs.inputs['Anisotropy'].default_value)
    vs.inputs['Density'].default_value = dens
    vs.inputs['Anisotropy'].default_value = ANISO
    ob = bpy.data.objects.get(NAME)
    if ob is None:
        me = bpy.data.meshes.new(NAME)
        verts = [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0),
                 (X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new(NAME, me)
        ob.data.materials.append(mat)
        bpy.data.collections["CONTEXT"].objects.link(ob)
        print("CREATED object %s" % NAME)
    else:
        for v, p in zip(ob.data.vertices,
                        [(X0, Y0, Z0), (X1, Y0, Z0), (X1, Y1, Z0), (X0, Y1, Z0),
                         (X0, Y0, Z1), (X1, Y0, Z1), (X1, Y1, Z1), (X0, Y1, Z1)]):
            v.co = p
        ob.data.update()
    # THE FAMILY'S OWN FLAGS, ASSERTED NOT ASSUMED (round 4 gate 2: a card that casts a
    # shadow stops being atmosphere).
    ob.visible_shadow = False
    ob.visible_camera = ob.visible_diffuse = ob.visible_glossy = True
    ob.visible_transmission = ob.visible_volume_scatter = True
    print("CARD %s  x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  density %.6f -> %.6f  aniso %.2f -> %.2f"
          % (NAME, X0, X1, Y0, Y1, Z0, Z1, old_d, dens, old_a, ANISO))
    return ob, mat


def gates(ob):
    mat = ob.material_slots[0].material
    users = [o.name for o in bpy.data.objects
             if o.type == 'MESH' and any(s.material is mat for s in o.material_slots)]
    assert users == [NAME], "%s is worn by %s" % (mat.name, users)
    assert ob.visible_shadow is False
    # GATE 3 (round 6): NO SOLVED CAMERA MAY LIE INSIDE ANY CARD.  Distance to the BOX.
    cams = json.load(open(os.path.join(ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]
    lo, hi = Vector((X0, Y0, Z0)), Vector((X1, Y1, Z1))
    worst = None
    for c in cams:
        p = Vector(c["pos"])
        d = Vector((max(lo[i] - p[i], 0.0, p[i] - hi[i]) for i in range(3))).length
        if worst is None or d < worst[1]:
            worst = (c["id"], d)
    assert worst[1] > 0.0, "camera %s is INSIDE %s" % (worst[0], NAME)
    print("GATE camera-inside-card: nearest eye is %s at %.2f m outside the box" % worst)


def census():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import dh_pixel_census as C
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = C._classify()
    assert NAME in vol, "%s is not a render-only volume card" % NAME
    cams = {c["id"]: c for c in json.load(open(os.path.join(
        ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]}
    grid = int(opt("--grid", 120))
    print("%-14s %8s %8s %8s %8s %9s | %s" %
          ("shot", "card%", "water%", "spill%", "tau med", "wash%max", "spill objects (top 3)"))
    from collections import Counter
    for sid in cams:
        c = cams[sid]
        p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
        ty = math.tan(math.radians(c["fov"]) / 2.0)
        W = grid; H = int(grid * 9 / 16); n = W * H
        ncard = nw = nsp = 0; taus = []; spill = Counter()
        for iy in range(H):
            Y = (1.0 - 2.0 * ((iy + 0.5) / H)) * ty
            for ix in range(W):
                X = (2.0 * ((ix + 0.5) / W) - 1.0) * ty * (W / H)
                dv = (f + X * r + Y * u).normalized()
                nm, mt, dist, tt, _ = C._march(sc, dg, p, dv, vol, skip)
                if NAME not in tt:
                    continue
                ncard += 1
                if tt[NAME]:
                    taus.append(tt[NAME])
                if nm in WATER:
                    nw += 1
                else:
                    nsp += 1; spill[(nm or "<bg>")] += 1
        taus.sort()
        print("%-14s %8.2f %8.2f %8.2f %8.4f %9.2f | %s" %
              (sid, 100.0 * ncard / n, 100.0 * nw / n, 100.0 * nsp / n,
               taus[len(taus) // 2] if taus else 0.0,
               100 * (1 - math.exp(-taus[-1])) if taus else 0.0,
               ", ".join("%s %d" % (k, v) for k, v in spill.most_common(3))))


def reflect():
    """THE CENSUS THAT NAMED THE MECHANISM.  For every camera ray that lands on a water
    sheet, mirror the view direction about the sheet's own up normal and march again:
    the object that comes back IS what the pixel is showing, because Roughness 0.09 at
    grazing incidence is a mirror.  Reported per distance band, with the sun visibility
    of the hit point, so "the far water is dark" can be separated from "the far water is
    unlit" — it is NOT unlit (81-96% of it sees `KEY_gorgewall`)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import dh_pixel_census as C
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = C._classify()
    suns = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN'
            and not o.hide_render and o.name in sc.objects]
    cams = {c["id"]: c for c in json.load(open(os.path.join(
        ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]}
    grid = int(opt("--grid", 120))
    shots = [s for s in (argv[argv.index("--shots") + 1].split(",")
             if "--shots" in argv else list(cams))]
    UP = Vector((0, 0, 1))
    for sid in shots:
        c = cams[sid]
        p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
        r = f.cross(UP).normalized(); u = r.cross(f)
        ty = math.tan(math.radians(c["fov"]) / 2.0)
        W = grid; H = int(grid * 9 / 16)
        bands = {}
        for iy in range(H):
            Y = (1.0 - 2.0 * ((iy + 0.5) / H)) * ty
            for ix in range(W):
                X = (2.0 * ((ix + 0.5) / W) - 1.0) * ty * (W / H)
                dv = (f + X * r + Y * u).normalized()
                nm, mt, dist, tt, _ = C._march(sc, dg, p, dv, vol, skip)
                if nm not in WATER:
                    continue
                hit = p + dv * dist
                b = 0 if dist < 30 else (1 if dist < 60 else (2 if dist < 100 else 3))
                st = bands.setdefault(b, {"n": 0, "lit": 0, "refl": {}, "tau": 0.0})
                st["n"] += 1
                st["tau"] += sum(v for v in tt.values() if v)
                for s_ in suns:
                    sd = -(s_.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()
                    ok, _, _, _, sob, _ = sc.ray_cast(dg, hit + sd * 0.02, sd)
                    if not ok or (sob and sob.name in vol):
                        st["lit"] += 1
                    break
                rd = (dv - 2.0 * dv.dot(UP) * UP).normalized()
                rn, _, _, _, _ = C._march(sc, dg, hit + rd * 0.02, rd, vol, skip)
                k = rn or "<sky bg>"
                st["refl"][k] = st["refl"].get(k, 0) + 1
        print("--- %s" % sid)
        for b in sorted(bands):
            st = bands[b]
            top = sorted(st["refl"].items(), key=lambda kv: -kv[1])[:3]
            print("   %-8s n=%-5d sunlit %5.1f%%  tau %.4f  reflects: %s"
                  % (["<30m", "30-60m", "60-100m", ">100m"][b], st["n"],
                     100.0 * st["lit"] / st["n"], st["tau"] / st["n"],
                     ", ".join("%s %.0f%%" % (k, 100.0 * v / st["n"]) for k, v in top)))


if RESTORE:
    ob = bpy.data.objects.get(NAME)
    if ob is not None:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    m = bpy.data.materials.get(MAT)
    if m is not None:
        bpy.data.materials.remove(m)
    print("RESTORED: %s and %s removed" % (NAME, MAT))
else:
    ob, mat = build(DENS)
    gates(ob)
    if MODE == "census":
        census()
    elif MODE == "reflect":
        reflect()

if SAVE:
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    json.dump({"card": NAME, "material": MAT,
               "bounds": [X0, X1, Y0, Y1, Z0, Z1], "density": DENS, "aniso": ANISO},
              open(MANIFEST, "w"), indent=1)
    bpy.ops.wm.save_mainfile()
    print("SAVED master + manifest %s" % MANIFEST)
