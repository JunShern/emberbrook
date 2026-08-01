"""t3_cliff_gorge.py — SCULPT THE DOWNSTREAM GORGE WALL.  Task #35, the user's
ruling: "replace the crude, blocky rectangular cliff used everywhere above town
height — perfect vertical rectangular drop-off into an empty vacuum".

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_cliff_gorge.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_cliff_gorge.py -- revert [save]      (back to the C2 shape)

WHICH CLIFF, MEASURED.  `tools/t2_probe_leak.py`'s first-opaque screen tally on
the shipped master names it without ambiguity:

    cliff_east_closure   1,173 verts   mean edge 2.12 m   mat_rock_farwall
        lockfive 19.88%   gate 14.63%   crossing 13.89%   of frame
        and 82.4% of the gate plate's ENTIRE TOP-LEFT QUADRANT

Its bbox is x 136..150, y -13..85.5, z -16..26.0 — and that 26.0 is EXACT,
because `t2_cliff_east.py` lays its top row on a constant z.  A flat plane, a
dead-straight horizon, and a 20 m texture tile.  That is the user's sentence,
in numbers.

WHAT CHANGES, AND WHAT DELIBERATELY DOES NOT.

1. RELIEF.  The C2 `edepth()` was "a lean and two swells, nothing that would
   repay a seventh octave", written when the wall was believed to be pure
   silhouette at 60-100 m.  It is now measured at d_mean 88.8 m (crossing) and
   91.3 m (lockfive) filling a FIFTH of those frames, which is not silhouette.
   It gets the south wall's proven language instead — seven incommensurate
   plane-wave octaves, two horizontal strata biases, a talus toe, and five
   vertical fissures.  NO PERIODIC LEDGES: cliff-completion.md AS BUILT note 3
   already paid for that lesson (a regular vertical period under the 53-degree
   raking key renders as a stacked quarry).

2. THE RIM BREAKS, AND IT ONLY EVER GOES UP.  The straight horizon is the single
   most legible thing about the old wall, so the top row carries a crest profile.
   `crest()` IS CLAMPED NON-NEGATIVE ON PURPOSE: a rim that dips below the old
   z = 26.0 would let a ray that used to hit the wall sail over it, and a new
   background pinhole is precisely the defect this wall exists to close.  Going
   only up is a monotone change and cannot leak.  The cap strip follows the
   crest back to x = 150 so the shell stays closed.

3. RESOLUTION.  Edge 2.12 m -> 1.30 m in the band the three cameras see
   (y -13..46, the fan every one of their rays crosses), 2.6 m north of it where
   only `cliff_far`'s overlap is behind.  ~4,600 verts, up from 1,173.

4. MATERIAL.  `mat_rock_gorgewall`, a copy of `mat_rock_farwall` with its
   Mapping scale 0.05 -> 0.30.  0.05 is a TWENTY METRE texture tile; at 88 m
   that is a smear, not rock.  0.30 is 3.33 m, which subtends ~92 px on the
   shipped 1536-line frame.  The blue-grey recession tint is KEPT — AS BUILT
   note 1 says mat_rock_farwall is an atmospheric-perspective material and is
   correct at 60-100 m, which is exactly where this wall stands; it is only
   wrong up close, where the south wall lives.  A COPY, not an edit, so
   `cliff_far` and `cliff_far_toe` (112-170 m) are untouched.

5. THE C2 ROW-PITCH FREEZE IS RETIRED, ON PURPOSE.  `t2_cliff_east.py` pins its
   row pitch so that the part of the wall lockfive and cottage-steps already had
   baked plates of stays bit-identical.  That constraint exists to protect
   plates; this pass REBAKES all three cameras that see the wall, so it has
   nothing left to protect and it would forbid the resolution change.  Recorded
   rather than silently dropped.

WHAT IT DOES NOT TOUCH: y extent, z floor, the x = 140 reference plane, the
overlap into `cliff_far` at y 85.53, the haze cards, the skirt.  The 1,234-ray
and 10,384-ray closure traces in cliff-completion.md stay valid because the
surface only ever moves EAST (deeper) or UP, never back through the traced plane.

NOT WALKABLE, NOT IN A WALK CORRIDOR: the nearest walk record is 30 m west.
"""
import bpy, os, sys, math, json

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t3_cliff_gorge.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

