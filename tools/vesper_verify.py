"""Re-import vesper-v2.glb, assert it is sane, and render the deformation-quality stills.
Blender -b --python-exit-code 1 --python tools/vesper_verify.py -- <glb> <outdir>

Also enforces the ARM ACCEPTANCE BAR the user set on 2026-07-31 after the "gunslinger"
idle: at the idle each upper arm must hang within IDLE_ARM_MAX deg of vertical, the
elbow must be softly bent (not straight, not folded), and the hands must not be inside
the coat. tools/vesper_arm_probe.py is the same measurement with a per-frame readout."""
import bpy, sys, math, os
from mathutils import Vector, Matrix, kdtree

IDLE_ARM_MAX = 15.0        # deg off vertical, upper arm, at the idle
ELBOW_RANGE = (10.0, 40.0)  # deg of bend -- "softly bent"

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTDIR = argv[0], argv[1]
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=GLB)
for o in list(bpy.data.objects):
    if o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o, do_unlink=True)     # Blender importer artifact, not in the file

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
tris = 0
for m in meshes:
    m.data.calc_loop_triangles(); tris += len(m.data.loop_triangles)
print("meshes:", [(m.name, len(m.data.vertices)) for m in meshes], "tris:", tris)
print("images:", [(i.name, tuple(i.size)) for i in bpy.data.images])
print("bones:", len(arm.data.bones))
acts = sorted(a.name for a in bpy.data.actions)
print("ACTIONS:", [(a.name, tuple(round(v, 1) for v in a.frame_range)) for a in bpy.data.actions])
assert set(acts) == {'Idle', 'Jump_Full_Short', 'Walking_A'}, acts
assert not any(m.name.lower().startswith('icosphere') for m in meshes)
assert len(bpy.data.images) == 3 and all(min(i.size) == 4096 for i in bpy.data.images)

if not arm.animation_data:
    arm.animation_data_create()

def play(name, f):
    a = bpy.data.actions[name]
    arm.animation_data.action = a
    try:
        arm.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    sc.frame_set(f); bpy.context.view_layer.update()

def evmesh():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = meshes[0].evaluated_get(dg)
    return ev, ev.to_mesh()

# pick the widest-stride frame of Walking_A
gi = {n: meshes[0].vertex_groups[n].index for n in ('L_ToeBase', 'R_ToeBase')}
LT = [v.index for v in meshes[0].data.vertices if any(g.group == gi['L_ToeBase'] and g.weight > .5 for g in v.groups)]
RT = [v.index for v in meshes[0].data.vertices if any(g.group == gi['R_ToeBase'] and g.weight > .5 for g in v.groups)]
best, bf = -1, 0
# Read the clip's OWN range: the donors are authored at 24 fps and each walk source has a
# different length (Walk_Loop 0..40 in this 30 fps scene, Jog_Fwd_Loop 0..28), so a
# hard-coded 0..32 either misses the widest-stride frame or scans past the clip's end.
WF0, WF1 = (int(round(v)) for v in bpy.data.actions['Walking_A'].frame_range)
for f in range(WF0, WF1 + 1):
    play('Walking_A', f)
    ev, me = evmesh()
    l = sum((me.vertices[i].co for i in LT), Vector()) / len(LT)
    r = sum((me.vertices[i].co for i in RT), Vector()) / len(RT)
    d = abs(l.y - r.y)
    if d > best:
        best, bf = d, f
    ev.to_mesh_clear()
print("Walking_A frames %d..%d, widest stride at frame %d (toe separation %.3f)"
      % (WF0, WF1, bf, best))

# ---- arm acceptance: hanging arms, soft elbows, hands outside the coat
DOWN = Vector((0, 0, -1))
vg = {n: meshes[0].vertex_groups[n].index for n in meshes[0].vertex_groups.keys()}
def _g(ps):
    return {vg[n] for n in vg if any(p in n for p in ps)}
ARMG = _g(('Upperarm', 'Forearm', 'Hand', 'Clavicle'))
HANDV = {s: [v.index for v in meshes[0].data.vertices
             if any(x.group in _g((s + '_Hand',)) and x.weight > 0.5 for x in v.groups)]
         for s in 'LR'}
