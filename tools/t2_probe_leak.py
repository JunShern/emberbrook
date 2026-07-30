"""t2_probe_leak.py — READ ONLY.  THE SKY-LEAK GATE for docs/plans/cliff-completion.md.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_leak.py -- --out /tmp/leak.json [--gw 224] [--cams a,b]

Opaque-only screen tally: FX cards whose material is volume-only (mat_haze_*,
mat_spray, mat_smoke) or a bare Transparent BSDF are SKIPPED, so a pixel that
really shows the world background counts as a LEAK.  That distinction IS the
audit — without it the haze cards paper over every hole and every number is
wrong.  It is how the investigation established that eight of the ten cameras the
user called "missing wall" leak 0.00%, and that the grey was cliff_town: a
placeholder, not a hole.

ACCEPTANCE (cliff-completion.md gate 5): sky-leak < 0.5% on EVERY camera.
Before the build: lockfive 19.96%, cottage-steps 16.26%, boatyard 0.36% (real sky
above the rim, 100% upward rays — legitimate), shelf-east 0.08%, the other 13 zero.

Also emits, per visible object, the resolution-proxy inputs (mean edge length,
verts, polys, d_mean) for gate 6: no visible surface over 250 px/edge above 1%
screen area.  `missrows` carries every leak ray's screen cell and direction —
that is what let the closure plane at x = 140 be solved exactly (10,384/10,384).

CPU ray-casts only.  NEVER saves.
"""
import bpy, os, sys, json, math, time, base64, struct
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
OUT = opt("--out", "/tmp/tally2.json")
GW = int(opt("--gw", "224"))
ONLY = [s for s in opt("--cams", "").split(",") if s]

S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
D = S["defaults"]; ASPECT = D["aspect"]; GH = int(round(GW / ASPECT))
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# ---- classify every material: does it write opaque colour to the frame? -------
matinfo = {}
for m in bpy.data.materials:
    if not m.use_nodes: continue
    kinds = set(n.type for n in m.node_tree.nodes)
    vol = False
    out = next((n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    surf_linked = bool(out and out.inputs['Surface'].is_linked)
    vol_linked = bool(out and out.inputs['Volume'].is_linked)
    matinfo[m.name] = {"kinds": sorted(kinds), "surface": surf_linked, "volume": vol_linked,
                       "blend": getattr(m, "blend_method", None)}

# a mesh is TRANSPARENT-FX if every slot is volume-only / no surface / a known haze mat
FXMAT = set()
for n, mi in matinfo.items():
    if mi["volume"] and not mi["surface"]: FXMAT.add(n)
    if 'BSDF_TRANSPARENT' in mi["kinds"] and not any(k.startswith('BSDF_') and k not in
        ('BSDF_TRANSPARENT',) for k in mi["kinds"]): FXMAT.add(n)
print("VOLUME/TRANSPARENT-ONLY MATERIALS:", sorted(FXMAT))

SKIP = set()
for o in sc.objects:
    if o.type != 'MESH': continue
    ms = [s.material.name for s in o.material_slots if s.material]
    if ms and all(m in FXMAT for m in ms):
        SKIP.add(o.name)
print("SKIPPED (see-through) OBJECTS:", len(SKIP), sorted(SKIP)[:40])

def cam_basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    r = f.cross(Vector((0, 0, 1)))
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f).normalized()
    if u.z < 0:
        r = -r; u = r.cross(f).normalized()
    return f, r, u

# How many see-through surfaces a ray may punch through before the probe gives up
# and calls it background.  It was 12, and 12 IS NOT ENOUGH — that is a measured
# statement, not a precaution.  2026-07-31: `boatyard` reported 2 leak rays that
# survived every closure built for them.  Traced hit-by-hit, both rays pass through
# the pitch kettle's two smoke volumes (`fx_kettle_smoke`, `fx_kettle_smoke_plume`,
# 40-vert shells in `mat_smoke`) and collect TWELVE boundary crossings inside four
# metres of plume — so the budget was spent before the ray had even left the
# boatyard, and the first opaque thing it meets, `yard_ground` twenty-five metres
# away, was never reached.  A ray that runs out of budget is scored as a hole in
# the world, which is the one thing this probe exists to be right about, and it
# fails in the direction that INVENTS defects and can equally mask real ones
# behind a nearer FX card.  64 is far past any plausible stack of see-through
# shells in this town (the worst real ray, through kettle smoke + three haze
# slabs, uses 18) and costs nothing on rays that hit rock immediately.
SKIP_BUDGET = 64


def first_opaque(pos, d):
    p = Vector(pos)
    for _ in range(SKIP_BUDGET):
        hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, p, d, distance=1400.0)
        if not hit: return None, None, None
        if ob.name not in SKIP: return ob, loc, nrm
        p = loc + d * 0.01
    return None, None, None

