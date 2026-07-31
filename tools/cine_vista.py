#!/usr/bin/env python3
"""cine_vista.py — SEARCH the establishing plate. Where do you stand to see a whole town?

    Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
        -P tools/cine_vista.py -- [--cam vista] [--out scratchpad/vista.json]
        [--coarse] [--top 24] [--require-arrival]

WHY THIS IS A SEARCH AND NOT AN AUTHORED FRAME. House doctrine: a free-standing thing is
SEARCHED, never authored, and the fallback is measured in the same pass. An establishing
plate is exactly that — a camera position with no region to anchor it, chosen from the
whole outside of the town. It is also the shot most likely to be argued about, so the
argument should be over a table of measurements.

THREE LESSONS THE PREVIOUS THREE ATTEMPTS PAID FOR (2026-08-01, DAYLOG round 2c). They
are enforced here in code, because a note saying "don't do that again" is not a gate:

  1. SCORE BY RAY-CAST, NEVER BY FRUSTUM. v1 scored landmarks merely inside the frustum,
     claimed 97.1% of the town, and baked a grazing view with the near cliff eating a
     third of the frame. "In frame != visible != unobstructed ray" is this repo's own
     doctrine. Here the frustum test is used ONLY as an admissible upper bound to prune
     candidates before ray-casting them (a probe out of frame cannot be visible, so
     ranking by in-frame can never discard a candidate that would have won).

  2. NEVER SCORE LANDMARK CENTRES. They sit inside their own buildings and can never be
     reached by a ray, so that metric under-counts by construction. The probes here are
     the town's WALK RECORDS — the ground a player can actually stand on — which is also
     what "the town" means to a player.

  3. AIM AT HORIZON LEVEL. Every v1/v2 aim point was down at the water, which forces a
     map view; a town reads as a town in ELEVATION. The aim is therefore held at the
     town's own inhabited height and the camera's DEPRESSION ANGLE is a reported,
     bounded quantity rather than whatever fell out of the fit.

THE PROBE SET IS NOT REBUILT HERE — IT IS READ FROM THE SOLVED FILE, and that is the
point of the plumbing. tools/cine_solve.mjs gives a cinematic camera a probe set spread
over EVERY walk mesh (not an owned region), and it does not depend on pos/aim, so the 64
points this search ranks candidates by are byte-identical to the 64 points cine_bake.py
will ray-cast when the winner is baked. The search's prediction and the bake's
measurement are therefore the same number, taken by the same instrument, and a
disagreement between them would be a real defect rather than a methodology gap.
A second, HIGH-RESOLUTION coverage number is computed for the finalists from every walk
mesh's own top-face samples, so the 64-probe figure can be checked for thinning bias.

WHAT ELSE IS MEASURED, because a vista that shows the town and not the river does not
answer the ask ("the entire dellhollow town and river"): river coverage over a grid on
the water surfaces, by the same ray-cast.

THE RAY-CAST IS THE SCENE'S OWN, WITH NOTHING DELETED. cine_bake.py computes visibleFrac
in its beauty pass, before it strips render-only volumes for the depth pass, so this
matches it exactly. If a haze dome occludes the town, it occludes it in the bake too and
this search must see that rather than be protected from it.
"""
import bpy, os, sys, json, math, time
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.abspath(bpy.data.filepath))) \
    if bpy.data.filepath else "/Users/junshernchan/projects/multiplayer-rpg"
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, dflt):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else dflt


CAMID = opt("--cam", "vista")
OUT = opt("--out", os.path.join(REPO, "scratchpad/vista_search.json"))
TOP = int(opt("--top", "24"))
COARSE = "--coarse" in argv

