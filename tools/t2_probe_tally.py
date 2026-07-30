"""t2_probe_tally.py — READ ONLY per-camera screen ray tally + water/bed probe.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_tally.py -- --out /tmp/tally.json [--gw 224] [--cams a,b] [--nowater]

TRANCHE-2 GATE.  This is the measurement layer behind docs/plans/cliff-completion.md,
docs/plans/pops-of-color.md and docs/plans/water-transparency.md.  Every screen-%,
px/edge and depth number in those three documents came out of this file and its
siblings, so it is promoted out of a scratchpad into tools/ where it can be re-run
against the master AFTER a build and the same numbers compared.

Two passes in one session:
  1. a 224x128 ray grid over every solved camera, recording per pixel the first-hit
     OBJECT and its distance, plus each object's mean edge length — the resolution
     proxy  px_per_edge = edge_m * (H/2) / (d_mean * tan(fov/2))  at the shipped
     2688x1536.  Under ~80 px an edge reads as curvature; over ~150 px as a facet.
  2. a 0.75 m down-ray STACK over every water sheet's footprint: is there water
     here, is there a bed under it, and how deep.  That is the bathymetry probe
     that found riverbed to be an 8-vertex flat slab.

Camera construction MATCHES cine_bake.py::build_cam (sensor_fit VERTICAL, fov is
the vertical angle), so the ray grid and the shipped plate agree.
Read the JSON with tools/t2_probe_report.py.

CPU ray-casts only: safe to run while a bake holds the GPU.  NEVER saves.
"""
import bpy, os, sys, json, math, time, base64, struct
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
OUT = opt("--out", "/tmp/tally.json")
GW = int(opt("--gw", "224"))
ONLY = [s for s in opt("--cams", "").split(",") if s]
DO_WATER = "--nowater" not in argv

S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
D = S["defaults"]
ASPECT = D["aspect"]
GH = int(round(GW / ASPECT))
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# ---- mean edge length per mesh (resolution proxy), cached -------------------
_edge = {}
def mean_edge(ob):
    k = ob.data.name
    if k in _edge: return _edge[k]
    me = ob.data
    s = ob.matrix_world.to_scale()
    ms = (abs(s.x) + abs(s.y) + abs(s.z)) / 3.0
    n = len(me.edges)
    if n == 0:
        _edge[k] = (0.0, 0, 0); return _edge[k]
    tot = 0.0
    vs = me.vertices
    step = 1 if n <= 4000 else max(1, n // 4000)
    cnt = 0
    for i in range(0, n, step):
        e = me.edges[i]
        tot += (vs[e.vertices[0]].co - vs[e.vertices[1]].co).length
        cnt += 1
    _edge[k] = (tot / cnt * ms, len(me.vertices), len(me.polygons))
    return _edge[k]

def cam_basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    U = Vector((0, 0, 1))
    r = f.cross(U)
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f).normalized()
    if u.z < 0:
        r = -r
        u = r.cross(f).normalized()
    return f, r, u

results = {}
t_all = time.time()
for c in S["cameras"]:
    cid = c["id"]
    if ONLY and cid not in ONLY: continue
    pos = Vector(c["pos"])
    f, r, u = cam_basis(c["pos"], c["aim"])
    ty = math.tan(math.radians(c["fov"]) / 2)   # vertical half-angle (sensor_fit VERTICAL)
    t0 = time.time()
    names = []          # per-camera object table
    idx = {}
    objid = bytearray(GW * GH * 2)
    dist_a = bytearray(GW * GH * 2)
    per = {}            # name -> [px, sum_dist, min_dist, max_dist]
    miss = 0
    missdirs = []
    for py in range(GH):
        sy = (1.0 - 2.0 * (py + 0.5) / GH) * ty            # top row = +u
        for px in range(GW):
            sx = (2.0 * (px + 0.5) / GW - 1.0) * ty * ASPECT
            d = (f + r * sx + u * sy).normalized()
            hit, loc, nrm, fidx, ob, mw = sc.ray_cast(dg, pos, d, distance=1400.0)
            o = py * GW + px
            if not hit:
                miss += 1
                missdirs.append((px, py, round(d.x, 4), round(d.y, 4), round(d.z, 4)))
                struct.pack_into("<H", objid, o * 2, 0xFFFF)
                struct.pack_into("<H", dist_a, o * 2, 0xFFFF)
                continue
            nm = ob.name
            i = idx.get(nm)
            if i is None:
                i = len(names); idx[nm] = i; names.append(nm)
                me_len, nv, npo = mean_edge(ob)
                mats = [ms.material.name if ms.material else None for ms in ob.material_slots]
                per[nm] = {"i": i, "px": 0, "sd": 0.0, "dmin": 1e9, "dmax": 0.0,
                           "edge": round(me_len, 4), "verts": nv, "polys": npo,
                           "mats": mats,
                           "loc": [round(v, 2) for v in ob.matrix_world.translation],
                           "hit0": [round(v, 2) for v in loc]}
            dd = (loc - pos).length
            p = per[nm]
            p["px"] += 1; p["sd"] += dd
            if dd < p["dmin"]: p["dmin"] = dd
            if dd > p["dmax"]: p["dmax"] = dd
            struct.pack_into("<H", objid, o * 2, i)
            struct.pack_into("<H", dist_a, o * 2, min(65534, int(dd * 100)))
    for nm, p in per.items():
        p["dmean"] = round(p["sd"] / p["px"], 2)
        p["dmin"] = round(p["dmin"], 2); p["dmax"] = round(p["dmax"], 2)
        del p["sd"]
    results[cid] = {"gw": GW, "gh": GH, "pos": c["pos"], "aim": c["aim"], "fov": c["fov"],
                    "miss": miss, "total": GW * GH,
                    "objects": per, "names": names,
                    "missdirs": missdirs if len(missdirs) < 40000 else missdirs[:40000],
                    "objid": base64.b64encode(bytes(objid)).decode(),
                    "dist": base64.b64encode(bytes(dist_a)).decode()}
    print("TALLY %-15s miss %6.2f%%  objs %4d  %.0fs" % (cid, 100.0 * miss / (GW * GH), len(names), time.time() - t0))
    sys.stdout.flush()