_edge = {}
def mean_edge(ob):
    k = ob.data.name
    if k in _edge: return _edge[k]
    me = ob.data; s = ob.matrix_world.to_scale()
    msc = (abs(s.x) + abs(s.y) + abs(s.z)) / 3.0
    n = len(me.edges)
    if n == 0: _edge[k] = (0.0, 0, 0); return _edge[k]
    step = 1 if n <= 4000 else max(1, n // 4000)
    tot = 0.0; cnt = 0
    for i in range(0, n, step):
        e = me.edges[i]
        tot += (me.vertices[e.vertices[0]].co - me.vertices[e.vertices[1]].co).length
        cnt += 1
    _edge[k] = (tot / cnt * msc, len(me.vertices), len(me.polygons))
    return _edge[k]

res = {}
t_all = time.time()
for c in S["cameras"]:
    cid = c["id"]
    if ONLY and cid not in ONLY: continue
    pos = Vector(c["pos"]); f, r, u = cam_basis(c["pos"], c["aim"])
    ty = math.tan(math.radians(c["fov"]) / 2)
    t0 = time.time()
    names = []; idx = {}; per = {}
    objid = bytearray(GW * GH * 2); dist_a = bytearray(GW * GH * 2)
    miss = 0; missrows = []
    for py in range(GH):
        sy = (1.0 - 2.0 * (py + 0.5) / GH) * ty
        for px in range(GW):
            sx = (2.0 * (px + 0.5) / GW - 1.0) * ty * ASPECT
            d = (f + r * sx + u * sy).normalized()
            ob, loc, nrm = first_opaque(pos, d)
            o = py * GW + px
            if ob is None:
                miss += 1
                missrows.append((px, py, round(d.x, 4), round(d.y, 4), round(d.z, 4)))
                struct.pack_into("<H", objid, o * 2, 0xFFFF)
                struct.pack_into("<H", dist_a, o * 2, 0xFFFF)
                continue
            nm = ob.name
            i = idx.get(nm)
            if i is None:
                i = len(names); idx[nm] = i; names.append(nm)
                el, nv, npo = mean_edge(ob)
                per[nm] = {"i": i, "px": 0, "sd": 0.0, "dmin": 1e9, "dmax": 0.0,
                           "edge": round(el, 4), "verts": nv, "polys": npo,
                           "mats": [s.material.name if s.material else None for s in ob.material_slots],
                           "loc": [round(v, 2) for v in ob.matrix_world.translation],
                           "wmin": [1e9, 1e9, 1e9], "wmax": [-1e9, -1e9, -1e9]}
            dd = (loc - pos).length
            p = per[nm]; p["px"] += 1; p["sd"] += dd
            if dd < p["dmin"]: p["dmin"] = dd
            if dd > p["dmax"]: p["dmax"] = dd
            for a in range(3):
                if loc[a] < p["wmin"][a]: p["wmin"][a] = loc[a]
                if loc[a] > p["wmax"][a]: p["wmax"][a] = loc[a]
            struct.pack_into("<H", objid, o * 2, i)
            struct.pack_into("<H", dist_a, o * 2, min(65534, int(dd * 100)))
    for nm, p in per.items():
        p["dmean"] = round(p["sd"] / p["px"], 2); del p["sd"]
        p["dmin"] = round(p["dmin"], 2); p["dmax"] = round(p["dmax"], 2)
        p["wmin"] = [round(v, 1) for v in p["wmin"]]; p["wmax"] = [round(v, 1) for v in p["wmax"]]
    res[cid] = {"gw": GW, "gh": GH, "pos": c["pos"], "aim": c["aim"], "fov": c["fov"],
                "miss": miss, "total": GW * GH, "objects": per, "names": names,
                "missrows": missrows[:60000],
                "objid": base64.b64encode(bytes(objid)).decode(),
                "dist": base64.b64encode(bytes(dist_a)).decode()}
    print("OPAQUE %-15s SKY-LEAK %6.2f%%  objs %4d  %.0fs" % (cid, 100.0 * miss / (GW * GH), len(names), time.time() - t0))
    sys.stdout.flush()

json.dump({"cameras": res, "matinfo": matinfo, "skipped": sorted(SKIP)}, open(OUT, "w"))
print("WROTE", OUT, "%.0fs" % (time.time() - t_all))