SOLVED = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
D = SOLVED["defaults"]
CAM = next(c for c in SOLVED["cameras"] if c["id"] == CAMID)
FOV = CAM.get("fov", D["fov"])
ASPECT = CAM.get("aspect", D["aspect"])
MARGIN = D["margin"]
PROBES = [Vector(p) for p in CAM["probes"]]          # THE bake's own 64 points

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# ---------------------------------------------------------------- the targets --
# HIGH-RESOLUTION WALK PROBES, built the same way cine_solve builds its own: every
# walk_ mesh's top face at centre + 4 corners, lifted to chest (0.5*charH) and head.
CH = D["charH"]
walk_full = []
for o in sc.objects:
    if o.type != 'MESH' or not o.name.startswith('walk_'):
        continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    x0 = min(p.x for p in bb); x1 = max(p.x for p in bb)
    y0 = min(p.y for p in bb); y1 = max(p.y for p in bb)
    z1 = max(p.z for p in bb)
    for (px, py) in [((x0 + x1) / 2, (y0 + y1) / 2), (x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        for h in (CH * 0.5, CH):
            walk_full.append(Vector((px, py, z1 + h)))

# RIVER PROBES: POINTS ON THE WATER MESH ITSELF — its polygon centres, lifted 5 cm so a
# ray does not terminate on the surface it is aimed at — clipped to the town's own
# along-gorge span, because "the river" in the user's ask is the river AT Dellhollow and
# scoring 150 m of water the town never sees would let a camera win by pointing away.
#
# NOT A GRID OVER THE BOUNDING BOX, and the correction is the same one v2 had to make
# about landmark centres. The pools' boxes span y 22.8..74 and the water inside them is a
# channel; a uniform grid over the box puts most of its points over the far bank, where
# they are occluded by terrain and counted as river-not-visible. That is an instrument
# that under-reports by construction, and it under-reported by a factor of two.
wx0 = min(p.x for p in walk_full); wx1 = max(p.x for p in walk_full)
water = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith('water_')]
river = []
for o in water:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    M = o.matrix_world
    for poly in me.polygons:
        c = M @ poly.center
        if wx0 <= c.x <= wx1:
            river.append(Vector((c.x, c.y, c.z + 0.05)))
    ev.to_mesh_clear()
if len(river) > 320:                       # deterministic thinning, as pickSpread does
    step = len(river) / 320.0
    river = [river[int(i * step)] for i in range(320)]

# THE ARRIVAL the plate must contain. cine_test projects the town-side portal spawn
# through the shot the portal opens on and asserts it is in frame — a player must never
# materialise off-screen, and a plate is no exception even when they are a speck. Read
# from the shipped wiring so this search cannot drift from the assertion.
SG = json.load(open(os.path.join(REPO, "public/world/scenegraph.json")))
ARRIVAL = None
for e in SG["edges"]:
    if e["kind"] == "portal" and e["to"] == SOLVED["sceneKey"]:
        s = e["spawn"]                                   # runtime [x, up, -y]
        ARRIVAL = Vector((s[0], -s[2], s[1] + CH * 0.5))  # -> map [x, y, h], chest
        break

CENTROID = Vector((sum(p.x for p in walk_full) / len(walk_full),
                   sum(p.y for p in walk_full) / len(walk_full),
                   sum(p.z for p in walk_full) / len(walk_full)))
TOWN_H = CENTROID.z                       # the town's own inhabited height: horizon level

print("probes: %d bake-set, %d high-res walk, %d river; town centroid %s; arrival %s"
      % (len(PROBES), len(walk_full), len(river),
         [round(v, 1) for v in CENTROID], [round(v, 1) for v in ARRIVAL] if ARRIVAL else None))


# ------------------------------------------------------------------- the frame --
def basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    U = Vector((0, 0, 1))
    r = f.cross(U)
    if r.length < 1e-6:
        r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f).normalized()
    if u.z < 0:
        r = -r
        u = r.cross(f).normalized()
    return f, r, u


TY = math.tan(math.radians(FOV) / 2)


