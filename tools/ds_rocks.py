"""ds_rocks.py — SOMETHING STANDS IN THE POOL, so the pool stops being a plane.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/ds_rocks.py -- [save] [--n 7]
  ... -- revert save

ITERATION 2 of round 3's item 2, and it exists because iteration 1 was LOOKED AT.
`ds_shelf.py` replaced the deep-stairs pool's dead-flat bed with real bathymetry
and `t2_water_shader` re-baked the depth-alpha over it — measured, gated, and by
the numbers a success (bed depth 0.75..4.04 m where it had been one number).  The
PLATE barely moved: over the deep-stairs water mask the frame went from
L mean 103.2 / sd 10.94 to L mean 94.8 / sd 9.07 — darker, no more structure.
The reason is not the bake.  The pool sits in full shadow, so what shows through a
partly transparent surface is unlit rock: the composite is a slightly darker
turquoise, still one tone, still a plane.  NUMBERS FOR ITERATION, PICTURES FOR THE
VERDICT.

So this iteration takes the other lever the judge's two nouns point at.  "Flat"
is not about colour, it is about a surface with nothing on it and nothing in it —
compare `fishdock`, the SAME material and the SAME shader, judged CONVINCING,
where piles, a skiff and a boat break the water in a dozen places.  Boulders at
the foot of a wharf under a cliff are the plainest possible answer and they cost
no light.

A FREE-STANDING SOLID IS SEARCHED, NEVER AUTHORED (world-building doctrine).
Every candidate on a 0.5 m grid over the reach must pass, in this order:
  * it is under water at all — the bed beneath it is at least MIN_DEPTH down;
  * the deep-stairs camera can SEE that spot: the first thing its ray meets is
    `water_pool-mid` within 0.5 m of the candidate.  Not "in frame", not "an
    unobstructed ray to the bed" — the pixel the boulder would occupy;
  * nothing else is close: no mesh other than water and terrain within CLEAR of
    the candidate in the z band the boulder occupies, which keeps it off the
    piles, the skiff walk and the mooring posts;
and the survivors are taken greedily, densest-visibility first, at a minimum
separation of SEP so they read as a scatter rather than a row.  The fallback is
measured in the same pass: the script prints how many candidates each filter
killed, so a future reach can be told apart from a bug.

Each boulder is a subdivided cube in `mat_rock` with seeded per-vertex jitter —
the `boil_dress` shape recipe, which the town already ships — sized so it BREACHES
the surface by BREACH_LO..BREACH_HI.  That is the whole point: a rock wholly under
water would just be more bathymetry, and bathymetry is what iteration 1 already
proved invisible here.
"""
import bpy, os, sys, json, math, random
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/ds_rocks.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
N_WANT = int(argv[argv.index("--n") + 1]) if "--n" in argv else 6

PREFIX = "t2w_rock_deep-stairs_"
MAT = "mat_rock"
CAM = "deep-stairs"
SURF = 0.20
X0, X1, Y0, Y1 = 37.5, 53.0, 22.5, 31.5
GRID = 0.5
MIN_DEPTH = 1.20            # metres of water under the candidate
CLEAR = float(argv[argv.index("--clear") + 1]) if "--clear" in argv else 0.85
                            # metres to anything that is not water or terrain
SEP = 1.60                  # metres between boulders
BREACH_LO, BREACH_HI = 0.14, 0.46
R_LO, R_HI = 0.42, 0.95
SEED = 20260807

TERRAIN = ("riverbed", "seam_bank", "wf_ground", "qm_ground", "cliff_", "t2w_bed_",
           "lf_riverbed", "yard_ground", "shelf_ground")

sc = bpy.context.scene

existing = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
for o in existing:
    bpy.data.objects.remove(o, do_unlink=True)
if existing:
    print("(removed %d previous boulder(s))" % len(existing))
if REVERT:
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

S = json.load(open(os.path.join(ROOT, "public/townmap/dellhollow.cameras.solved.json")))
cam = {c["id"]: c for c in S["cameras"]}[CAM]
eye = Vector(cam["pos"])

water_names = {o.name for o in sc.objects if o.type == 'MESH'
               and any(s.material and s.material.name == "m_water" for s in o.material_slots)}


def is_terrain(nm):
    return any(nm.startswith(t) for t in TERRAIN)


# ---- pass 1: the bed, with water and walk records out of the way ------------
hidden = []
for o in sc.objects:
    if o.type != 'MESH':
        continue
    if o.name in water_names or o.name.startswith("walk_") or o.name.startswith("bar_"):
        if not o.hide_viewport:
            o.hide_viewport = True
            hidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

