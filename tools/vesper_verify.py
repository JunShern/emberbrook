"""Re-import vesper-v2.glb, assert it is sane, and render the deformation-quality stills.
Blender -b --python-exit-code 1 --python tools/vesper_verify.py -- <glb> <outdir>

Also enforces the ARM ACCEPTANCE BAR the user set on 2026-07-31 after the "gunslinger"
idle: at the idle each upper arm must hang within IDLE_ARM_MAX deg of vertical, the
elbow must be softly bent (not straight, not folded), and the hands must not be inside
the coat. tools/vesper_arm_probe.py is the same measurement with a per-frame readout.

THE IDLE BARS ARE FOR A BODY STANDING STILL, AND THEY WERE NOT WIDENED FOR COMBAT
(2026-08-02, the combat-clips lane). Attack / Hit_A / Death_A legitimately violate every
one of them -- an upper arm 15 deg from vertical through a sword swing is not a swing,
and a head held level through a death is not a death. The temptation was to relax
IDLE_ARM_MAX until the new clips fit, which would have deleted the gate that caught the
gunslinger idle in the first place. Instead:

    * the arm / elbow / hand-vs-coat bars stay EXACTLY as they were and are asserted on
      Idle ONLY -- the clip they were written about;
    * the head-pitch bar stays exactly as it was and is asserted on the three LOCOMOTION
      clips -- Idle, Walking_A, Jump_Full_Short -- for the same reason;
    * the combat clips get their own five bars (see THE COMBAT GATE), which assert the
      things that are actually true of a good strike and false of a bad one.

An honest new bar beats a widened old one, and the load-bearing one of the five is G1:
it asserts the clip leaves the idle envelope, so "the body slid forward on its idle
pose" -- the defect this whole lane exists to fix -- can never silently come back.

COMBAT CONTACT SHEET (2026-08-02):  ... -- <glb> <outdir> sheet=side,front sheetn=8
Renders every combat clip as an evenly-spaced strip per view, because no number in this
file can see a performance and a clip that passes all five bars can still read as a
seizure. Off by default.

VARIANTS MODE (added 2026-08-01):  ... -- <glb> <outdir> variants
Runs the SAME three gates over EVERY action in the file and prints a variant x gate
table instead of asserting, for the posture/run ladder in anim_test.glb. It reports
rather than fails on purpose: a rung that misses the bar is a DATA POINT the user is
choosing against, not a broken build, and the gates themselves are up for re-derivation
once a winner is picked. It skips the renders and the 3-action runtime contract."""
import bpy, sys, math, os
from mathutils import Vector, Matrix, kdtree

IDLE_ARM_MAX = 15.0        # deg off vertical, upper arm, at the idle
ELBOW_RANGE = (10.0, 40.0)  # deg of bend -- "softly bent"

# ---- THE P3 EXCEPTION (2026-08-01, user ruling; see vesper_retarget's TASTE RULINGS)
# The user picked posture P3 -- arms hanging naturally at the sides -- after A/B'ing it
# against the gate-clean F3 and rejecting F3 as unnatural. P3 costs two of the three
# gates: the elbow straightens past the 10 deg "softly bent" floor, and the hands enter
# the coat. THE GATES ARE WAIVED, NOT DELETED. Each is re-pinned to the pose the user
# actually chose, with a margin, so the assert still catches a REGRESSION past it --
# which is the entire reason the gate exists. A waived gate that stops asserting stops
# detecting, and this project has already paid for one of those.
# strict=1 restores the pre-ruling bars (the F ladder passes those; P3 does not).
ELBOW_MIN_P3 = 2.0         # P3 measures 2.8 at its straightest
CLEAR_FLOOR_P3 = -0.045    # P3 measures -0.0387 at its deepest

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTDIR = argv[0], argv[1]
VARIANTS = 'variants' in argv[2:]
STRICT = 'strict=1' in argv[2:]
OPT = dict(a.split('=', 1) for a in argv[2:] if '=' in a)
if not STRICT:
    ELBOW_RANGE = (ELBOW_MIN_P3, ELBOW_RANGE[1])