WALL = "cliff_east_closure"
COLL = "CONTEXT"
MAT = "mat_rock_gorgewall"
MAT_TEMPLATE = "mat_rock_farwall"
MAP_SCALE = 0.30                  # 3.33 m rock tile (was 0.05 = 20 m)

EX = 140.0                        # the traced closure plane
EY0 = -13.0
EZ0, EZ1 = -16.0, 26.0            # EZ1 is the OLD rim; the crest only rises off it
CAP_X = 150.0

# the C2 pitch, kept only to reproduce the same y extent exactly
EY1_C2, EDGE_C2 = 54.0, 2.0
NY_C2 = max(2, int(round((EY1_C2 - EY0) / EDGE_C2)) + 1)
PITCH_C2 = (EY1_C2 - EY0) / (NY_C2 - 1)
EY1 = EY0 + PITCH_C2 * (NY_C2 + 16 - 1)          # 85.53, unchanged

# ---- resolution bands in y.  (y0, y1, step) ---------------------------------
# The three cameras' rays all cross x = 140 inside y -13..46; north of that only
# the cliff_far overlap is behind the wall and nothing reads its facets.
YBANDS = [(EY0, 46.0, 1.30), (46.0, EY1, 2.60)]
ZSTEP = 1.30

# (amplitude m, y frequency, z frequency, phase) — incommensurate on purpose, so
# no two octaves ever come back into step and the relief never repeats.
OCTAVES = [
    (2.60, 0.0330,  0.0210,  0.40),
    (1.55, 0.0790, -0.0410,  2.15),
    (0.95, 0.1630,  0.0930, -1.35),
    (0.58, 0.3110, -0.1770,  0.80),
    (0.34, 0.6070,  0.2890,  2.90),
    (0.19, 1.1900, -0.5410,  1.55),
    (0.11, 2.3100,  1.0700, -2.05),
]
FISSURES = [                       # (y, width m, extra depth m)
    (-2.0, 2.6, 3.10), (14.0, 2.0, 2.40), (27.5, 2.3, 2.90),
    (41.0, 1.8, 2.20), (58.0, 2.4, 2.00),
]
CRESTS = [                         # (y, width m, height m) — the rim, upward only
    (-9.0, 11.0, 4.6), (6.0, 9.0, 2.4), (19.0, 13.0, 5.8),
    (34.0, 10.0, 3.1), (50.0, 15.0, 4.2), (68.0, 12.0, 2.6),
]


