"""
Retarget KayKit rogue clips (Idle / Walking_A / Jump_Full_Short) onto Vesper's
Tripo auto-rig and export public/assets/characters/vesper/vesper-v2.glb.

Run:  Blender -b --python-exit-code 1 --python tools/vesper_retarget.py -- <fixed.glb> <out.glb>
(<fixed.glb> comes from tools/vesper_fix_glb.py -- the raw Tripo GLB has a broken skin.)

METHOD (no addons, explicit math):
  Both rigs are read in world space. For each donor bone we take its WORLD rotation
  delta from its own rest,  dW = R_pose . R_rest^-1 , and drive the mapped target bone
  to  W_target = dW . T[b]  where T[b] is the target bone's "donor-rest reference
  orientation".

  T[b] matters because the rest poses differ: rogue rests in a T-pose, Vesper rests in
  a near-vertical A-pose (upper arm 69 deg below horizontal). A plain rest-preserving
  retarget would ADD rogue's ~70 deg arms-down idle to her already-down arms and fold
  her arms into her ribs. So for the limb bones T[b] is her rest bone rotated (in
  world, hierarchically) until its anatomical axis matches the donor's rest axis --
  i.e. a virtual T-pose. Nothing is baked into the rest pose, so the mesh binding is
  never touched. Torso/neck bones need no correction (both rigs rest upright) and use
  T[b] = rest.

  Unmapped bones (Root, Pelvis, Waist, clavicles, every *Twist*) keep an identity basis
  and simply inherit -- which is what carries the deformation here, since Tripo put the
  skin weights on the twist bones, not on L_Upperarm/L_Thigh/etc.
"""
import bpy, sys, math, os
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
FIXED, OUT = argv[0], argv[1]
# Optional amplitude damping "legs,arms,torso" (1,1,1 = faithful transfer, the default).
# rogue is an extreme chibi -- head ~60% of his height, legs 17% -- so his stylised
# bounce, transferred at full angle onto a realistically proportioned body, reads as a
# sprint rather than a walk. Damping slerps each bone's world delta back toward the
# donor's OWN idle stance (not toward rest, which would drift the arms out to the
# virtual T-pose), shrinking the swing while keeping the neutral pose intact.
DAMP = [float(x) for x in (argv[2] if len(argv) > 2 else '1,1,1').split(',')]
ROGUE = "/Users/junshernchan/projects/multiplayer-rpg/public/assets/characters3d/rogue.glb"
CLIPS = ['Idle', 'Walking_A', 'Jump_Full_Short']

