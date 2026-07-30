"""t2_probe_chroma.py — READ ONLY.  Per-pixel MATERIAL tally (first opaque hit).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_chroma.py -- --out /tmp/chroma.json [--gw 224]

THE COLOUR-BUDGET GATE for docs/plans/pops-of-color.md.  Same ray grid as
t2_probe_leak.py, but it records the hit MATERIAL rather than the hit object, so
"chromatic pop" can be defined narrowly and measured: the fraction of a frame
whose hit material is a painted panel, cloth, awning, flag or produce.  Timber,
roofs, rock and deck planking are excluded on purpose — a warm brown plank is the
thing being broken up, not an instance of breaking it up.  (A looser filter that
counts any saturated material returns 12-53% per frame and just re-measures the
timber.)  The accent material set lives in tools/t2_probe_report.py.

ACCEPTANCE (pops-of-color.md gate 4): every camera in [5%, 11%] after the build.
Before: town mean 3.07%, six eastern cameras at 0.00-0.17%.

Also counts leak-ray directions (up / level / DOWN) per camera, which is how a
hole is told from legitimate sky: a downward ray that hits nothing in a valley
town is unambiguously a hole.

CPU ray-casts only.  NEVER saves.
"""
import bpy, os, sys, json, math, time, collections
from mathutils import Vector
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d): return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
OUT = opt("--out", "/tmp/tally3.json"); GW = int(opt("--gw", "224"))
S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
ASPECT = S["defaults"]["aspect"]; GH = int(round(GW / ASPECT))
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()

FXMAT = set()
for m in bpy.data.materials:
    if not m.use_nodes: continue
    out = next((n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out and out.inputs['Volume'].is_linked and not out.inputs['Surface'].is_linked:
        FXMAT.add(m.name)
SKIP = set(o.name for o in sc.objects if o.type == 'MESH'
           and [s.material.name for s in o.material_slots if s.material]
           and all((s.material.name in FXMAT) for s in o.material_slots if s.material))

def basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    r = f.cross(Vector((0, 0, 1)))
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize(); u = r.cross(f).normalized()
    if u.z < 0: r = -r; u = r.cross(f).normalized()
    return f, r, u

res = {}
for c in S["cameras"]:
    cid = c["id"]; pos = Vector(c["pos"]); f, r, u = basis(c["pos"], c["aim"])
    ty = math.tan(math.radians(c["fov"]) / 2); t0 = time.time()
    mc = collections.Counter(); pairs = collections.Counter(); miss = 0
    updown = collections.Counter()
    for py in range(GH):
        sy = (1.0 - 2.0 * (py + 0.5) / GH) * ty
        for px in range(GW):
            sx = (2.0 * (px + 0.5) / GW - 1.0) * ty * ASPECT
            d = (f + r * sx + u * sy).normalized()
            p = Vector(pos); got = None
            for _ in range(12):
                hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, p, d, distance=1400.0)
                if not hit: break
                if ob.name in SKIP: p = loc + d * 0.01; continue
                got = (ob, fi); break
            if got is None:
                miss += 1
                updown["up" if d.z > 0.02 else ("level" if d.z > -0.02 else "DOWN")] += 1
                mc["<SKY>"] += 1; continue
            ob, fi = got
            me = ob.evaluated_get(dg).data
            try:
                mi = me.polygons[fi].material_index
                mn = ob.material_slots[mi].material.name if mi < len(ob.material_slots) and ob.material_slots[mi].material else "<none>"
            except Exception:
                mn = "<err>"
            mc[mn] += 1; pairs[(ob.name, mn)] += 1
    res[cid] = {"gw": GW, "gh": GH, "total": GW * GH, "miss": miss,
                "missdir": dict(updown),
                "mats": dict(mc),
                "pairs": {"%s|%s" % k: v for k, v in pairs.items() if v >= 3}}
    print("MAT %-15s miss %5.2f%%  %s  %.0fs" % (cid, 100.0 * miss / (GW * GH), dict(updown), time.time() - t0))
    sys.stdout.flush()
json.dump(res, open(OUT, "w"))
print("WROTE", OUT)