def axis(a, b, step):
    n = max(1, int(math.ceil((b - a) / step - 1e-9)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def rows_y():
    out = []
    for a, b, s in YBANDS:
        for v in axis(a, b, s):
            if not out or abs(v - out[-1]) > 1e-7:
                out.append(v)
    return out


YR = rows_y()
ZR = axis(EZ0, EZ1, ZSTEP)


def crest(y):
    """metres the rim stands ABOVE the old z = 26.0.  NEVER NEGATIVE — see the
    header: a dipping rim opens a background pinhole, which is the defect this
    wall exists to close."""
    c = 0.0
    for cy, cw, ch in CRESTS:
        c += ch * math.exp(-(((y - cy) / cw) ** 2))
    c += 0.55 * math.sin(y * 0.117 + 1.3) + 0.30 * math.sin(y * 0.243 - 0.6)
    return max(0.0, c)


def edepth(y, z):
    """metres EAST of x = 140.  Only ever positive, so the surface can never move
    back through the traced closure plane."""
    # BASE 3.10, and the 2.00 m over the first draft's 1.10 is MEASURED, not
    # guessed.  At 1.10 the raw field reached -1.780 m and the max(0, ...) clamp
    # fired on 170 of the 10,115 sampled cells in the visible band; a clamp does
    # not merely cost relief, it welds every clamped vertex onto ONE dead-flat
    # plane, and a flat facet is the defect this pass exists to remove.  Swept at
    # 0.25 m over the whole wall (y -13..85.53, z -16..26):
    #     base 1.10  raw depth -1.780 .. +11.308 m    clamp fires
    #     base 3.00  raw depth +0.120 .. +13.208 m    clear by 12 cm
    #     base 3.10  raw depth +0.220 .. +13.308 m    clear by 22 cm  <- shipped
    # So "only ever positive" is now true BY CONSTRUCTION rather than by
    # clipping, and the closure trace still holds because the surface only ever
    # moves EAST of the traced plane at x = 140.
    d = 3.10 + 0.085 * max(0.0, z + 4.0)          # leans away as it rises
    for a, fy, fz, ph in OCTAVES:
        d += a * math.sin(y * fy + z * fz + ph)
    # horizontal strata — grain, never a step (AS BUILT note 3)
    d += 0.85 * math.sin(z * 0.905 + 0.40 * math.sin(y * 0.047) + 0.75)
    d += 0.34 * math.sin(z * 1.870 + 0.65 * math.sin(y * 0.112) - 0.85)
    # talus toe: the wall comes forward (west) low down, where the gorge floor is
    d -= 1.30 * math.exp(-(((z + 9.0) / 4.2) ** 2))
    for fy, fw, fd in FISSURES:
        d += fd * math.exp(-(((y - (fy + 0.19 * (z - 5.0))) / fw) ** 2))
    return max(0.0, d)


def new_mesh(name, verts, faces, mat, cname):
    old = bpy.data.objects.get(name)
    flags = None
    if old:
        flags = dict(hide_render=old.hide_render, hide_viewport=old.hide_viewport,
                     visible_shadow=old.visible_shadow)
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    for p in me.polygons:
        p.use_smooth = True          # from_pydata leaves every polygon flat
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    (bpy.data.collections.get(cname) or bpy.context.scene.collection).objects.link(ob)
    if flags:
        for k, v in flags.items():
            setattr(ob, k, v)
    return ob


# =============================================================== REVERT =======
if REVERT:
    # rebuild the C2 shape exactly: 2.0 m grid, the lean-and-two-swells depth,
    # constant rim, mat_rock_farwall.
    def c2depth(y, z):
        d = 2.6 * math.sin(y * 0.052 + 0.9) + 1.5 * math.sin(y * 0.021 - 2.1)
        d += 0.9 * math.sin(y * 0.190 + z * 0.06 + 1.7)
        d += 0.35 * math.sin(y * 0.610 - z * 0.31)
        d += 0.14 * max(0.0, z + 4.0)
        return d
    ny = NY_C2 + 16
    nz = max(2, int(round((EZ1 - EZ0) / EDGE_C2)) + 1)
    v, f = [], []
    for i in range(ny):
        y = EY0 + (EY1 - EY0) * i / (ny - 1)
        for j in range(nz):
            z = EZ0 + (EZ1 - EZ0) * j / (nz - 1)
            v.append((EX + c2depth(y, z), y, z))
    for i in range(ny - 1):
        for j in range(nz - 1):
            a = i * nz + j
            f.append((a, a + 1, a + nz + 1, a + nz))
    b = len(v)
    v += [(CAP_X, EY0 + (EY1 - EY0) * i / (ny - 1), EZ1) for i in range(ny)]
    for i in range(ny - 1):
        a = i * nz + (nz - 1)
        f.append((a, b + i, b + i + 1, (i + 1) * nz + (nz - 1)))
    new_mesh(WALL, v, f, bpy.data.materials[MAT_TEMPLATE], COLL)
    m = bpy.data.materials.get(MAT)
    if m is not None and m.users == 0:
        bpy.data.materials.remove(m)
    print("REVERTED %s to the C2 shape: %d verts / %d polys, %s" % (WALL, len(v), len(f), MAT_TEMPLATE))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# =============================================================== MATERIAL =====
mat = bpy.data.materials.get(MAT)
if mat is None:
    mat = bpy.data.materials[MAT_TEMPLATE].copy()
    mat.name = MAT
    print("DERIVED %s from %s (a COPY — cliff_far and cliff_far_toe keep theirs)"
          % (MAT, MAT_TEMPLATE))
mp = [n for n in mat.node_tree.nodes if n.type == 'MAPPING']
assert len(mp) == 1, "expected exactly one Mapping node in %s" % MAT
old_scale = round(mp[0].inputs['Scale'].default_value[0], 4)
mp[0].inputs['Rotation'].default_value = (0.0, 0.0, 0.0)
mp[0].inputs['Scale'].default_value = (MAP_SCALE,) * 3
proj = sorted(set(t.projection for t in mat.node_tree.nodes if t.type == 'TEX_IMAGE'))
assert proj == ['BOX'], "%s Image Textures are %s, not BOX" % (MAT, proj)
print("   Mapping rotation 0 (box projection picks the plane), scale %.3f -> %.3f  "
      "(tile %.1f m -> %.2f m)" % (old_scale, MAP_SCALE, 1.0 / old_scale, 1.0 / MAP_SCALE))

# =============================================================== THE WALL =====
ny, nz = len(YR), len(ZR)
verts, faces = [], []
for i, y in enumerate(YR):
    ztop = EZ1 + crest(y)
    for j, z in enumerate(ZR):
        # the top row rides the crest; every row below keeps its own z, so the
        # sampled relief does not shear when the rim rises
        zz = ztop if j == nz - 1 else z
        verts.append((EX + edepth(y, zz), y, zz))
for i in range(ny - 1):
    for j in range(nz - 1):
        a = i * nz + j
        faces.append((a, a + 1, a + nz + 1, a + nz))
# cap strip: follows the crest back to x = CAP_X so the shell stays closed
base = len(verts)
verts += [(CAP_X, y, EZ1 + crest(y)) for y in YR]
for i in range(ny - 1):
    a = i * nz + (nz - 1)
    faces.append((a, base + i, base + i + 1, (i + 1) * nz + (nz - 1)))

ob = new_mesh(WALL, verts, faces, mat, COLL)
ds = [edepth(y, z) for y in YR for z in ZR]
cs = [crest(y) for y in YR]
mean_edge = (sum(b - a for a, b, s in [(YR[i], YR[i + 1], 0) for i in range(ny - 1)]) / (ny - 1)
             + (EZ1 - EZ0) / (nz - 1)) / 2.0
print("BUILT %-22s %5d verts %5d polys   y %.1f..%.1f  z %.1f..%.1f(+crest)  "
      "mean edge %.2f m" % (WALL, len(verts), len(faces), EY0, EY1, EZ0, EZ1, mean_edge))
print("   depth east of x=140:  %.2f .. %.2f m   (C2 was a lean and two swells)"
      % (min(ds), max(ds)))
print("   crest above z=26.0 :  %.2f .. %.2f m   (NEVER negative — a dipping rim "
      "would open a background pinhole)" % (min(cs), max(cs)))
ty = math.tan(math.radians(35.0) / 2.0)
for cam, dm, was in (("lockfive", 91.3, 19.88), ("crossing", 88.8, 13.89), ("gate", 163.2, 14.63)):
    print("   px/edge at %-9s d_mean %5.1f m: %3.0f  (was %3.0f at 2.12 m edges; "
          "%.2f%% of frame)" % (cam, dm, mean_edge * (768.0 / (dm * ty)),
                                2.12 * (768.0 / (dm * ty)), was))

json.dump(dict(
    _doc=("GENERATED by tools/t3_cliff_gorge.py — the downstream gorge wall, "
          "resculpted.  Supersedes the wall built by tools/t2_cliff_east.py; that "
          "tool still owns the haze cards and the upstream skirt, and RE-RUNNING IT "
          "WOULD PUT THE FLAT C2 PLANE BACK."),
    generator="tools/t3_cliff_gorge.py", supersedes="tools/t2_cliff_east.py (the wall only)",
    plan="docs/plans/cliff-completion.md", task="#35 user ruling",
    finding=dict(object=WALL, screen_pct=dict(lockfive=19.88, gate=14.63, crossing=13.89),
                 gate_top_left_quadrant_pct=82.4, old_verts=1173, old_edge_m=2.12,
                 old_rim_z=26.0, instrument="tools/t2_probe_leak.py first-opaque tally"),
    wall=dict(name=WALL, plane_x=EX, y=[EY0, EY1], z=[EZ0, EZ1], cap_x=CAP_X,
              ybands=YBANDS, zstep=ZSTEP, verts=len(verts), polys=len(faces),
              mean_edge_m=round(mean_edge, 3),
              depth_m=[round(min(ds), 3), round(max(ds), 3)],
              crest_m=[round(min(cs), 3), round(max(cs), 3)],
              material=MAT, map_scale=MAP_SCALE),
    octaves=OCTAVES, fissures=FISSURES, crests=CRESTS,
    rebake=["gate", "crossing", "lockfive"],
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