# ---------------------------------------------------------------- bone map
# Tripo (Vesper)  ->  KayKit (rogue).   Twist chains and the clavicles are absent from
# the donor and are deliberately left to inherit.
BONEMAP = {
    'Hip': 'hips',
    'Spine01': 'spine',
    'Spine02': 'chest',
    'NeckTwist01': 'head', 'NeckTwist02': 'head', 'Head': 'head',
    'L_Upperarm': 'upperarm.l', 'L_Forearm': 'lowerarm.l', 'L_Hand': 'hand.l',
    'R_Upperarm': 'upperarm.r', 'R_Forearm': 'lowerarm.r', 'R_Hand': 'hand.r',
    'L_Thigh': 'upperleg.l', 'L_Calf': 'lowerleg.l', 'L_Foot': 'foot.l', 'L_ToeBase': 'toes.l',
    'R_Thigh': 'upperleg.r', 'R_Calf': 'lowerleg.r', 'R_Foot': 'foot.r', 'R_ToeBase': 'toes.r',
}
# bones whose rest ORIENTATION must be pre-aligned to the donor's rest (the T-pose delta)
ALIGN = {b for b in BONEMAP if any(k in b for k in
         ('Upperarm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'ToeBase'))}
# anatomical direction = head -> this child's head (leaves fall back to the bone axis)
CHILD_T = {'L_Upperarm': 'L_Forearm', 'L_Forearm': 'L_Hand', 'L_Thigh': 'L_Calf',
           'L_Calf': 'L_Foot', 'L_Foot': 'L_ToeBase',
           'R_Upperarm': 'R_Forearm', 'R_Forearm': 'R_Hand', 'R_Thigh': 'R_Calf',
           'R_Calf': 'R_Foot', 'R_Foot': 'R_ToeBase',
           'Spine01': 'Spine02', 'Spine02': 'NeckTwist01'}
CHILD_S = {'upperarm.l': 'lowerarm.l', 'lowerarm.l': 'wrist.l', 'upperleg.l': 'lowerleg.l',
           'lowerleg.l': 'foot.l', 'foot.l': 'toes.l',
           'upperarm.r': 'lowerarm.r', 'lowerarm.r': 'wrist.r', 'upperleg.r': 'lowerleg.r',
           'lowerleg.r': 'foot.r', 'foot.r': 'toes.r',
           'spine': 'chest', 'chest': 'head'}

HIP = 'Hip'
BAKE_PREFIX = 'VESPER__'

def damp_k(tname, clip):
    if clip == 'Idle':
        return 1.0          # the idle IS its departure from the idle stance; damping deadens it
    if any(k in tname for k in ('Thigh', 'Calf', 'Foot', 'ToeBase')):
        return DAMP[0]
    if any(k in tname for k in ('Upperarm', 'Forearm', 'Hand')):
        return DAMP[1]
    return DAMP[2]

# ---------------------------------------------------------------- helpers
def anat_dir(arm, name, childmap):
    """World-space anatomical direction of a rest bone."""
    b = arm.data.bones[name]
    M = arm.matrix_world
    ch = childmap.get(name)
    if ch and ch in arm.data.bones:
        return ((M @ arm.data.bones[ch].head_local) - (M @ b.head_local)).normalized()
    return ((M @ b.tail_local) - (M @ b.head_local)).normalized()

def hier(arm):
    out = []
    def rec(b):
        out.append(b)
        for c in b.children:
            rec(c)
    for b in arm.data.bones:
        if b.parent is None:
            rec(b)
    return out

def rest_rel(b):
    return (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy()

def purge_icospheres():
    for o in list(bpy.data.objects):
        if o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30           # KayKit clips are authored at 30fps; keeps frame ranges integral

bpy.ops.import_scene.gltf(filepath=ROGUE)
src = bpy.data.objects['Rig']
src.name = 'DONOR'
rogue_objs = [o for o in bpy.data.objects if o.type == 'MESH']

bpy.ops.import_scene.gltf(filepath=FIXED)
tgt = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o is not src][0]
vmesh = [o for o in bpy.data.objects if o.type == 'MESH' and o not in rogue_objs
         and not o.name.startswith('Icosphere')]
purge_icospheres()
print("target armature:", tgt.name, "meshes:", [o.name for o in vmesh])
assert src.matrix_world == Matrix.Identity(4) and tgt.matrix_world == Matrix.Identity(4)

# flatten the Tripo RootNode empty away, keep the transform (it is identity)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and not o.children_recursive:
        bpy.data.objects.remove(o, do_unlink=True)
root_empty = [o for o in bpy.data.objects if o.type == 'EMPTY']

sb = src.data.bones
tb = tgt.data.bones
missing = [k for k in BONEMAP if k not in tb] + [v for v in BONEMAP.values() if v not in sb]
assert not missing, "missing bones: %s" % missing

# ---------------------------------------------------------------- report the map
leg_s = ((sb['upperleg.l'].head_local - sb['lowerleg.l'].head_local).length +
         (sb['lowerleg.l'].head_local - sb['foot.l'].head_local).length)
leg_t = ((tb['L_Thigh'].head_local - tb['L_Calf'].head_local).length +
         (tb['L_Calf'].head_local - tb['L_Foot'].head_local).length)
RATIO = leg_t / leg_s
print("\nleg length donor=%.4f target=%.4f  hip-translation ratio=%.4f" % (leg_s, leg_t, RATIO))
print("\n%-13s -> %-12s %-8s donor rest dir        target rest dir       delta" %
      ("TRIPO", "KAYKIT", "align"))
for t, s in sorted(BONEMAP.items()):
    ds = anat_dir(src, s, CHILD_S)
    dt = anat_dir(tgt, t, CHILD_T)
    print("%-13s -> %-12s %-8s (%6.3f,%6.3f,%6.3f)  (%6.3f,%6.3f,%6.3f)  %5.1f deg" %
          (t, s, 'YES' if t in ALIGN else '-', ds.x, ds.y, ds.z, dt.x, dt.y, dt.z,
           math.degrees(ds.angle(dt))))
for t in sorted(b.name for b in tb if b.name not in BONEMAP):
    print("%-13s -> %-12s (inherits)" % (t, '-'))

# ---------------------------------------------------------------- T[]: donor-rest reference
ORDER = hier(tgt)
REL = {b.name: rest_rel(b) for b in ORDER}
T = {}
for b in ORDER:
    base = (T[b.parent.name] @ REL[b.name]) if b.parent else REL[b.name].copy()
    if b.name in ALIGN:
        u = b.matrix_local.to_3x3().inverted() @ anat_dir(tgt, b.name, CHILD_T)   # dir in bone frame
        cur = (base.to_3x3() @ u).normalized()
        want = anat_dir(src, BONEMAP[b.name], CHILD_S)
        Rc = cur.rotation_difference(want).to_matrix()
        m = (Rc @ base.to_3x3()).to_4x4(); m.translation = base.translation
        T[b.name] = m
    else:
        T[b.name] = base
print("\nT-pose reference built; shoulder correction = %.1f deg, hip/torso = %.1f deg" % (
    math.degrees((T['L_Upperarm'].to_3x3().to_quaternion().rotation_difference(
        tb['L_Upperarm'].matrix_local.to_3x3().to_quaternion())).angle),
    math.degrees((T['Hip'].to_3x3().to_quaternion().rotation_difference(
        tb['Hip'].matrix_local.to_3x3().to_quaternion())).angle)))

REST_Q = {b.name: (src.matrix_world @ b.matrix_local).to_quaternion() for b in sb}
SRC_HIP_REST = sb['hips'].matrix_local.translation.copy()
BASE3_HIP = rest_rel(tb[HIP]).to_3x3()   # Hip's parent (Root) never poses, so this is constant

# rest bbox, measured with the rig unposed
def mesh_bbox():
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in vmesh:
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
        ev.to_mesh_clear()
    return mn, mx

# vertices that actually make ground contact, for the per-clip sink check
FOOTG = [vmesh[0].vertex_groups[n].index for n in
         ('L_Foot', 'L_ToeBase', 'R_Foot', 'R_ToeBase') if n in vmesh[0].vertex_groups]
FOOTV = [v.index for v in vmesh[0].data.vertices
         if any(g.group in FOOTG and g.weight > 0.3 for g in v.groups)]

def foot_min_z():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = vmesh[0].evaluated_get(dg); me = ev.to_mesh()
    z = min((vmesh[0].matrix_world @ me.vertices[i].co).z for i in FOOTV)
    ev.to_mesh_clear()
    return z

rmn, rmx = mesh_bbox()
print("\nREST bbox (Blender Z-up) min %s max %s  height=%.4f" %
      (tuple(round(v, 4) for v in rmn), tuple(round(v, 4) for v in rmx), rmx.z - rmn.z))
print("foot-contact vertices: %d" % len(FOOTV))
assert abs(rmn.z) < 1e-3, "rest feet are not on the ground (z=%.4f)" % rmn.z

for pb in tgt.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# damping pivot: the donor's own idle stance
if not src.animation_data:
    src.animation_data_create()
_idle = bpy.data.actions['Idle']
src.animation_data.action = _idle
try:
    src.animation_data.action_slot = _idle.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
DREF = {n: (src.matrix_world @ src.pose.bones[n].matrix).to_quaternion() @ REST_Q[n].inverted()
        for n in set(BONEMAP.values())}
DREF_HIP = src.pose.bones['hips'].matrix.translation - SRC_HIP_REST
IDQ = Quaternion((1, 0, 0, 0))
print("damping (legs,arms,torso) =", DAMP)

def damped(sname, k):
    if k >= 0.999:
        return dW[sname]
    rel = DREF[sname].inverted() @ dW[sname]
    if rel.w < 0:
        rel.negate()
    return DREF[sname] @ IDQ.slerp(rel, k)

# ---------------------------------------------------------------- bake
if not src.animation_data:
    src.animation_data_create()
if not tgt.animation_data:
    tgt.animation_data_create()

made = []
for clip in CLIPS:
    sact = bpy.data.actions.get(clip)
    if sact is None:
        print("!! donor clip missing:", clip); continue
    src.animation_data.action = sact
    try:
        src.animation_data.action_slot = sact.slots[0]
    except Exception:
        pass
    f0, f1 = int(round(sact.frame_range[0])), int(round(sact.frame_range[1]))

    # NB: the donor's own actions are already called Idle/Walking_A/..., so bake under a
    # prefix and rename after the donor is purged -- otherwise actions.new() silently
    # yields "Idle.001", the cleanup pass drops it, and the exporter ships the DONOR's
    # clips (which target rogue bone names) as constant channels. That bug shipped a
    # perfectly static "animated" GLB once already.
    act = bpy.data.actions.new(BAKE_PREFIX + clip)
    act.use_fake_user = True
    tgt.animation_data.action = act
    if getattr(tgt.animation_data, 'action_slot', None) is None:
        try:
            slot = act.slots.new(id_type='OBJECT', name=tgt.name)
        except TypeError:
            slot = act.slots.new('OBJECT', tgt.name)
        tgt.animation_data.action_slot = slot

    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        dW = {}
        for name in set(BONEMAP.values()):
            q = (src.matrix_world @ src.pose.bones[name].matrix).to_quaternion()
            dW[name] = q @ REST_Q[name].inverted()
        raw_hip = src.pose.bones['hips'].matrix.translation - SRC_HIP_REST
        hip_off = (DREF_HIP + (raw_hip - DREF_HIP) * damp_k('L_Thigh', clip)) * RATIO

        W = {}
        for b in ORDER:
            base = (W[b.parent.name] @ REL[b.name]) if b.parent else REL[b.name].copy()
            pb = tgt.pose.bones[b.name]
            if b.name in BONEMAP:
                want3 = damped(BONEMAP[b.name], damp_k(b.name, clip)).to_matrix() @ T[b.name].to_3x3()
                basis3 = base.to_3x3().inverted() @ want3
            else:
                basis3 = Matrix.Identity(3)
            mb = basis3.to_4x4()
            if b.name == HIP:
                mb.translation = base.to_3x3().inverted() @ hip_off
            pb.matrix_basis = mb
            W[b.name] = base @ mb
            if b.name in BONEMAP:
                pb.keyframe_insert('rotation_quaternion', frame=f)
            if b.name == HIP:
                pb.keyframe_insert('location', frame=f)

    # GROUND LOCK: no foot IK here, so the retargeted legs can plant a few mm under the
    # floor. Lift the hips by a constant per clip so the deepest contact frame sits at
    # exactly z=0 -- cheap, keeps the cycle intact, and beats sinking through the road.
    zs = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        zs.append(foot_min_z())
    lift = -min(zs)
    if abs(lift) > 1e-4:
        dl = BASE3_HIP.inverted() @ Vector((0, 0, lift))
        for fc in [c for lay in act.layers for st in lay.strips
                   for cb in st.channelbags for c in cb.fcurves
                   if c.data_path.endswith('.location') and '"%s"' % HIP in c.data_path]:
            for kp in fc.keyframe_points:
                kp.co[1] += dl[fc.array_index]
                kp.handle_left[1] += dl[fc.array_index]
                kp.handle_right[1] += dl[fc.array_index]
            fc.update()
    # the clip must actually MOVE (see the naming note above)
    span = max((max(k.co[1] for k in fc.keyframe_points) -
                min(k.co[1] for k in fc.keyframe_points))
               for lay in act.layers for st in lay.strips for cb in st.channelbags
               for fc in cb.fcurves)
    assert span > 0.01, "%s baked static (max channel span %.5f)" % (clip, span)
    made.append((clip, f0, f1, (f1 - f0) / sc.render.fps))
    print("baked %-18s frames %d..%d  (%.3fs)  foot z %.4f..%.4f  hip lift %+.4f  span %.3f"
          % (clip, f0, f1, (f1 - f0) / sc.render.fps, min(zs), max(zs), lift, span))

# ---------------------------------------------------------------- strip the donor
sc.frame_set(0)
src.animation_data_clear()
for o in rogue_objs + [src]:
    try:
        bpy.data.objects.remove(o, do_unlink=True)
    except ReferenceError:
        pass          # already gone (e.g. purged as an importer Icosphere)
for a in list(bpy.data.actions):
    if not a.name.startswith(BAKE_PREFIX):
        bpy.data.actions.remove(a)
for a in bpy.data.actions:
    a.name = a.name[len(BAKE_PREFIX):]
assert sorted(a.name for a in bpy.data.actions) == sorted(CLIPS), \
    [a.name for a in bpy.data.actions]
for blk in (bpy.data.armatures, bpy.data.meshes, bpy.data.materials, bpy.data.images):
    for x in list(blk):
        if x.users == 0:
            blk.remove(x)
purge_icospheres()
print("\nremaining objects:", [(o.name, o.type) for o in bpy.data.objects])
print("remaining actions:", [a.name for a in bpy.data.actions])
print("remaining images:", [(i.name, tuple(i.size)) for i in bpy.data.images])

# final sanity: unposed rig, feet on the ground
tgt.animation_data.action = None
for pb in tgt.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
mn, mx = mesh_bbox()
print("final REST bbox min %s max %s  height=%.4f" %
      (tuple(round(v, 4) for v in mn), tuple(round(v, 4) for v in mx), mx.z - mn.z))
assert abs(mn.z) < 1e-3

# ---------------------------------------------------------------- export
os.makedirs(os.path.dirname(OUT), exist_ok=True)
kw = dict(filepath=OUT, export_format='GLB', use_selection=False,
          export_apply=False, export_yup=True, export_skins=True,
          export_animations=True, export_animation_mode='ACTIONS',
          export_bake_animation=False, export_optimize_animation_size=False,
          export_optimize_animation_keep_anim_armature=True,
          export_anim_single_armature=True, export_force_keep_channel_for_bones=False,
          export_frame_range=False, export_image_format='AUTO',
          export_texture_dir='', export_morph=False, export_extras=False)
sig = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
kw = {k: v for k, v in kw.items() if k in sig}
bpy.ops.export_scene.gltf(**kw)
print("EXPORTED", OUT, os.path.getsize(OUT), "bytes")
print("CLIPS", made)