NX = int((X1 - X0) / GRID) + 1
NY = int((Y1 - Y0) / GRID) + 1
bed = {}
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * GRID, Y0 + j * GRID
        hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, SURF - 0.02)),
                                                Vector((0, 0, -1)), distance=30.0)
        bed[(i, j)] = loc.z if hit else None

# pass 2: OCCUPANCY.  Put the walk records and props back but keep the water
# hidden, and ask a down-ray what actually stands over each spot.  ONE
# DEPSGRAPH IS SHARED, so each visibility state gets its OWN pass rather than a
# helper called from inside the next loop — the first draft toggled visibility
# after taking the depsgraph and every test silently ran against the last state.
# And A BOUNDING BOX CANNOT ANSWER THIS EITHER: `wv_planking` alone spans
# x 46..109 by y 18..30, so a bbox test called every visible cell crowded and the
# search returned nothing.  Ask the geometry.
for nm in hidden:
    o = bpy.data.objects.get(nm)
    if o is not None and o.name not in water_names:
        o.hide_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

occ = {}
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * GRID, Y0 + j * GRID
        b = bed[(i, j)]
        taken = False
        if b is not None:
            for (dx, dy) in ((0, 0), (CLEAR, 0), (-CLEAR, 0), (0, CLEAR), (0, -CLEAR)):
                hit, loc, nrm, fi, ob, mw = sc.ray_cast(
                    dg, Vector((x + dx, y + dy, SURF + 2.0)), Vector((0, 0, -1)),
                    distance=12.0)
                if hit and not is_terrain(ob.name) and loc.z > b - 0.10:
                    taken = True
                    break
        occ[(i, j)] = taken

# pass 3: VISIBILITY, with the water back — it must be the first thing the camera
# meets, or the boulder would stand behind something.
for nm in hidden:
    o = bpy.data.objects.get(nm)
    if o is not None:
        o.hide_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

# the camera basis, so a candidate can be asked the one question the first draft
# forgot: IS IT IN THE FRAME.  "unobstructed ray" is not "visible" (seam-canon
# 10.3) — the first six boulders this search returned all projected to v > 1.10,
# below the bottom edge, and every one of them passed the ray test.
FWD = (Vector(cam["aim"]) - eye).normalized()
RGT = FWD.cross(Vector((0, 0, 1))).normalized()
UPV = RGT.cross(FWD).normalized()
HY = math.tan(math.radians(cam["fov"]) / 2.0)
HX = HY * (1344.0 / 768.0)


def frame_uv(p):
    rel = p - eye
    zc = rel.dot(FWD)
    if zc <= 0.01:
        return None
    return (0.5 + (rel.dot(RGT) / zc) / HX * 0.5, 0.5 - (rel.dot(UPV) / zc) / HY * 0.5)


kill = dict(no_bed=0, too_shallow=0, unseen=0, crowded=0, offframe=0)
cands = []
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * GRID, Y0 + j * GRID
        b = bed[(i, j)]
        if b is None:
            kill["no_bed"] += 1
            continue
        if SURF - b < MIN_DEPTH:
            kill["too_shallow"] += 1
            continue
        # walk records and rails COUNT here: a boulder must not stand on a lane.
        if occ[(i, j)]:
            kill["crowded"] += 1
            continue
        target = Vector((x, y, SURF))
        uv = frame_uv(target)
        if uv is None or not (0.03 <= uv[0] <= 0.97 and 0.03 <= uv[1] <= 0.97):
            kill["offframe"] += 1
            continue
        d = (target - eye)
        dist = d.length
        hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, eye, d.normalized(), distance=dist + 2.0)
        if not (hit and ob.name == "water_pool-mid" and (loc - target).length < 0.5):
            kill["unseen"] += 1
            continue
        cands.append((dist, x, y, b))

cands.sort()                                   # nearest the camera reads biggest
picked = []
for dist, x, y, b in cands:
    if all((x - px) ** 2 + (y - py) ** 2 >= SEP ** 2 for _, px, py, _ in picked):
        picked.append((dist, x, y, b))
    if len(picked) >= N_WANT:
        break

print("=" * 78)
print("SEARCH over %d candidates on a %.1f m grid, x %.1f..%.1f y %.1f..%.1f"
      % (NX * NY, GRID, X0, X1, Y0, Y1))
print("  killed:  no bed %d · shallower than %.2f m %d · within %.2f m of a prop %d "
      "· outside the frame %d · not visible through the surface %d"
      % (kill["no_bed"], MIN_DEPTH, kill["too_shallow"], CLEAR, kill["crowded"],
         kill["offframe"], kill["unseen"]))