# ============================ WATER / BED PROBE ==============================
water = {}
if DO_WATER:
    wobs = []
    for o in sc.objects:
        if o.type != 'MESH': continue
        mn = [ms.material.name for ms in o.material_slots if ms.material]
        if any("water" in m.lower() for m in mn) or "water" in o.name.lower():
            wobs.append(o)
    wnames = set(o.name for o in wobs)
    print("WATER OBJECTS:", [o.name for o in wobs])

    def down_stack(x, y, ztop, maxhits=8):
        """all hits going straight down from ztop, in order"""
        out = []
        p = Vector((x, y, ztop))
        dvec = Vector((0, 0, -1))
        for _ in range(maxhits):
            hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, p, dvec, distance=400.0)
            if not hit: break
            out.append((ob.name, round(loc.z, 3)))
            p = loc + dvec * 0.002
        return out

    for o in wobs:
        bb = [o.matrix_world @ Vector(cc) for cc in o.bound_box]
        x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
        y0, y1 = min(v.y for v in bb), max(v.y for v in bb)
        wz = max(v.z for v in bb)
        step = 0.75
        nx = max(2, int((x1 - x0) / step) + 1)
        ny = max(2, int((y1 - y0) / step) + 1)
        samples = []
        for iy in range(ny):
            yy = y0 + (y1 - y0) * (iy / max(1, ny - 1))
            for ix in range(nx):
                xx = x0 + (x1 - x0) * (ix / max(1, nx - 1))
                st = down_stack(xx, yy, wz + 6.0)
                # first water hit, first non-water hit below it
                wi = next((k for k, (n, z) in enumerate(st) if n in wnames), None)
                if wi is None:
                    # not over this water sheet; is there land here?
                    land = st[0][1] if st else None
                    samples.append({"x": round(xx, 2), "y": round(yy, 2), "w": 0,
                                    "land": land, "bed": None, "stack": [s[0] for s in st[:3]]})
                    continue
                surf = st[wi][1]
                bed = next(((n, z) for (n, z) in st[wi + 1:] if n not in wnames), None)
                above = st[0] if wi > 0 else None
                samples.append({"x": round(xx, 2), "y": round(yy, 2), "w": 1,
                                "surf": surf,
                                "bed": bed[1] if bed else None,
                                "bedobj": bed[0] if bed else None,
                                "above": above[0] if above else None,
                                "depth": round(surf - bed[1], 3) if bed else None})
        water[o.name] = {"bbox": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                         "surf_z": round(wz, 3), "nx": nx, "ny": ny, "step": step,
                         "mats": [ms.material.name for ms in o.material_slots if ms.material],
                         "verts": len(o.data.vertices), "polys": len(o.data.polygons),
                         "samples": samples}
        nb = sum(1 for s in samples if s.get("w") and s.get("bed") is None)
        nw = sum(1 for s in samples if s.get("w"))
        print("WATER %-22s surf_z %7.2f  %4d water samples, %4d with NO BED (%.0f%%)"
              % (o.name, wz, nw, nb, 100.0 * nb / max(1, nw)))

json.dump({"cameras": results, "water": water}, open(OUT, "w"))
print("WROTE", OUT, "%.0fs total" % (time.time() - t_all))
