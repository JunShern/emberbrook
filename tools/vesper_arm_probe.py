"""
ARM INSTRUMENT: measure, in world space, where a character's arms actually are.

    Blender -b --python-exit-code 1 --python tools/vesper_arm_probe.py -- <glb> [clip[,clip...]]

For every frame of every clip it prints, per side:
  elev  = angle of the UPPER ARM axis (shoulder -> elbow) away from straight DOWN.
          0 deg = hanging vertically. This is the number the idle is judged on.
  abd   = the part of that angle in the coronal (side-to-side) plane -- "winging out".
  fwd   = the part in the sagittal plane, + = elbow forward (arm swing).
  elbow = angle between upper arm and forearm, 0 = straight.
  hand  = world position of the hand bone head.
  clr   = SIGNED clearance of the hand (hand-weighted vertices only -- the sleeve
          resting against the coat is not a defect) against the coat/body surface:
          the nearest non-arm vertex's outward normal decides the sign, so
          negative = the hand is INSIDE the coat. Body height is 0.9785 Blender
          units == 1.45 m in game, so 0.001 here is ~1.5 mm on screen.

Works on both rigs: Tripo/Vesper (L_Upperarm/L_Forearm/L_Hand) and KayKit/rogue
(upperarm.l/lowerarm.l/hand.l), so the donor's own envelope can be measured with the
same instrument as the retarget's.
"""
import bpy, sys, math, os
from mathutils import Vector, kdtree

argv = sys.argv[sys.argv.index('--') + 1:]
GLB = argv[0]
WANT = argv[1].split(',') if len(argv) > 1 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=GLB)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o, do_unlink=True)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
B = {b.name for b in arm.data.bones}

TRIPO = ('L_Upperarm', 'L_Forearm', 'L_Hand', 'R_Upperarm', 'R_Forearm', 'R_Hand')
KAY = ('upperarm.l', 'lowerarm.l', 'hand.l', 'upperarm.r', 'lowerarm.r', 'hand.r')
NAMES = TRIPO if set(TRIPO) <= B else KAY
assert set(NAMES) <= B, "no known arm chain in %s" % sorted(B)
SIDES = {'L': NAMES[0:3], 'R': NAMES[3:6]}
print("rig:", arm.name, "arm chain:", NAMES)

# hand vertices (for the coat-clearance probe) -- only on the Vesper rig
HANDV, OTHERV = {}, None
if NAMES is TRIPO and meshes:
    mo = max(meshes, key=lambda m: len(m.data.vertices))
    gi = {n: mo.vertex_groups[n].index for n in mo.vertex_groups.keys()}
    def group_ids(prefixes):
        return {gi[n] for n in gi if any(p in n for p in prefixes)}
    for s, (_, fa, ha) in SIDES.items():
        g = group_ids((ha,))
        HANDV[s] = [v.index for v in mo.data.vertices
                    if any(x.group in g and x.weight > 0.5 for x in v.groups)]
    armg = group_ids(('Upperarm', 'Forearm', 'Hand', 'Clavicle'))
    OTHERV = [v.index for v in mo.data.vertices
              if not any(x.group in armg and x.weight > 0.2 for x in v.groups)]
    print("hand+forearm verts L/R:", [len(HANDV[s]) for s in 'LR'], "torso verts:", len(OTHERV))

DOWN = Vector((0, 0, -1))
OUT = {'L': Vector((-1, 0, 0)), 'R': Vector((1, 0, 0))}   # +X is her LEFT? resolved below


def head(name):
    return arm.matrix_world @ arm.pose.bones[name].head


_KD = [None, None]      # (kdtree, positions, normals) rebuilt per frame


def body_kd(mo):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mo.evaluated_get(dg); me = ev.to_mesh()
    M = mo.matrix_world
    N = M.to_3x3().inverted().transposed()
    pos = [M @ me.vertices[i].co for i in OTHERV]
    nrm = [(N @ me.vertices[i].normal).normalized() for i in OTHERV]
    kd = kdtree.KDTree(len(pos))
    for k, p in enumerate(pos):
        kd.insert(p, k)
    kd.balance()
    hand = {s: [M @ me.vertices[i].co for i in HANDV[s]] for s in HANDV}
    ev.to_mesh_clear()
    return kd, pos, nrm, hand


def clearance(side, mo):
    """Signed distance of the hand to the coat: negative = inside the garment."""
    if OTHERV is None or not HANDV.get(side):
        return float('nan')
    kd, pos, nrm, hand = _KD[0]
    worst = 1e9
    for p in hand[side]:
        co, idx, d = kd.find(p)
        s = (p - co).dot(nrm[idx])
        worst = min(worst, math.copysign(d, s if abs(s) > 1e-9 else 1.0))
    return worst


def measure(side, with_clear=False):
    up, fo, ha = SIDES[side]
    a = head(up); b = head(fo); c = head(ha)
    v = (b - a)
    axis = v.normalized()
    elev = math.degrees(axis.angle(DOWN))
    # decompose: abduction = lateral tilt, flexion = fore/aft tilt
    abd = math.degrees(math.atan2(axis.x, -axis.z))
    fwd = math.degrees(math.atan2(-axis.y, -axis.z))
    elbow = math.degrees((c - b).angle(v)) if (c - b).length > 1e-6 else 0.0
    clr = clearance(side, max(meshes, key=lambda m: len(m.data.vertices))) if with_clear else float('nan')
    return dict(elev=elev, abd=abd, fwd=fwd, elbow=elbow, hand=c, clr=clr, axis=axis)


if not arm.animation_data:
    arm.animation_data_create()
acts = [a for a in bpy.data.actions if WANT is None or a.name in WANT]
print("clips:", [a.name for a in acts])

for act in acts:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    print("\n=== %s  frames %d..%d ===" % (act.name, f0, f1))
    print("%5s | %-38s | %-38s" % ('frame', 'LEFT  elev  abd  fwd elbow  clr',
                                   'RIGHT elev  abd  fwd elbow  clr'))
    stats = {s: [] for s in 'LR'}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        if OTHERV is not None:
            _KD[0] = body_kd(max(meshes, key=lambda m: len(m.data.vertices)))
        row = ""
        for s in 'LR':
            m = measure(s, with_clear=True)
            stats[s].append(m)
            row += "| %5.1f %5.1f %5.1f %5.1f %6.4f " % (m['elev'], m['abd'], m['fwd'],
                                                         m['elbow'], m['clr'])
        print("%5d %s" % (f, row))
    for s in 'LR':
        e = [m['elev'] for m in stats[s]]
        c = [m['clr'] for m in stats[s]]
        b = [m['elbow'] for m in stats[s]]
        # EXCURSION is the max angle between a frame's arm axis and the clip's mean axis.
        # Unlike elev it is invariant under any constant rotation of the whole arm, so it
        # is the honest measure of "is the motion still there" after a shoulder offset.
        mean = Vector()
        for m in stats[s]:
            mean += m['axis']
        mean.normalize()
        exc = max(math.degrees(m['axis'].angle(mean)) for m in stats[s])
        print("  %s: elev mean %6.2f  min %6.2f  max %6.2f   excursion %5.2f   "
              "elbow %5.1f..%5.1f   clr min %.4f"
              % (s, sum(e) / len(e), min(e), max(e), exc, min(b), max(b), min(c)))
print("PROBE OK")