CLEAR_FLOOR = 0.0 if STRICT else CLEAR_FLOOR_P3
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
# THE RUNTIME CONTRACT. LOCO is play3d.html's (the overworld body); COMBAT is
# battle_stage3d.js's CLIP table, which matches these three names EXACTLY -- so the
# arena picks them up with no edit and its procedural swing stands itself down.
LOCO = ['Idle', 'Walking_A', 'Jump_Full_Short']
COMBAT = ['Attack', 'Hit_A', 'Death_A']
# THE PERFORMANCE SET (2026-08-08, the battle-cast lane). battle_stage3d's CLIP table
# asks for SIX intents -- idle, attack, hit, die, item, cheer -- and the shipped rigs
# bound four, so the game's victory pose was the party standing in their idles. These
# two are the other two, and they go through the SAME gate the combat clips do: a clip
# that never leaves the idle envelope is the defect, whatever it is called.
PERF = ['Cheer', 'Use_Item']
GATED = COMBAT + PERF          # every clip that moves, held to THE COMBAT GATE below
assert VARIANTS or set(acts) == set(LOCO) | set(GATED), acts
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
# (Variants mode has no clip called Walking_A -- it picks its own frames.)
if not VARIANTS:
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

def arm_bones(s, f, clip='Idle'):
    play(clip, f)
    h = lambda n: arm.matrix_world @ arm.pose.bones[n].head
    u = (h(s + '_Forearm') - h(s + '_Upperarm')).normalized()
    fo = (h(s + '_Hand') - h(s + '_Forearm')).normalized()
    return u, fo

def hand_clearance_both():
    """Both sides off ONE KD-tree of the current frame -- the tree costs ~20k inserts
    and the variant sweep pays it 200+ times, so build it once and query twice."""
    ev, me = evmesh()
    M, N = meshes[0].matrix_world, meshes[0].matrix_world.to_3x3().inverted().transposed()
    pos = [M @ me.vertices[i].co for i in BODYV]
    nrm = [(N @ me.vertices[i].normal).normalized() for i in BODYV]
    kd = kdtree.KDTree(len(pos))
    for k, p in enumerate(pos):
        kd.insert(p, k)
    kd.balance()
    out = {}
    for s in 'LR':
        worst = 1e9
        for i in HANDV[s]:
            p = M @ me.vertices[i].co
            co, idx, d = kd.find(p)
            worst = min(worst, math.copysign(d, (p - co).dot(nrm[idx]) or 1.0))
        out[s] = worst
    ev.to_mesh_clear()
    return out

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

