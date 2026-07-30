"""Re-import vesper-v2.glb, assert it is sane, and render the deformation-quality stills.
Blender -b --python-exit-code 1 --python tools/vesper_verify.py -- <glb> <outdir>"""
import bpy, sys, math, os
from mathutils import Vector, Matrix

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
for f in range(0, 33):
    play('Walking_A', f)
    ev, me = evmesh()
    l = sum((me.vertices[i].co for i in LT), Vector()) / len(LT)
    r = sum((me.vertices[i].co for i in RT), Vector()) / len(RT)
    d = abs(l.y - r.y)
    if d > best:
        best, bf = d, f
    ev.to_mesh_clear()
print("Walking_A widest stride at frame %d (toe separation %.3f)" % (bf, best))

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