BODYV = [v.index for v in meshes[0].data.vertices
         if not any(x.group in ARMG and x.weight > 0.2 for x in v.groups)]

def arm_bones(s, f):
    play('Idle', f)
    h = lambda n: arm.matrix_world @ arm.pose.bones[n].head
    u = (h(s + '_Forearm') - h(s + '_Upperarm')).normalized()
    fo = (h(s + '_Hand') - h(s + '_Forearm')).normalized()
    return u, fo

def hand_clearance(s):
    """Signed: negative means hand vertices are inside the coat/body surface."""
    ev, me = evmesh()
    M, N = meshes[0].matrix_world, meshes[0].matrix_world.to_3x3().inverted().transposed()
    pos = [M @ me.vertices[i].co for i in BODYV]
    nrm = [(N @ me.vertices[i].normal).normalized() for i in BODYV]
    kd = kdtree.KDTree(len(pos))
    for k, p in enumerate(pos):
        kd.insert(p, k)
    kd.balance()
    worst = 1e9
    for i in HANDV[s]:
        p = M @ me.vertices[i].co
        co, idx, d = kd.find(p)
        worst = min(worst, math.copysign(d, (p - co).dot(nrm[idx]) or 1.0))
    ev.to_mesh_clear()
    return worst

IF0, IF1 = (int(round(v)) for v in bpy.data.actions['Idle'].frame_range)
print("\nARM ACCEPTANCE (idle, %d frames)" % (IF1 - IF0 + 1))
for s in 'LR':
    el, eb = [], []
    for f in range(IF0, IF1 + 1):
        u, fo = arm_bones(s, f)
        el.append(math.degrees(u.angle(DOWN)))
        eb.append(math.degrees(fo.angle(u)))
    play('Idle', 0)
    clr = hand_clearance(s)
    print("  %s upper arm off-vertical mean %5.2f  min %5.2f  max %5.2f   elbow bend "
          "%5.1f..%5.1f   hand-vs-coat %+.4f" %
          (s, sum(el) / len(el), min(el), max(el), min(eb), max(eb), clr))
    assert max(el) <= IDLE_ARM_MAX, "%s arm %.1f deg off vertical, bar is %.1f" % (
        s, max(el), IDLE_ARM_MAX)
    assert ELBOW_RANGE[0] <= min(eb) and max(eb) <= ELBOW_RANGE[1], \
        "%s elbow bend %.1f..%.1f outside %s" % (s, min(eb), max(eb), ELBOW_RANGE)
    assert clr > 0, "%s hand is inside the coat by %.4f" % (s, -clr)
    assert max(el) - min(el) > 0.15, "%s idle arm is frozen (no breathing sway)" % s

# ---- render setup
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 520, 700
w = bpy.data.worlds.new("W"); sc.world = w
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.07, 0.08, 0.10, 1)
for e, rot in ((4.0, (55, 0, 35)), (1.6, (60, 0, 210)), (1.2, (110, 0, 180))):
    L = bpy.data.objects.new("L", bpy.data.lights.new("L", 'SUN'))
    sc.collection.objects.link(L); L.data.energy = e
    L.rotation_euler = tuple(math.radians(a) for a in rot)
gnd = bpy.data.meshes.new("g")
gnd.from_pydata([(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [], [(0, 1, 2, 3)])
go = bpy.data.objects.new("ground", gnd); sc.collection.objects.link(go)
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 1.25
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
ctr = Vector((0, 0, 0.49))

def shot(path, view):
    d = Vector((0, -1, 0)) if view == 'front' else Vector((1, 0, 0))
    pos = ctr + d * 10
    up = Vector((0, 0, 1)); fwd = (ctr - pos).normalized()
    z = -fwd; x = up.cross(z).normalized(); y = z.cross(x)
    cam.matrix_world = Matrix(((x.x, y.x, z.x, pos.x), (x.y, y.y, z.y, pos.y),
                               (x.z, y.z, z.z, pos.z), (0, 0, 0, 1)))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

for tag, clip, f in (('idle', 'Idle', 0), ('walk', 'Walking_A', bf)):
    for view in ('front', 'side'):
        play(clip, f)
        shot(os.path.join(OUTDIR, "vesper_v2_%s_%s.png" % (tag, view)), view)
        print("rendered", tag, view, "frame", f)
print("VERIFY OK")