def in_frame(pos, F, R, U, p, pad=1.0):
    v = p - pos
    z = v.dot(F)
    if z <= 1e-6:
        return False
    return abs((v.dot(R) / z) / (TY * ASPECT)) <= pad and abs((v.dot(U) / z) / TY) <= pad


def clear(origin, targets, F, R, U):
    """in-frame AND unobstructed. Returns (visible, in_frame). Same ray as cine_bake."""
    vis = 0
    inf = 0
    for p in targets:
        if not in_frame(origin, F, R, U, p):
            continue
        inf += 1
        v = p - origin
        L = v.length
        if L < 1e-4:
            continue
        hit, *_ = sc.ray_cast(dg, origin, v.normalized(), distance=L - 0.35)
        if not hit:
            vis += 1
    return vis, inf


def standable(pos):
    """The camera must be in open air. A candidate buried in the far cliff scores zero
    and would be rejected by the ray-cast anyway, but this catches the subtler case the
    map's 13 draft cameras died of: a position INSIDE a solid, where every ray leaves
    through a backface and the shot looks merely 'dark' in a report."""
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        hit, *_ = sc.ray_cast(dg, pos, Vector(d), distance=1.5)
        if not hit:
            return True
    return False


# ------------------------------------------------------------------ the sweep --
# THE SEARCH SPACE, stated so it can be argued with. The plate is unshackled from the
# walkable shots' standoff cap (that cap is a legibility constraint and a plate has no
# legibility duty), so distance runs out to where the arithmetic says a 100 m town fits:
# at fov 35 / aspect 1.75 the horizontal half-angle is 28.9 deg, so 100 m of frontage
# needs ~90 m of standoff head-on, less when the view is oblique.
if COARSE:
    AIMX = [CENTROID.x]
    AIMY = [CENTROID.y]
    YAWS = list(range(0, 360, 20))
    PITCHES = [10, 20, 30]
    DISTS = [60, 90, 120]
else:
    AIMX = [CENTROID.x - 12, CENTROID.x, CENTROID.x + 12]
    AIMY = [CENTROID.y - 6, CENTROID.y, CENTROID.y + 6]
    YAWS = list(range(0, 360, 10))
    PITCHES = [8, 14, 20, 26, 32, 38]
    DISTS = [55, 70, 85, 100, 115, 130]
AIMH = [TOWN_H]
# Every axis is overridable so the same tool does the coarse sweep, the full sweep and
# the LOCAL REFINEMENT around a winner without a second script that could drift from it.
_ax = {"--aimx": "AIMX", "--aimy": "AIMY", "--aimh": "AIMH",
       "--yaw": "YAWS", "--pitch": "PITCHES", "--dist": "DISTS"}
for flag, var in _ax.items():
    if flag in argv:
        globals()[var] = [float(v) for v in opt(flag, "").split(",")]

cands = []
for ax in AIMX:
    for ay in AIMY:
      for ah in AIMH:
        aim = Vector((ax, ay, ah))              # HORIZON LEVEL by default, lesson 3
        for yaw in YAWS:
            for pit in PITCHES:
                for dist in DISTS:
                    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
                    cp, sp = math.cos(math.radians(pit)), math.sin(math.radians(pit))
                    pos = aim + Vector((cp * cy, cp * sy, sp)) * dist
                    cands.append((pos, aim, yaw, pit, dist))
print("candidates: %d" % len(cands))

# --- stage 1: frustum only (no rays). An ADMISSIBLE upper bound on coverage. -----
t0 = time.time()
stage1 = []
for (pos, aim, yaw, pit, dist) in cands:
    F, R, U = basis(pos, aim)
    if ARRIVAL is not None and not in_frame(pos, F, R, U, ARRIVAL, 1.0 - MARGIN):
        continue                                  # the arrival must be ON the plate
    n = sum(1 for p in walk_full if in_frame(pos, F, R, U, p))
    if n == 0:
        continue
    stage1.append((n / len(walk_full), pos, aim, yaw, pit, dist))