if VARIANTS:
    # ---- the variant x gate table. Same three gates, reported not asserted.
    # Bone angles are read on EVERY frame (cheap: pose-bone heads). Hand-vs-coat needs
    # an evaluated 92k-tri mesh plus a KD-tree, so it is sampled on up to SAMPLES frames
    # spread across the clip -- stated, because a sampled minimum can miss a one-frame
    # dip (the shipped jog has exactly one such frame, f15 of 29). Read the clearance
    # column as "no contact on the sampled frames", not "no contact anywhere".
    SAMPLES = 12
    HEADB = 'Head' if 'Head' in arm.pose.bones else None
    print("\nVARIANT x GATE  (arm<=%.0f deg off vertical | elbow %.0f-%.0f deg | "
          "hand-vs-coat > 0; clearance sampled on <=%d frames)"
          % (IDLE_ARM_MAX, ELBOW_RANGE[0], ELBOW_RANGE[1], SAMPLES))
    print("%-9s %5s  %-21s %-21s %-19s %s"
          % ('clip', 'frms', 'upper arm off-vert L/R', 'elbow bend L/R',
             'hand-coat min L/R', 'gates'))
    rows = []
    for name in acts:
        a = bpy.data.actions[name]
        f0, f1 = (int(round(v)) for v in a.frame_range)
        el = {s: [] for s in 'LR'}
        eb = {s: [] for s in 'LR'}
        for f in range(f0, f1 + 1):
            for s in 'LR':
                u, fo = arm_bones(s, f, name)
                el[s].append(math.degrees(u.angle(DOWN)))
                eb[s].append(math.degrees(fo.angle(u)))
        step = max(1, (f1 - f0 + 1) // SAMPLES)
        clr = {s: 1e9 for s in 'LR'}
        for f in range(f0, f1 + 1, step):
            play(name, f)
            c = hand_clearance_both()
            for s in 'LR':
                clr[s] = min(clr[s], c[s])
        g_arm = max(max(el[s]) for s in 'LR') <= IDLE_ARM_MAX
        g_elb = all(ELBOW_RANGE[0] <= min(eb[s]) and max(eb[s]) <= ELBOW_RANGE[1] for s in 'LR')
        g_clr = min(clr['L'], clr['R']) > 0
        rows.append((name, g_arm, g_elb, g_clr))
        print("%-9s %5d  %5.1f..%-5.1f %5.1f..%-5.1f  %5.1f..%-5.1f %5.1f..%-5.1f  "
              "%+7.4f %+7.4f  %s%s%s"
              % (name, f1 - f0 + 1, min(el['L']), max(el['L']), min(el['R']), max(el['R']),
                 min(eb['L']), max(eb['L']), min(eb['R']), max(eb['R']),
                 clr['L'], clr['R'],
                 'ARM ' if g_arm else 'arm!', 'ELB ' if g_elb else 'elb!',
                 'CLR' if g_clr else 'clr!'))
    print("\nGATE SUMMARY (uppercase = pass)")
    for n, a_, e_, c_ in rows:
        print("  %-9s arm %-4s elbow %-4s clearance %-4s  %s"
              % (n, 'PASS' if a_ else 'FAIL', 'PASS' if e_ else 'FAIL',
                 'PASS' if c_ else 'FAIL',
                 'ALL PASS' if (a_ and e_ and c_) else '--'))
    print("VARIANT TABLE OK")
    sys.exit(0)

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
    assert clr > CLEAR_FLOOR, \
        "%s hand-vs-coat %+.4f is past the pinned floor %+.4f -- that is a REGRESSION " \
        "beyond the P3 pose the user ruled for, not the ruling itself" % (s, clr, CLEAR_FLOOR)
    assert max(el) - min(el) > 0.15, "%s idle arm is frozen (no breathing sway)" % s

# ---- HEAD PITCH GATE (2026-08-01). The complaint that started the lock was "heads
# always downturned", and it was the donor's pitch transferred verbatim (-12.7 deg at
# the idle, -20.7 at the walk, IDENTICAL on Vesper and Finn -- which is what proved it
# was the donor and not the model). Nothing else in this file would notice it coming
# back, so it gets its own bar. 0 = the rest orientation the A-pose turnaround was drawn
# at; the idle's own breathing sway is +-2.2, so 5 deg is sway plus margin.
HEAD_PITCH_MAX = 5.0
FWD = Vector((0, -1, 0))
_hu = (arm.matrix_world @ arm.data.bones['Head'].matrix_local).to_3x3().inverted() @ FWD
# LOCOMOTION ONLY. A combat clip's head arc IS the performance -- Death_A ends looking
# at the sky because the body is on its back -- so this bar would be measuring the
# animation, not the defect. The defect it protects against (the donor's -12.7 deg
# neutral downturn, transferred verbatim) is a property of the DONOR'S NEUTRAL, and the
# combat clips are solved from exactly that neutral (vesper_retarget COMBAT CLIPS §2),
# so Idle passing this bar is what proves the correction was applied to all six.
print("\nHEAD PITCH (0 = rest/level, negative = looking down; bar +-%.1f)" % HEAD_PITCH_MAX)
for clip in LOCO:
    C0, C1 = (int(round(v)) for v in bpy.data.actions[clip].frame_range)
    ps = []
    for f in range(C0, C1 + 1):
        play(clip, f)
        v = (arm.matrix_world @ arm.pose.bones['Head'].matrix).to_3x3() @ _hu
        ps.append(math.degrees(math.asin(max(-1.0, min(1.0, v.normalized().z)))))
    print("  %-16s mean %+5.1f  min %+5.1f  max %+5.1f" %
          (clip, sum(ps) / len(ps), min(ps), max(ps)))
    assert abs(sum(ps) / len(ps)) <= HEAD_PITCH_MAX, \
        "%s head pitch mean %+.1f deg, bar is +-%.1f -- the downturn is back" % (
            clip, sum(ps) / len(ps), HEAD_PITCH_MAX)

# ======================================================================= THE COMBAT GATE
# (2026-08-02, the combat-clips lane. Read the note at the top of this file first: the
# idle bars above were NOT widened to let these through, they were scoped to the clip
# they describe, and these five are what replaces them for a clip that moves.)
#
# G1  IT MUST ACTUALLY SWING.  The inverse of the idle bar, and the reason this gate
#     exists at all. Before these clips the party's attack was a body sliding forward on
#     its idle pose; a clip that never leaves the idle arm envelope IS that bug. So the
#     attack's peak upper-arm elevation must EXCEED the idle bar by a wide margin and the
#     arm must travel. Hit_A is a flinch, not a strike, and is held to a smaller travel.
# G2  NO SEIZURE.  Max frame-to-frame rotation of any single limb axis, and the bar is
#     the SAMPLE RATE, not a guess about anatomy. The first draft barred 45 deg/frame on
#     the reasoning that 1350 deg/s is past what a human limb does; the sword strike's
#     forearm measured 74.5 and the reasoning was simply wrong -- a shoulder does not
#     move that fast, a wrist in a cut does. The principled bar is that a rotation of
#     more than 90 deg between two 30 fps samples cannot be RECONSTRUCTED: three.js
#     slerps the short arc between keys, so past a quarter turn the runtime either shows
#     a jump or takes the wrong way round, and the two are indistinguishable from the
#     transfer's real failure mode (a quaternion that flipped sign, which lands near
#     180). Under 90 the motion is unambiguous however fast it is.
# G3  IT MUST COME HOME.  Attack and Hit_A are one-shots the stage crossfades back to
#     Idle over 0.2 s, so their last frame must sit near their first or the body snaps.
#     The bar is what that fade can ABSORB: 20 deg per axis over 200 ms is 100 deg/s, a
#     settle nobody sees; 60 would be 300 deg/s and would read as a snap.
#     Death_A is EXEMPT and that is the point of a death: it holds its last frame.
# G4  FEET ON THE GROUND.  The retarget's ground lock puts the deepest contact frame at
#     z=0; this catches the other end -- a body hovering through its own strike. Death_A
#     is exempt (Death01 kicks a leg up as it falls back, measured toe z 0.55).
# G5  HAND-VS-COAT, READ ONLY WHERE THE INSTRUMENT CAN BE READ.  A swing brings the hand
#     across the body and some penetration is unavoidable -- the P3 ruling already waived
#     this at the idle. The floor is deliberately loose: it is not "is the swing clean",
#     it is "is an arm buried through the torso", a broken transfer and not a pose.
#
#     THE FIRST DRAFT OF THIS BAR WAS WRONG AND FAILED FIVE OF THE SIX RIGS ON A DEFECT
#     THAT IS NOT THERE (2026-08-02, corrected the same day). hand_clearance_both()
#     returns the distance to the NEAREST BODY VERTEX, signed by that vertex's NORMAL.
#     The distance is sound at any range; the SIGN is only meaningful while the hand is
#     near the surface, because the nearest vertex of a far-away hand is some arbitrary
#     patch of body pointing wherever it happens to point. That was already measured and
#     written down on the lake retarget -- DAYLOG 2026-08-02, "read this metric's sign
#     only at |d| < ~0.05" -- and this gate read it at arm's length anyway.
#
#     MEASURED AGAIN HERE, finn's Attack, EVERY frame, right hand:
#         f10 +0.183   f11 -0.294   f12 -0.340   f13 +0.209
#     The MAGNITUDE is continuous and the SIGN flickers. A hand does not enter and leave
#     a body 340 mm deep in two frames, and 340 mm is deeper than the body is thick.
#     RENDERED AND LOOKED AT (scratchpad finn_attack_f12): f12 is the frame where both
#     arms are flung WIDEST, hands in clear air -- the worst "burial" in the clip is the
#     moment of GREATEST clearance. The whole clip's closest approach is +0.0656.
#
#     SO: the sign is read only inside CLEAR_VALID_R, and the CLOSEST APPROACH (min |d|)
#     is printed beside it, because that is the number that actually answers "did a hand
#     ever go near the body". A clip whose hand never enters the domain never touched the
#     body, and passes on that fact rather than on a waiver. Sampled on EVERY frame, not
#     the 10 the first draft used: a crossing of the surface is what the gate is looking
#     for, and it is exactly what a coarse sample steps over.
SWING_ARM_MIN = 60.0     # deg off vertical the attack's peak upper arm must exceed
# G1's travel bar is PER CLIP because the beats are not the same size: a strike throws
# the arm, a flinch does not, and a drink lifts one hand. Each is pinned just under the
# clip's own MEASURED travel (see the numbers in DAYLOG 2026-08-08), so the bar catches a
# transfer that collapsed the motion and does not encode a wish about how big it should be.
SWING_TRAVEL = {'Attack': 40.0, 'Hit_A': 8.0, 'Death_A': 40.0,
                'Cheer': 60.0, 'Use_Item': 24.0}   # deg of peak-to-trough
MAX_STEP = 90.0          # deg, one limb axis, one frame @30fps -- the reconstruction limit
RETURN_MAX = 20.0        # deg per axis, mean over the 8 axes, last frame vs first
FOOT_CEIL = 0.30         # m, highest a foot-contact vertex may go (a step, not a leap)
COMBAT_CLEAR_FLOOR = -0.090   # m, hand vertices inside the body surface
CLEAR_VALID_R = 0.050    # m, the radius inside which this metric's SIGN is real (see G5)

AXES = [('%s_Upperarm', '%s_Forearm'), ('%s_Forearm', '%s_Hand'),
        ('%s_Thigh', '%s_Calf'), ('%s_Calf', '%s_Foot')]
AXNAME = ['%s %s' % (s, n) for s in 'LR' for n in ('upper', 'fore', 'thigh', 'shin')]
FOOTG = {vg[n] for n in ('L_Foot', 'L_ToeBase', 'R_Foot', 'R_ToeBase') if n in vg}
FOOTV = [v.index for v in meshes[0].data.vertices
         if any(x.group in FOOTG and x.weight > 0.3 for x in v.groups)]

def limb_axes():
    """The 8 axes G2/G3 are measured on, at the current frame."""
    h = lambda n: arm.matrix_world @ arm.pose.bones[n].head
    return [(h(b % s) - h(a % s)).normalized() for s in 'LR' for a, b in AXES]

def foot_z():
    ev, me = evmesh()
    M = meshes[0].matrix_world
    zs = [(M @ me.vertices[i].co).z for i in FOOTV]
    ev.to_mesh_clear()
    return min(zs), max(zs)

print("\nTHE COMBAT GATE  (swing>=%.0f | step<=%.0f | return<=%.0f | foot<=%.2f | "
      "hand>=%+.3f)" % (SWING_ARM_MIN, MAX_STEP, RETURN_MAX, FOOT_CEIL, COMBAT_CLEAR_FLOOR))
for clip in GATED:
    a = bpy.data.actions[clip]
    C0, C1 = (int(round(v)) for v in a.frame_range)
    el = {s: [] for s in 'LR'}
    seq, fzmin, fzmax = [], 1e9, -1e9
    for f in range(C0, C1 + 1):
        play(clip, f)
        ax = limb_axes()
        seq.append(ax)
        el['L'].append(math.degrees(ax[0].angle(DOWN)))
        el['R'].append(math.degrees(ax[4].angle(DOWN)))
        lo, hi = foot_z()
        fzmin, fzmax = min(fzmin, lo), max(fzmax, hi)
    step, stepat = max(((math.degrees(x.angle(y)), (AXNAME[k], C0 + i))
                        for i in range(len(seq) - 1)
                        for k, (x, y) in enumerate(zip(seq[i], seq[i + 1]))))
    ret = sum(math.degrees(x.angle(y)) for x, y in zip(seq[-1], seq[0])) / len(seq[0])
    peak = max(max(el[s]) for s in 'LR')
    travel = max(max(el[s]) - min(el[s]) for s in 'LR')
    # HAND-VS-COAT, every frame, sign read only inside CLEAR_VALID_R -- see G5.
    # `near` is every reading the sign can be trusted on; `approach` is the closest the
    # hand ever gets to the body, which is signless and therefore always readable.
    near, approach, far = [], 1e9, 0
    for f in range(C0, C1 + 1):
        play(clip, f)
        c = hand_clearance_both()
        for s in 'LR':
            approach = min(approach, abs(c[s]))
            if abs(c[s]) < CLEAR_VALID_R:
                near.append(c[s])
            elif c[s] < 0:
                far += 1              # a negative the sign cannot carry: counted, not used
    clr = min(near) if near else None
    print("  %-8s %2d frames %.3fs | upper arm %5.1f..%5.1f (travel %5.1f) | max step "
          "%5.1f (%s f%d) | return %5.1f | foot z %+.3f..%+.3f | hand closest %.4f, "
          "in-domain worst %s%s"
          % (clip, C1 - C0 + 1, (C1 - C0) / 30.0, min(min(el[s]) for s in 'LR'), peak,
             travel, step, stepat[0], stepat[1], ret, fzmin, fzmax, approach,
             ('%+.4f' % clr) if near else 'n/a (never near the body)',
             (' [%d out-of-domain negatives discarded]' % far) if far else ''))
    if clip == 'Attack':
        assert peak >= SWING_ARM_MIN, (
            "G1: %s peaks at %.1f deg off vertical, bar is %.1f. An attack that stays "
            "inside the idle envelope is the 'body sliding forward on its idle pose' "
            "bug this clip exists to fix." % (clip, peak, SWING_ARM_MIN))
    assert travel >= SWING_TRAVEL[clip], \
        "G1: %s upper arm travels only %.1f deg, bar is %.1f" % (clip, travel, SWING_TRAVEL[clip])
    assert step <= MAX_STEP, (
        "G2: %s moves a limb axis %.1f deg in one frame (%.0f deg/s), bar is %.1f. That "
        "is not a fast strike, it is a flipped quaternion." % (clip, step, step * 30, MAX_STEP))
    if clip != 'Death_A':
        assert ret <= RETURN_MAX, (
            "G3: %s ends %.1f deg/axis from where it started, bar is %.1f -- the "
            "crossfade back to Idle would snap." % (clip, ret, RETURN_MAX))
        assert fzmax <= FOOT_CEIL, \
            "G4: %s lifts a foot to z=%.3f, ceiling is %.2f" % (clip, fzmax, FOOT_CEIL)
    assert abs(fzmin) < 0.02, \
        "G4: %s deepest foot contact is z=%+.4f, the ground lock should put it at 0" % (clip, fzmin)
    assert clr is None or clr > COMBAT_CLEAR_FLOOR, (
        "G5: %s buries a hand %+.4f into the body, floor is %+.4f. This one IS readable: "
        "it is inside the %.3f m radius where the nearest-vertex sign means something."
        % (clip, clr, COMBAT_CLEAR_FLOOR, CLEAR_VALID_R))
print("COMBAT GATE OK")

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

# ---- THE COMBAT CONTACT SHEET  (sheet=front,side  sheetn=<frames per clip>)
# The numbers above cannot see a performance. A clip can pass all five combat bars and
# still read as a seizure, so every combat clip is rendered as an evenly-spaced strip
# per requested view and LOOKED AT before anything ships. Frames go out as separate
# PNGs; scratchpad stitching turns each clip into one row. Off by default -- the gate is
# the cheap thing to run, the sheet is the thing a person has to sit and watch.
SHEET = [v for v in OPT.get('sheet', '').split(',') if v]
SHEET_N = int(OPT.get('sheetn', '8'))
if SHEET:
    sc.render.resolution_x, sc.render.resolution_y = 400, 540
    for clip in GATED:
        C0, C1 = (int(round(v)) for v in bpy.data.actions[clip].frame_range)
        frames = [C0 + round(i * (C1 - C0) / (SHEET_N - 1)) for i in range(SHEET_N)]
        for view in SHEET:
            for i, f in enumerate(frames):
                play(clip, f)
                shot(os.path.join(OUTDIR, "sheet_%s_%s_%02d.png" % (clip, view, i)), view)
            print("sheet %-8s %-5s frames %s" % (clip, view, frames))
print("VERIFY OK")
