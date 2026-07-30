"""t2_probe_place.py — READ ONLY.  (a) vertex-colour census of existing cloth /
bunting / awnings, (b) per-camera visibility + occlusion-tested screen-% of
PROPOSED pop-of-colour placements.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_place.py -- --cands tools/blends/districts/t2_color_cands.json \
                                    --out /tmp/place.json

THE PLACEMENT PROBE behind docs/plans/pops-of-color.md Part 3.  Each candidate is
a rectangle (centre `at`, half-edges `e1`/`e2`); it is projected into all 17
solved cameras and its 25 sample points are ray-cast against the town, so the
reported `screen` is the share of frame the element covers AFTER occlusion, not a
wish.  `screen_full` is the unoccluded projection and `vis` the visible fraction.

The census half prints, for every mesh whose name contains cloth/bunting/awning/
flag/pennant, the top vertex `Col` values by loop count — that is what found the
two free wins: nine awnings that are >50% neutral grey, and lf_bunting_0..3 whose
810 loops are 720 brown rope.

RE-RUN IT AFTER THE CLIFF PASS, before building any colour: the 47-row budget was
measured against frames in which up to 22.6% of pixels were the grey cliff_town
slab that cliff-completion.md replaces.

CPU ray-casts only.  NEVER saves.
"""
import bpy, os, sys, json, math
from mathutils import Vector
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d): return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
OUT = opt("--out", "/tmp/place.json")
S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
ASPECT = S["defaults"]["aspect"]
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()

def srgb(v):
    v = max(0.0, min(1.0, v))
    return v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055

print("=" * 90)
print("EXISTING CLOTH / BUNTING VERTEX COLOURS (lf_matte & friends drive colour from Col)")
print("=" * 90)
vc = {}
for o in sc.objects:
    if o.type != 'MESH': continue
    if not any(k in o.name for k in ("cloth", "bunting", "awning", "flag", "pennant")): continue
    me = o.data
    ca = me.color_attributes.active_color if me.color_attributes else None
    if ca is None:
        print("%-24s NO Col attribute  mats=%s" % (o.name, [s.material.name for s in o.material_slots if s.material]))
        continue
    cols = {}
    n = len(ca.data)
    for i in range(0, n, max(1, n // 600)):
        c = ca.data[i].color
        k = (round(c[0], 2), round(c[1], 2), round(c[2], 2))
        cols[k] = cols.get(k, 0) + 1
    top = sorted(cols.items(), key=lambda kv: -kv[1])[:6]
    print("%-24s loops=%-6d distinct~%-4d  top: %s" % (o.name, n, len(cols),
          " ".join("%s x%d" % (str(tuple(round(srgb(x), 2) for x in k)), v) for k, v in top)))
    vc[o.name] = {"n": n, "top": [[list(k), v] for k, v in top]}

# ------------------------------------------------------------------ placements
CANDS_PATH = opt("--cands", os.path.join(REPO, "tools/blends/districts/t2_color_cands.json"))
CANDS = json.load(open(CANDS_PATH)) if os.path.exists(CANDS_PATH) else []
print("\nPLACEMENT CANDIDATES: %d from %s" % (len(CANDS), CANDS_PATH))

def basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    r = f.cross(Vector((0, 0, 1)))
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize(); u = r.cross(f).normalized()
    if u.z < 0: r = -r; u = r.cross(f).normalized()
    return f, r, u

def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0

out = {}
for c in S["cameras"]:
    cid = c["id"]; pos = Vector(c["pos"]); f, r, u = basis(c["pos"], c["aim"])
    ty = math.tan(math.radians(c["fov"]) / 2)
    rows = {}
    for cand in CANDS:
        ctr = Vector(cand["at"]); e1 = Vector(cand["e1"]); e2 = Vector(cand["e2"])
        corners = [ctr - e1 - e2, ctr + e1 - e2, ctr + e1 + e2, ctr - e1 + e2]
        ndc = []
        ok = True
        for p in corners:
            v = p - pos; z = v.dot(f)
            if z <= 0.2: ok = False; break
            ndc.append(((v.dot(r) / z) / (ty * ASPECT), (v.dot(u) / z) / ty))
        if not ok: rows[cand["id"]] = {"vis": 0.0, "screen": 0.0, "why": "behind"}; continue
        # clip-ish: fraction of the quad inside [-1,1]^2 estimated on a 5x5 sample
        inside = 0; seen = 0; tot = 0
        for a in range(5):
            for b in range(5):
                sA = (a + 0.5) / 5 * 2 - 1; sB = (b + 0.5) / 5 * 2 - 1
                p = ctr + e1 * sA + e2 * sB
                v = p - pos; z = v.dot(f)
                tot += 1
                if z <= 0.2: continue
                nx = (v.dot(r) / z) / (ty * ASPECT); ny = (v.dot(u) / z) / ty
                if abs(nx) > 1 or abs(ny) > 1: continue
                inside += 1
                d = (p - pos)
                hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, pos, d.normalized(), distance=d.length - 0.25)
                if not hit: seen += 1
        frame_area = 4.0                       # NDC frame is 2x2
        raw = poly_area(ndc) / frame_area
        vis = seen / tot
        rows[cand["id"]] = {"vis": round(vis, 3),
                            "inframe": round(inside / tot, 3),
                            "screen": round(100.0 * raw * vis, 3),
                            "screen_full": round(100.0 * raw, 3),
                            "dist": round((ctr - pos).length, 1)}
    out[cid] = rows

json.dump({"vertexcolours": vc, "placements": out}, open(OUT, "w"))
print("\nWROTE", OUT)
