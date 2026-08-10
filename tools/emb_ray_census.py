"""emb_ray_census.py — WHAT OBJECT IS ACTUALLY AT THESE PIXELS, ASKED OF THE DRESSED
MASTER.  Emberbrook's counterpart to the Dellhollow ray census, in one Blender run.

    /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/emberbrook-dressed.blend \
        --python-exit-code 1 -P tools/emb_ray_census.py -- \
        --shot homerow --uv 0.892,0.248,0.998,0.438 --n 900

    …                --shot homerow --box 47.4,51.1,56.6,61.9,1.9,8.8      # a world box
    …                --shot homerow --uv … --json /tmp/out.json

WHY IT EXISTS.  `emb_plate_object` attributes a judge's bbox against `emb-cine/scene.glb`,
which is exported from `emberbrook-master.blend` — THE GRAY BLOCKOUT.  It says so, and it
reports a RESIDUAL for exactly this case: when the pixels are made by dressing, the
nearest massing sits a metre or more behind them and the residual is the answer, not the
object name.  Round 1's #1 residual for round 2 was `lm_watermill_body` at 1.16-1.41 m,
i.e. "the thing you are looking at is not in the collision bundle".  This asks the DRESSED
master instead, so the answer is an object and a MATERIAL.

WHAT IT MODELS, and both halves are scars this repo has already paid for:
  * objects with `hide_render` are not in the render and are not in the cast (a naive
    tally once attributed 57% of a Dellhollow frame to a hidden card);
  * a RENDER-ONLY VOLUME (material output with a Volume link and no Surface link) is not
    a surface — the ray passes through it and it is reported as an attenuator, never as
    a hit.  Emberbrook is not known to ship one; the classification is printed either way
    so that a future one cannot silently become "the object at this pixel".

The ray directions come from the SHIPPED bundle's own solved camera (`emb-cine/cine.json`,
Blender Z-up, sensor_fit VERTICAL so `fov` is angle_y) — the same construction
`plate_probe` and `emb_plate_object` use, so all three instruments are asking about the
same pixels.  When `depth.png` is available the tool also reports AGREEMENT: the distance
the cast travelled against the distance the plate's own depth says, per sample.  A
disagreement is the finding — it means the render saw something the depth pass did not
(or the plate is stale).

IT DOES NOT USE `scene.ray_cast`, ON PURPOSE.  That casts against the evaluated depsgraph,
and dressed Emberbrook carries **6.36 M scattered leaf/grass dupli instances** (CLAUDE.md,
"the 146x trap") — building one BVH over those to ask about a building wall is tens of
gigabytes on a shared machine.  Instead: every real mesh object whose bounding sphere the
ray corridor passes within is SHORTLISTED (printed with its count), and the cast is a
per-object `BVHTree.FromObject`.  **SO SCATTERED INSTANCES ARE NOT OCCLUDERS HERE**, which
is exactly what the agreement column is for: if the render put something in front that
this cast cannot see, the cast distance is LONGER than `depth.png`'s and the disagreement
is printed rather than hidden.  `--near` skips the cast entirely and just lists what is
inside a world box, with materials.
"""
import bpy, sys, os, json, math
from mathutils import Vector
from collections import Counter

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(f, d=None):
    return argv[argv.index(f) + 1] if f in argv else d


BUNDLE = arg("--bundle", os.path.join(ROOT, "public/assets/scenes/emb-cine"))
SHOT = arg("--shot", "homerow")
N = int(arg("--n", "900"))
JS = arg("--json")
CAMS = {c["id"]: c for c in json.load(open(os.path.join(BUNDLE, "cine.json")))["cameras"]}
C = CAMS[SHOT]