print("  survivors %d -> %d taken at %.1f m separation" % (len(cands), len(picked), SEP))
# THE NULL RESULT IS A RECEIPT AND MUST SURVIVE THE REFUSAL: write the manifest
# before the assert, or an empty search leaves nothing on disk to cite.
json.dump(dict(_doc=("GENERATED by tools/ds_rocks.py — boulders SEARCHED into the "
                     "deep-stairs pool so the water surface stops reading as a "
                     "plane. Iteration 2; iteration 1 (ds_shelf) was measured, "
                     "looked at, and found insufficient on its own. An EMPTY "
                     "`rocks` list is a finding about the reach, not a failure of "
                     "the run."),
               generator="tools/ds_rocks.py", camera=CAM, grid=GRID,
               box=[X0, X1, Y0, Y1], min_depth=MIN_DEPTH, clear=CLEAR, sep=SEP,
               breach=[BREACH_LO, BREACH_HI], radius=[R_LO, R_HI], seed=SEED,
               killed=kill, candidates=len(cands), picked=len(picked), rocks=[]),
          open(MANIFEST, "w"), indent=1)

assert picked, ("the search found nowhere to stand a boulder — that is a finding "
                "about the reach, not a reason to place one by hand")

# ---- build --------------------------------------------------------------
mat = bpy.data.materials.get(MAT)
assert mat is not None, "material %s is not in this blend" % MAT
host = bpy.data.objects.get("riverbed")
coll = host.users_collection[0] if host and host.users_collection else sc.collection
rng = random.Random(SEED)
built = []
for k, (dist, x, y, b) in enumerate(picked):
    r = rng.uniform(R_LO, R_HI)
    breach = rng.uniform(BREACH_LO, BREACH_HI)
    top = SURF + breach
    bot = min(b - 0.15, top - 2 * r)           # always sits INTO the bed
    cz = (top + bot) / 2.0
    hz = (top - bot) / 2.0
    V, F = [], []
    # a subdivided box, then seeded jitter — boil_dress's shape recipe
    n = 3
    for a in range(n + 1):
        for c2 in range(n + 1):
            for e in range(n + 1):
                if a in (0, n) or c2 in (0, n) or e in (0, n):
                    V.append((x + r * (2 * a / n - 1), y + r * (2 * c2 / n - 1),
                              cz + hz * (2 * e / n - 1)))
    # convex hull of the jittered shell is a clean closed lump
    for idx in range(len(V)):
        vx, vy, vz = V[idx]
        V[idx] = (vx + rng.uniform(-0.10, 0.10) * r,
                  vy + rng.uniform(-0.10, 0.10) * r,
                  vz + rng.uniform(-0.08, 0.08) * hz)
    me = bpy.data.meshes.new(PREFIX + str(k))
    me.from_pydata(V, [], [])
    me.validate()
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    me.materials.append(mat)
    built.append(dict(name=ob.name, at=[round(x, 2), round(y, 2)], r=round(r, 2),
                      breach=round(breach, 2), top=round(top, 2), bed=round(b, 2),
                      dist=round(dist, 1), verts=len(me.vertices),
                      polys=len(me.polygons)))
    uu, vv = frame_uv(Vector((x, y, top)))
    print("  %-26s at (%.1f, %.1f)  r %.2f  top %+.2f (breach %.2f)  bed %.2f  "
          "%d verts   frame u %.3f v %.3f" % (ob.name, x, y, r, top, breach, b,
                                              len(me.vertices), uu, vv))

# ------------------------------------------------------------------ GATE ----
bad = 0
for rec in built:
    ob = bpy.data.objects[rec["name"]]
    ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
    zt, zb = max(w.z for w in ws), min(w.z for w in ws)
    if not (SURF + BREACH_LO - 0.12 <= zt <= SURF + BREACH_HI + 0.12):
        print("  GATE: %s breaches %.2f, outside %.2f..%.2f"
              % (rec["name"], zt - SURF, BREACH_LO, BREACH_HI))
        bad += 1
    if zb > rec["bed"] + 0.01:
        print("  GATE: %s floats — its base %.2f is above the bed %.2f"
              % (rec["name"], zb, rec["bed"]))
        bad += 1
assert bad == 0, "%d boulder gate violation(s)" % bad
print("  GATE: %d boulders, every one breaching %.2f..%.2f m and bedded into the "
      "floor" % (len(built), BREACH_LO, BREACH_HI))

m = json.load(open(MANIFEST))
m["rocks"] = built
json.dump(m, open(MANIFEST, "w"), indent=1)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