stage1.sort(key=lambda r: -r[0])
KEEP = 900 if not COARSE else 200
survived = len(stage1)
stage1 = stage1[:KEEP]
print("stage 1 (frustum bound): %d of %d candidates frame the arrival and see any of the "
      "town, kept the best %d, best bound %.1f%%  [%.1fs]"
      % (survived, len(cands), len(stage1), stage1[0][0] * 100 if stage1 else 0,
         time.time() - t0))

# --- stage 2: ray-cast the BAKE's own 64 probes ---------------------------------
t0 = time.time()
stage2 = []
for (bound, pos, aim, yaw, pit, dist) in stage1:
    if not standable(pos):
        continue
    vis, inf = clear(pos, PROBES, *basis(pos, aim))
    stage2.append({"cov64": vis / len(PROBES), "bound": bound,
                   "pos": [round(v, 3) for v in pos], "aim": [round(v, 3) for v in aim],
                   "yaw": yaw, "pitch": pit, "dist": dist})
stage2.sort(key=lambda r: -r["cov64"])
print("stage 2 (ray-cast, %d bake probes): %d in open air, best %.1f%%  [%.1fs]"
      % (len(PROBES), len(stage2), stage2[0]["cov64"] * 100 if stage2 else 0, time.time() - t0))

# --- stage 3: the finalists at full resolution, plus the river -------------------
# THE FINALISTS ARE A PARETO FRONT OVER DEPRESSION, NOT A GLOBAL TOP-N, and that is the
# correction this search needed after its first full run. Coverage rises MONOTONICALLY
# with altitude — every occluder in a canyon town is beaten by getting above it — so a
# global top-N is a list of thirty aerial photographs, and the metric has quietly
# answered a question nobody asked. A town reads as a town in ELEVATION; the down-angle
# is the thing being traded away, so it is the axis the report is banded on and the
# choice between bands is a stated one rather than a maximum.
t0 = time.time()
PER_BAND = int(opt("--per-band", "5"))
bands = {}
for r in stage2:
    bands.setdefault(r["pitch"], []).append(r)
shortlist = []
for p in sorted(bands):
    shortlist += bands[p][:PER_BAND]
final = []
for r in shortlist[:max(TOP, len(shortlist))]:
    pos = Vector(r["pos"])
    aim = Vector(r["aim"])
    F, R, U = basis(pos, aim)
    wv, wi = clear(pos, walk_full, F, R, U)
    rv, ri = clear(pos, river, F, R, U)
    r = dict(r)
    r["covWalk"] = wv / len(walk_full)
    r["inFrameWalk"] = wi / len(walk_full)
    r["covRiver"] = rv / len(river) if river else None
    # SPLIT THE RIVER'S MISS INTO ITS TWO CAUSES. `covRiver` counts a probe only if it
    # is BOTH in frame and unoccluded, so a low number can mean "the gorge hides the
    # water" or "that reach is behind the camera", and those are opposite verdicts. The
    # town never needs this split (inFrameWalk is 100% for every finalist); the river
    # does, because the pools run 50 m wide and out past the camera's own standpoint.
    r["inFrameRiver"] = ri / len(river) if river else None
    r["depressionDeg"] = round(math.degrees(math.asin(max(-1, min(1, (pos - aim).normalized().z)))), 2)
    r["arrivalInFrame"] = bool(ARRIVAL is not None and in_frame(pos, F, R, U, ARRIVAL, 1.0 - MARGIN))
    final.append(r)
final.sort(key=lambda r: (r["depressionDeg"], -r["covWalk"]))
print("stage 3 (%d finalists, %d high-res probes + %d river)  [%.1fs]"
      % (len(final), len(walk_full), len(river), time.time() - t0))