# ----------------------------------------------------------------- classify ---
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
vols, skip = set(), []
for o in sc.objects:
    if o.type != 'MESH':
        continue
    if o.hide_render:
        skip.append(o.name)
        continue
    for ms in o.material_slots:
        m = ms.material
        if not (m and m.use_nodes):
            continue
        out = next((n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out and out.inputs['Volume'].is_linked and not out.inputs['Surface'].is_linked:
            vols.add(o.name)
print("RENDER-ONLY VOLUME OBJECTS (marched through, never a hit): %s"
      % (", ".join(sorted(vols)) if vols else "none"))
print("NOT IN THE RENDER (hide_render): %d objects%s"
      % (len(skip), (": " + ", ".join(sorted(skip)[:10])) if skip else ""))

# -------------------------------------------------------------------- rays ---
pos = Vector(C["pos"]); aim = Vector(C["aim"])
f = (aim - pos).normalized()
up = Vector((0, 0, 1)) if abs(f.z) < 0.9999 else Vector((0, 1, 0))
r = f.cross(up).normalized()
u = r.cross(f)
ty = math.tan(math.radians(C["fov"]) / 2.0)
W, H = C["depth"]["width"], C["depth"]["height"]

# depth.png, for the agreement column (optional)
DEPTH = None
try:
    from PIL import Image
    import numpy as np
    dpi = Image.open(os.path.join(BUNDLE, "cameras", SHOT, "depth.png")).convert("RGB")
    dp = np.asarray(dpi).astype(np.float64)
    nn = dp[..., 0] * 65536 + dp[..., 1] * 256 + dp[..., 2]
    near, far = C["depth"]["near"], C["depth"]["far"]
    DEPTH = (near + (far - near) * nn / 16777215.0, nn >= 16777215 - 0.5)
    H, W = DEPTH[0].shape
except Exception as e:                                    # pragma: no cover
    print("depth.png unavailable (%s) — no agreement column" % e)

UV = arg("--uv")
BOX = arg("--box")
assert UV or BOX, "give --uv u0,v0,u1,v1 (a judge's bbox) or --box x0,x1,y0,y1,z0,z1"

# sample pixels on a regular lattice inside the uv box; a world box is filtered after
if UV:
    u0, v0, u1, v1 = [float(x) for x in UV.split(",")]
else:
    u0, v0, u1, v1 = 0.0, 0.0, 1.0, 1.0
bx = [float(x) for x in BOX.split(",")] if BOX else None
px0, px1 = int(u0 * W), max(int(u1 * W), int(u0 * W) + 1)
py0, py1 = int(v0 * H), max(int(v1 * H), int(v0 * H) + 1)
step = max(1, int(math.sqrt((px1 - px0) * (py1 - py0) / max(N, 1))))

# build the ray list first — the shortlist is derived from it
RAYS = []
for py in range(py0, py1, step):
    for px in range(px0, px1, step):
        X = (2.0 * ((px + 0.5) / W) - 1.0) * ty * (W / H)
        Y = (1.0 - 2.0 * ((py + 0.5) / H)) * ty
        dv = (f + X * r + Y * u).normalized()
        if bx and DEPTH is not None:
            if DEPTH[1][py, px]:
                continue
            P = pos + dv * DEPTH[0][py, px]
            if not (bx[0] <= P.x <= bx[1] and bx[2] <= P.y <= bx[3] and bx[4] <= P.z <= bx[5]):
                continue
        RAYS.append((px, py, dv))
n = len(RAYS)
assert n, ("no sample survived the filter — an instrument that finds nothing must prove "
           "it could have found something; widen --uv/--box")

# ------------------------------------------------------------- the shortlist ---
NEAR = "--near" in argv
MARGIN = float(arg("--margin", "0.5"))
cand = []
for o in sc.objects:
    if o.type != 'MESH' or o.hide_render or not o.data.polygons:
        continue
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    ctr = sum(ws, Vector()) / 8.0
    rad = max((w - ctr).length for w in ws) + MARGIN
    if bx and NEAR:
        lo = Vector((min(w.x for w in ws), min(w.y for w in ws), min(w.z for w in ws)))
        hi = Vector((max(w.x for w in ws), max(w.y for w in ws), max(w.z for w in ws)))
        if hi.x < bx[0] or lo.x > bx[1] or hi.y < bx[2] or lo.y > bx[3] \
           or hi.z < bx[4] or lo.z > bx[5]:
            continue
        cand.append((o, ctr, rad))
        continue
    v = ctr - pos
    for _px, _py, dv in RAYS:                       # bounding sphere vs the ray corridor
        t = v.dot(dv)
        if t < -rad:
            continue
        if (v - dv * max(t, 0.0)).length <= rad:
            cand.append((o, ctr, rad))
            break
print("SHORTLIST: %d of %d render meshes lie on the ray corridor (margin %.2f m)"
      % (len(cand), sum(1 for o in sc.objects if o.type == 'MESH' and not o.hide_render), MARGIN))

if NEAR:
    print("\n== objects inside world box %s" % BOX)
    for o, ctr, rad in sorted(cand, key=lambda c: -c[0].dimensions.length):
        mm = ",".join(sorted({(ms.material.name if ms.material else "-")
                              for ms in o.material_slots})) or "-"
        print("   %-38s dim %6.2f x %6.2f x %6.2f  tris %6d  mat %s"
              % (o.name, o.dimensions.x, o.dimensions.y, o.dimensions.z,
                 len(o.data.loop_triangles) or len(o.data.polygons), mm))
    sys.exit(0)

from mathutils.bvhtree import BVHTree
TREES = []
for o, ctr, rad in cand:
    try:
        TREES.append((o, BVHTree.FromObject(o, dg)))
    except Exception as e:
        print("   ! no BVH for %s (%s)" % (o.name, e))
print("built %d object BVHs" % len(TREES))

hits, mats, dists, disag = Counter(), Counter(), {}, []
miss = 0
for px, py, dv in RAYS:
    best = None
    for o, tree in TREES:
        mw = o.matrix_world
        mi = mw.inverted()
        lo = mi @ pos
        ld = (mi.to_3x3() @ dv)
        sc_ = ld.length or 1.0
        loc, nor, idx, d = tree.ray_cast(lo, ld.normalized())
        if loc is None:
            continue
        wd = ((mw @ loc) - pos).length
        if best is None or wd < best[0]:
            best = (wd, o, idx)
    if best is None:
        miss += 1
        continue
    wd, o, idx = best
    name = o.name
    try:
        mat = o.material_slots[o.data.polygons[idx].material_index].material.name
    except Exception:
        mat = "-"
    hits[name] += 1
    mats["%s | %s" % (name, mat)] += 1
    dists.setdefault(name, []).append(wd)
    if DEPTH is not None and not DEPTH[1][py, px]:
        disag.append(wd - float(DEPTH[0][py, px]))

print("\n== %s  %s  %d rays" % (SHOT, UV and ("uv " + UV) or ("box " + BOX), n))
print("FIRST OPAQUE HIT:")
for nm, c in hits.most_common(14):
    dd = dists[nm]
    print("   %-34s %5d (%5.1f%%)  dist %6.2f..%6.2f m"
          % (nm, c, 100.0 * c / n, min(dd), max(dd)))
if miss:
    print("   %-34s %5d (%5.1f%%)" % ("<no hit / world background>", miss, 100.0 * miss / n))
print("BY MATERIAL:")
for k, c in mats.most_common(12):
    print("   %-58s %5d (%5.1f%%)" % (k, c, 100.0 * c / n))
if disag:
    disag.sort()
    print("AGREEMENT cast vs plate depth.png:  p05 %+.3f  p50 %+.3f  p95 %+.3f m"
          % (disag[int(.05 * (len(disag) - 1))], disag[len(disag) // 2],
             disag[int(.95 * (len(disag) - 1))]))
if JS:
    json.dump({"shot": SHOT, "uv": UV, "box": BOX, "rays": n,
               "hits": hits.most_common(), "materials": mats.most_common(),
               "miss": miss}, open(JS, "w"), indent=1)
    print("wrote " + JS)