print("\n idx  depr  cov64  covWalk  covRiver (of inFrame)  townInFrame   yaw  dist   cam h   pos")
for i, r in enumerate(final):
    print(" %3d  %4.0f  %5.1f%%  %6.1f%%   %6.1f%%  (%5.1f%%)        %6.1f%%  %4d  %4d  %6.1f   %s"
          % (i, r["depressionDeg"], r["cov64"] * 100, r["covWalk"] * 100,
             (r["covRiver"] or 0) * 100, (r["inFrameRiver"] or 0) * 100,
             r["inFrameWalk"] * 100, r["yaw"], r["dist"], r["pos"][2],
             [round(v, 1) for v in r["pos"]]))
print("\nTHE CEILING PER DEPRESSION BAND — the trade the choice is made against:")
for p in sorted(bands):
    b = [r for r in final if r["pitch"] == p]
    if not b:
        continue
    best = max(b, key=lambda r: r["covWalk"])
    bestr = max(b, key=lambda r: (r["covRiver"] or 0))
    print("  %2d deg down:  town %5.1f%% (yaw %3d, %3d m, h %5.1f)   |  best river in band "
          "%5.1f%% at town %5.1f%%"
          % (p, best["covWalk"] * 100, best["yaw"], best["dist"], best["pos"][2],
             (bestr["covRiver"] or 0) * 100, bestr["covWalk"] * 100))

# ------------------------------------------------------ shoot the finalists ----
# THE NUMBER CHOOSES THE BAND; THE EYE CHOOSES INSIDE IT. Coverage cannot tell a town
# from a contour map, and this project has already baked one vista that scored well and
# looked like a plan view. The preview is rendered through the SAME camera construction
# and the SAME grade cine_bake.py uses, so what is judged here is what would ship.
SHOOT = opt("--shoot", "")
if SHOOT:
    idx = [int(v) for v in SHOOT.split(",")] if SHOOT != "all" else list(range(len(final)))
    SDIR = opt("--shoot-out", os.path.join(REPO, "docs/qa/districts"))
    os.makedirs(SDIR, exist_ok=True)
    sc.view_settings.view_transform = D.get("view_transform", "AgX")
    sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
    sc.view_settings.exposure = D.get("exposure", 0.0)
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.cycles.samples = int(opt("--samples", "48"))
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        cp = prefs.preferences
        try:
            cp.compute_device_type = 'METAL'; cp.get_devices()
            for d in cp.devices: d.use = True
            sc.cycles.device = 'GPU'
        except Exception as e:
            print("GPU setup failed, CPU fallback:", e)
    for i in idx:
        if i >= len(final):
            continue
        r = final[i]
        cd = bpy.data.cameras.new("vista_%02d" % i)
        cd.sensor_fit = 'VERTICAL'
        cd.angle_y = math.radians(FOV)
        cd.clip_start, cd.clip_end = CAM["clip"][0], CAM["clip"][1]
        ob = bpy.data.objects.new("vista_%02d" % i, cd)
        sc.collection.objects.link(ob)
        ob.location = Vector(r["pos"])
        ob.rotation_euler = (Vector(r["aim"]) - ob.location).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = ob
        f = os.path.join(SDIR, "vista_d%02d_y%03d_%03dm.png"
                         % (round(r["depressionDeg"]), r["yaw"], r["dist"]))
        sc.render.filepath = f
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print("  shot %-42s %.1fs   town %.1f%%  river %.1f%%"
              % (os.path.basename(f), time.time() - t, r["covWalk"] * 100,
                 (r["covRiver"] or 0) * 100))
        bpy.data.objects.remove(ob, do_unlink=True)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "tool": "tools/cine_vista.py", "cam": CAMID, "fov": FOV, "aspect": ASPECT,
           "candidates": len(cands), "probes64": len(PROBES),
           "probesHiRes": len(walk_full), "probesRiver": len(river),
           "arrival": [round(v, 3) for v in ARRIVAL] if ARRIVAL else None,
           "finalists": final}, open(OUT, "w"), indent=1)
print("\nwrote %s" % OUT)
