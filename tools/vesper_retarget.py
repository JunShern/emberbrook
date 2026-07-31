"""
Retarget donor clips onto Vesper's Tripo auto-rig and export a vesper GLB with the
three runtime clips  Idle / Walking_A / Jump_Full_Short.

Run:  Blender -b --python-exit-code 1 --python tools/vesper_retarget.py -- <fixed.glb> <out.glb> [k=v ...]
(<fixed.glb> comes from tools/vesper_fix_glb.py -- the raw Tripo GLB has a broken skin.)
Options (all optional, k=v):  damp=1,1,1   idle=Idle_Loop   walk=Jog_Fwd_Loop   stance=on|off
                              armhang=U_abd,U_fwd,F_abd,F_fwd  (re-shoot the arm hang on
                              EVERY clip at once -- see PER-CLIP ARM HANG)

METHOD (no addons, explicit math):
  Both rigs are read in world space. For each donor bone we take its WORLD rotation
  delta from its own rest,  dW = R_pose . R_rest^-1 , and drive the mapped target bone
  to  W_target = dW . T[b]  where T[b] is the target bone's "donor-rest reference
  orientation".

  T[b] matters because the rest poses differ: the donors rest in a T-pose, Vesper rests
  in a near-vertical A-pose (upper arm 69 deg below horizontal). A plain rest-preserving
  retarget would ADD the donor's ~70 deg arms-down idle to her already-down arms and fold
  her arms into her ribs. So for the limb bones T[b] is her rest bone rotated (in
  world, hierarchically) until its anatomical axis matches the donor's rest axis --
  i.e. a virtual T-pose. Nothing is baked into the rest pose, so the mesh binding is
  never touched. Torso/neck bones need no correction (both rigs rest upright) and use
  T[b] = rest.

  Unmapped bones (Root, Pelvis, Waist, clavicles, every *Twist*) keep an identity basis
  and simply inherit -- which is what carries the deformation here, since Tripo put the
  skin weights on the twist bones, not on L_Upperarm/L_Thigh/etc.

DONOR SWAP: PER-CLIP DONORS (added 2026-07-31, late; supersedes the single-donor script)
  The user, having had to flag the idle twice (arms, then legs), ruled: stop patching
  incrementally, get a donor whose neutral fits her. So the donor is no longer one file:
  each clip names its own source, and everything donor-shaped -- bone map, anatomical
  child map, rest quaternions, the virtual-T reference T[], the leg-length ratio that
  scales hip translation, the damping pivot -- is now computed PER DONOR.

      Idle             <- Quaternius Universal Animation Library  'Idle_Loop'  (CC0)
      Walking_A        <- Quaternius UAL                          'Jog_Fwd_Loop'
      Jump_Full_Short  <- KayKit rogue                            'Jump_Full_Short'

  (UAL has no full jump arc, only Start/Loop/Land, so the jump stays on KayKit.)

  WHY THE JOG AND NOT THE WALK (2026-07-31, the ship candidate). The runtime moves her at
  4.5 units/s. Measured on the BAKED clips (toe fore-aft travel per cycle, scaled to the
  in-game 1.45-unit model -- scratchpad/stride.py):

      Walk_Loop     0.46 u/s      Jog_Fwd_Loop  1.17 u/s      (KayKit walk, shipped: 0.62)

  Every clip under-runs the controller, so the runtime has to scale SOME clip up; the
  question is only which one is asked to stretch. The walk needs ~10x, the jog ~4x. A walk
  cycle stretched that far is the moon-skate the user has already rejected once, so the
  jog is the honest clip for the player and the coordinator adds actWalk.timeScale in
  play3d.html. Use walk=Walk_Loop for the NPC recipe -- NPCs wander at a fraction of the
  player's speed and the walk is the honest clip THERE.
  COST OF THE JOG, measured (scratchpad/pen_who.py, hand-vs-body signed distance, every
  frame): the jog swings the right hand deep enough that at ONE frame of 29 (f15) about
  25 of 2893 fingertip vertices enter the right thigh / coat. That is not the arm hang --
  re-solving the walk at 15 deg abduction only trims it to 2 vertices -- it is the knee
  rising through the hand's swing path, and only per-frame IK would remove it. It is
  strictly better than what ships today (the KayKit walk is negative on SIX consecutive
  frames, f13..f18, up to 30 vertices). Walk_Loop is clean on every frame.
  UAL is a Rigify DEF- rig on a realistically proportioned mannequin, so the rest-pose
  mismatch that the virtual-T solves is small and the MOTION is human-scaled: no damping
  is needed (damp defaults to 1,1,1 and is now only meaningful for KayKit-sourced clips).
  Note UAL is authored at 24 fps: imported into this 30 fps scene, Idle_Loop is 0..75
  and Walk_Loop 0..40, and Blender resamples on the way in. Never hard-code those.

  WHAT THE NEW DONOR ACTUALLY MEASURED (donor rig, its own Idle_Loop, mean over cycle,
  angles away from straight DOWN; this is exactly what the transfer reproduces on her,
  since the world-delta transfer is angle-exact -- see the note under SHOULDER OFFSET):

      upper arm   L 23.7 deg (21.2 out, 11.4 back)   R 28.9 deg (12.4 out, 26.9 back)
      elbow bend  L 30.8                             R 43.7
      thigh       L 24.4 deg (9.0 out, 23.1 fwd)     R 15.9 deg (12.9 out, 9.5 back)
      knee bend   L 24.2                             R 18.8       stance width 0.357 (hips 0.178)
      toe yaw     L 5.7 turned in                    R 43.7 turned out

  So the new donor is a large improvement (KayKit's idle was 63/59 deg off vertical) but
  it is NOT free of the same class of problem: Idle_Loop is a relaxed staggered stand --
  left foot forward, right foot 0.23 back and turned out, right arm swept behind -- and
  its arms sit ~24-29 deg off vertical, which is over the 15 deg acceptance bar the user
  set. MEASURED, NOT ASSUMED: the offset machinery below is therefore kept and still
  applied, but it now moves the arms ~12-17 deg instead of ~50, and it is auto-disabled
  (see ARM_BAR / THIGH_BAR) the moment a donor lands inside the bar on its own.

  ONE CHANGE TO THE INSTRUMENT: the arm offset is solved PER CLIP for donors whose
  clips are all "neutral-armed" (arm_solve='clip'), not once from the donor's idle. With
  KayKit that distinction did not matter -- his idle and walk carry the arms alike. UAL's
  idle is deliberately asymmetric (right arm 27 deg behind the hip) while its walk is
  symmetric, so an idle-solved constant would have shoved the walking right arm 21 deg
  forward and left the left arm at 6: a permanent, visible limp in the arm swing. Solving
  each clip against the SAME target angles gives every clip the same neutral -- which is
  what the "applied to all clips" rule was really protecting (no snap on crossfade) --
  while each clip keeps its own swing envelope exactly. The KayKit jump keeps the
  idle-solved offset, since it has no neutral of its own to solve against.

SHOULDER OFFSET (added 2026-07-31, after the user flagged a "gunslinger" idle).
  MEASURED FIRST, tools/vesper_arm_probe.py, upper-arm axis (shoulder head -> elbow
  head) as an angle away from straight DOWN, at the idle:

      rogue  Idle  L 63.39 deg  R 58.65 deg      vesper-v2  Idle  L 63.39  R 58.65

  Identical to two decimals. So the virtual-T correction does NOT under-rotate -- the
  transfer is exact, and the raised arms ARE rogue's own idle stance (arms ~57 deg out
  to the side and ~40-50 deg swept behind him). He is a chibi: his arms have to clear a
  barrel torso and his hands cannot reach past his own hips, so a stance that reads as
  "arms at his sides" on him reads as a drawn-gun half-A on a normally proportioned
  woman. No amount of fixing the RETARGET fixes this; the donor's neutral is simply not
  her neutral. (That reading is what eventually forced the donor swap above; the
  instrument below is what makes ANY donor's neutral land on hers.)

  So: a constant, per-side, world-space offset applied to the whole arm chain, solved
  (not guessed) so that the retargeted clip's MEAN upper-arm axis lands on a chosen
  hanging direction:

      Cs = rotation_difference(mean upper-arm axis, target upper)   -- shoulder
      Ce = rotation_difference(Cs * mean forearm axis, target fore) -- elbow

  (the target pair comes from ARM_HANG, chosen per clip -- see PER-CLIP ARM HANG)

  and the bake drives  W_upperarm = Cs . dW . T ,  W_forearm = W_hand-chain = Ce . Cs . dW . T.
  Because Cs and Ce are CONSTANT within a clip, every frame-to-frame delta -- the
  breathing sway, the walk's arm swing, the jump's reach -- survives untouched; only the
  neutral the motion is drawn around moves. The elbow-to-wrist and shoulder-to-elbow
  lengths are untouched too (positions come from the hierarchy, not from the correction).

  WHY THIS IS NOT THE DAMPING TRAP. The predecessor's note above is right that damping
  toward REST would drift the arms out to the virtual T-pose -- but that is a statement
  about the DONOR's rest (the T). Vesper's own rest is arms-down (upper arm 68.5 deg
  BELOW horizontal, i.e. 21.7 deg off vertical), so pulling her idle toward HER rest
  pulls the arms DOWN, which is the direction we want. Both readings are consistent;
  the offset solve above is just the sharper instrument, because it hits a measured
  target angle instead of a blend weight, and it does not flatten the animation at all.

  APPLIED TO EVERY CLIP. It is a rig-space fact about her shoulders and her coat, not a
  per-clip tweak: if only the idle were corrected, the arms would snap outward the moment
  she walked. The walk's own swing envelope is preserved exactly.

PER-CLIP ARM HANG (added 2026-07-31, last; the ONE place the paragraph above is now
  qualified). The offset is still solved and applied on every clip -- what is no longer
  shared is the ANGLE it aims at. Two facts collided:

    * The idle at the coat-safe target still reads a touch wide/bent when she is standing
      still and the eye has time to look. Tightening the hang to (10,2)+(22,14) fixes it.
    * That same tight target, applied globally, SHIPS HANDS INSIDE THE COAT on the other
      two clips -- measured, not feared. Per-frame hand-vs-body signed distance (min over
      the clip; scratchpad/hand_clear.py), global-tight vs the coat-safe hang:

          Walk_Loop  L +0.0021 R -0.0169   vs   L +0.0245 R +0.0047
          Jump       L -0.0212 R -0.0284   vs   L +0.0117 R -0.0084

      i.e. the tight hang buries BOTH hands in the jump and puts the walking right hand
      in the coat as well. That build is kept as vesper-v2-ual-tighthands-REJECTED.glb.
      NB the coat-safe jump is not perfectly clean either -- the KayKit tuck grazes the
      right hand on f25/f26 (-0.0084, -0.0038) -- but that is bit-for-bit what already
      ships, and it is the number the tight hang triples.

  The resolution is that the coat clearance a target has to buy is not constant across
  clips: standing still, the coat hangs plumb and a 22 deg forearm clears it; mid-stride
  and mid-jump the coat's flare moves INTO where a tight arm would be. So:

      Idle             ARM_HANG['tight']  upper (10,2)   forearm (22,14)
      Walking_A        ARM_HANG['coat']   upper (12,6)   forearm (32,26)
      Jump_Full_Short  ARM_HANG['coat']   (same, via the KayKit shared idle solve)

  Both targets are still CONSTANT within their clip, so nothing about the swing envelope
  or the "no snap mid-clip" property changes. The neutral does differ ACROSS clips now --
  about 10 deg at the forearm -- and that settle is covered by the runtime's 0.15 s
  idle<->walk crossfade, the same mechanism that already covers the idle-only leg stance
  (see LEG STANCE, UNLIKE THE SHOULDERS). Accepted by the coordinator by design.
  The `armhang=` option overrides BOTH sets at once, which is exactly how the rejected
  global-tight build was produced -- keep it that way so that result stays reproducible.

LEG STANCE (added 2026-07-31, after the user flagged the idle a second time: "standing
  like" -- the arms were fixed but the STANCE is still the donor's: feet planted in a
  wide straddle, hip permanently cocked, a thief sizing you up). Same diagnosis as the
  shoulders -- the wide base is the donor's own neutral (a chibi needs it to look
  grounded under a giant head; UAL's is a staggered weight-shifted stand) and transfers
  verbatim -- and the same instrument: constant per-side world-space offsets, solved so
  the idle's MEAN thigh axis lands on TARGET_THIGH (feet a hip-width apart) and the shin
  on TARGET_CALF (knee nearly straight). The foot's TILT is deliberately NOT corrected,
  so it keeps the donor's world orientation and stays flat on the ground instead of
  rolling onto its inside edge.

  ITS YAW IS (added with the UAL donor, 2026-07-31). A staggered donor idle turns its
  back foot out -- UAL's right toe sits 44 deg out, which reads fine on the donor
  because that foot is also 0.23 behind the other one, and becomes one duck foot the
  moment the legs are brought under the hips. TARGET_TOE lands both toes 7 deg out; the
  correction is a rotation about the WORLD VERTICAL only (the sole stays exactly as flat
  as it was) applied from the KNEE DOWN -- see the measured reason in solve_stance: her
  coat is skinned to the thigh bones, so turning the whole leg from the hip swings the
  coat's flare into her hand (right-hand clearance +0.035 -> +0.004), while the shin
  carries only the legging and the boot shaft and turns for free.

  UNLIKE THE SHOULDERS, IDLE ONLY. The walk's leg placement is correct as shipped, and
  a constant adduction there would scissor the gait. Stance is a property of standing
  still, not of her rig; the runtime crossfades idle<->walk, so the small stance
  difference blends invisibly.
"""
import bpy, sys, math, os
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
FIXED, OUT = argv[0], argv[1]
OPT = {}
for a in argv[2:]:
    if '=' in a:
        k, v = a.split('=', 1)
        OPT[k] = v
    else:
        OPT['damp'] = a                     # legacy positional damping argument
# Optional amplitude damping "legs,arms,torso" (1,1,1 = faithful transfer, the default).
# Only meaningful for KayKit-sourced clips: rogue is an extreme chibi -- head ~60% of his
# height, legs 17% -- so his stylised bounce, transferred at full angle onto a
# realistically proportioned body, reads as a sprint rather than a walk. Damping slerps
# each bone's world delta back toward the donor's OWN idle stance (not toward rest, which
# would drift the arms out to the virtual T-pose), shrinking the swing while keeping the
# neutral pose intact. UAL is human-proportioned and needs none of it.
DAMP = [float(x) for x in OPT.get('damp', '1,1,1').split(',')]
STANCE_ON = OPT.get('stance', 'on') != 'off'

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'public', 'assets', 'characters3d')
ROGUE = os.path.join(ASSETS, 'rogue.glb')
UAL = os.path.join(ASSETS, 'ual_standard.glb')      # Quaternius Universal Animation Library, CC0

# ------------------------------------------------------------- correction targets
# Where the arms should HANG at the mean frame, in the same convention the probe
# reports: abd = tilt out to the side, fwd = tilt forward, both measured from straight
# down, per side. Acceptance bar for the upper arm is <=15 deg off vertical.
# Neither angle is zero, and that is measured, not taste: her coat flares to |x| = 0.158
# and y = -0.131 at hand height (z 0.40-0.46), so a plumb, unbent arm buries 64% of the
# hand's vertices INSIDE the coat (deepest -38 mm at model scale). The upper arm carries
# a little of the clearance and the forearm the rest -- a 25 deg elbow with the hands
# resting just outside the coat's flare, which is what a person in a heavy coat does.
# The right side gets ~1-2 deg more of both because the satchel hangs there.
# Solved by sweeping these four angles against the hand-vs-coat signed-distance probe.
# These are facts about HER, not about the donor, so they survive the donor swap intact.
# A hang is written once as the LEFT angles and mirrored (+0/+1 upper, +1/+2 forearm).
def hang(u_abd, u_fwd, f_abd, f_fwd):
    return ({'L': (u_abd, u_fwd), 'R': (u_abd, u_fwd + 1.0)},
            {'L': (f_abd, f_fwd), 'R': (f_abd + 1.0, f_fwd + 2.0)})

# Two hangs, chosen PER CLIP (see PER-CLIP ARM HANG above). 'coat' is the solved,
# coat-safe pair; 'tight' is the closer hang the idle can afford because a still coat
# hangs plumb. Which clip gets which is in CLIPS below -- not here.
ARM_HANG = {
    'coat': hang(12.0, 6.0, 32.0, 26.0),
    'tight': hang(10.0, 2.0, 22.0, 14.0),
}
# A/B knob for the hang, so the angles above can be re-shot without editing code:
# armhang=U_abd,U_fwd,F_abd,F_fwd gives the LEFT side. It overrides EVERY hang, i.e. it
# puts one global target on all three clips -- which is how the rejected tight-hands
# build was made, and the reason the per-clip table exists. The default is the pair above.
if 'armhang' in OPT:
    ARM_HANG = {k: hang(*(float(x) for x in OPT['armhang'].split(','))) for k in ARM_HANG}
    print("armhang override (ALL clips): upper %s forearm %s" % ARM_HANG['coat'])
# Where the thighs should point at the idle's mean frame (see LEG STANCE above).
# A relaxed stand is feet under hips: thigh a few degrees out, none forward.
TARGET_THIGH = {'L': (4.0, 0.0), 'R': (4.0, 0.0)}       # (abd out, fwd) degrees off DOWN
# The shin continues the thigh with only a whisper of knee: the donors' idles keep a
# bent combat-ready knee that reads as a slouch once the stance is narrowed.
TARGET_CALF = {'L': (4.0, -2.0), 'R': (4.0, -2.0)}      # near-vertical shin, ~2 deg heel-back
# Where the TOES should point once the stance is narrowed (deg turned outward, per side).
# A relaxed stand is a few degrees out, not parallel and not splayed -- see FOOT YAW.
TARGET_TOE = {'L': 7.0, 'R': 7.0}

# A donor that already lands inside these bars gets NO offset at all -- the point of
# swapping donors was to stop stacking corrections on motion that does not need them.
# (ARM_BAR/ELBOW_OK mirror tools/vesper_verify.py's acceptance test; the hand-vs-coat
# clearance is verify's to judge, this script only reads bone angles.)
ARM_BAR = 15.0
ELBOW_OK = (10.0, 40.0)
THIGH_BAR = 8.0
KNEE_BAR = 10.0
TOE_BAR = 12.0     # deg of splay away from TARGET_TOE that needs no correcting

# ---------------------------------------------------------------- bone maps
# Tripo (Vesper) -> donor.  Twist chains and the clavicles are absent from both donors
# and are deliberately left to inherit.
KAY_MAP = {
    'Hip': 'hips',
    'Spine01': 'spine',
    'Spine02': 'chest',
    'NeckTwist01': 'head', 'NeckTwist02': 'head', 'Head': 'head',
    'L_Upperarm': 'upperarm.l', 'L_Forearm': 'lowerarm.l', 'L_Hand': 'hand.l',
    'R_Upperarm': 'upperarm.r', 'R_Forearm': 'lowerarm.r', 'R_Hand': 'hand.r',
    'L_Thigh': 'upperleg.l', 'L_Calf': 'lowerleg.l', 'L_Foot': 'foot.l', 'L_ToeBase': 'toes.l',
    'R_Thigh': 'upperleg.r', 'R_Calf': 'lowerleg.r', 'R_Foot': 'foot.r', 'R_ToeBase': 'toes.r',
}
KAY_CHILD = {'upperarm.l': 'lowerarm.l', 'lowerarm.l': 'wrist.l', 'upperleg.l': 'lowerleg.l',
             'lowerleg.l': 'foot.l', 'foot.l': 'toes.l',
             'upperarm.r': 'lowerarm.r', 'lowerarm.r': 'wrist.r', 'upperleg.r': 'lowerleg.r',
             'lowerleg.r': 'foot.r', 'foot.r': 'toes.r',
             'spine': 'chest', 'chest': 'head'}
# UAL is Rigify: DEF- deform chain, hips + spine.001..003 + neck + head, fingers.
# Spine02 -> DEF-spine.002 and NOT spine.003: measured, the donor's idle leans
# spine.003 14.3 deg forward (a relaxed mannequin hunch) while spine.002 sits 1.2 deg
# off vertical, and Spine02 is where her clavicles hang -- mapping the hunch in would
# push her shoulders and coat forward for no gain. Everything above Spine02 is mapped
# absolutely anyway (neck, head), so the head still lands where the donor puts it.
UAL_MAP = {
    'Hip': 'DEF-hips',
    'Spine01': 'DEF-spine.001',
    'Spine02': 'DEF-spine.002',
    'NeckTwist01': 'DEF-neck', 'NeckTwist02': 'DEF-neck', 'Head': 'DEF-head',
    'L_Upperarm': 'DEF-upper_arm.L', 'L_Forearm': 'DEF-forearm.L', 'L_Hand': 'DEF-hand.L',
    'R_Upperarm': 'DEF-upper_arm.R', 'R_Forearm': 'DEF-forearm.R', 'R_Hand': 'DEF-hand.R',
    'L_Thigh': 'DEF-thigh.L', 'L_Calf': 'DEF-shin.L', 'L_Foot': 'DEF-foot.L', 'L_ToeBase': 'DEF-toe.L',
    'R_Thigh': 'DEF-thigh.R', 'R_Calf': 'DEF-shin.R', 'R_Foot': 'DEF-foot.R', 'R_ToeBase': 'DEF-toe.R',
}
UAL_CHILD = {'DEF-upper_arm.L': 'DEF-forearm.L', 'DEF-forearm.L': 'DEF-hand.L',
             'DEF-hand.L': 'DEF-f_middle.01.L',
             'DEF-thigh.L': 'DEF-shin.L', 'DEF-shin.L': 'DEF-foot.L', 'DEF-foot.L': 'DEF-toe.L',
             'DEF-upper_arm.R': 'DEF-forearm.R', 'DEF-forearm.R': 'DEF-hand.R',
             'DEF-hand.R': 'DEF-f_middle.01.R',
             'DEF-thigh.R': 'DEF-shin.R', 'DEF-shin.R': 'DEF-foot.R', 'DEF-foot.R': 'DEF-toe.R',
             'DEF-spine.001': 'DEF-spine.002', 'DEF-spine.002': 'DEF-spine.003',
             'DEF-spine.003': 'DEF-neck', 'DEF-neck': 'DEF-head'}

DONORS = {
    'kaykit': dict(key='kaykit', path=ROGUE, hip='hips', idle='Idle',
                   map=KAY_MAP, child=KAY_CHILD, arm_solve='idle'),
    'ual': dict(key='ual', path=UAL, hip='DEF-hips', idle='Idle_Loop',
                map=UAL_MAP, child=UAL_CHILD, arm_solve='clip'),
}
# The runtime contract (public/play3d.html) is these three names, in this spelling.
# 'hang' picks the arm target out of ARM_HANG -- see PER-CLIP ARM HANG. Only the idle,
# whose coat hangs still, can afford the tight one.
CLIPS = [
    dict(name='Idle', donor='ual', src=OPT.get('idle', 'Idle_Loop'),
         stance=True, hang='tight'),
    dict(name='Walking_A', donor='ual', src=OPT.get('walk', 'Jog_Fwd_Loop'),
         stance=False, hang='coat'),
    dict(name='Jump_Full_Short', donor='kaykit', src='Jump_Full_Short',
         stance=False, hang='coat'),
]

# anatomical direction = head -> this child's head (leaves fall back to the bone axis)
CHILD_T = {'L_Upperarm': 'L_Forearm', 'L_Forearm': 'L_Hand', 'L_Thigh': 'L_Calf',
           'L_Calf': 'L_Foot', 'L_Foot': 'L_ToeBase',
           'R_Upperarm': 'R_Forearm', 'R_Forearm': 'R_Hand', 'R_Thigh': 'R_Calf',
           'R_Calf': 'R_Foot', 'R_Foot': 'R_ToeBase',
           'Spine01': 'Spine02', 'Spine02': 'NeckTwist01'}
# bones whose rest ORIENTATION must be pre-aligned to the donor's rest (the T-pose delta)
ALIGN = {b for b in UAL_MAP if any(k in b for k in
         ('Upperarm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'ToeBase'))}

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

def set_action(obj, act):
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = act
    try:
        obj.animation_data.action_slot = act.slots[0]
    except Exception:
        pass

def frange(act):
    return int(round(act.frame_range[0])), int(round(act.frame_range[1]))

def tdir(sx, abd, fwd):
    """Unit direction: `abd` deg out to the side, `fwd` deg forward, off straight down."""
    return Vector((sx * math.tan(math.radians(abd)),
                   -math.tan(math.radians(fwd)), -1.0)).normalized()

def report(v):
    return (math.degrees(v.angle(Vector((0, 0, -1)))),
            math.degrees(math.atan2(v.x, -v.z)), math.degrees(math.atan2(-v.y, -v.z)))

# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30           # KayKit is authored at 30fps; UAL at 24 and is resampled on import

donor_objs = []
for key in sorted({c['donor'] for c in CLIPS}):
    D = DONORS[key]
    before_o = set(bpy.data.objects)
    before_a = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=D['path'])
    new_o = [o for o in bpy.data.objects if o not in before_o]
    D['acts'] = {a.name: a for a in bpy.data.actions if a not in before_a}
    D['objs'] = new_o
    D['obj'] = [o for o in new_o if o.type == 'ARMATURE'][0]
    D['obj'].name = 'DONOR_' + key
    donor_objs += new_o
    print("donor %-7s %s: %d objects, %d actions, armature %s (%d bones)" %
          (key, os.path.basename(D['path']), len(new_o), len(D['acts']),
           D['obj'].name, len(D['obj'].data.bones)))

bpy.ops.import_scene.gltf(filepath=FIXED)
tgt = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o not in donor_objs][0]
vmesh = [o for o in bpy.data.objects if o.type == 'MESH' and o not in donor_objs
         and not o.name.startswith('Icosphere')]
purge_icospheres()
print("target armature:", tgt.name, "meshes:", [o.name for o in vmesh])
assert tgt.matrix_world == Matrix.Identity(4)
for key in DONORS:
    if 'obj' in DONORS[key]:
        assert DONORS[key]['obj'].matrix_world == Matrix.Identity(4), key

# flatten the Tripo RootNode empty away, keep the transform (it is identity)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY' and not o.children_recursive:
        bpy.data.objects.remove(o, do_unlink=True)

tb = tgt.data.bones
ORDER = hier(tgt)
REL = {b.name: rest_rel(b) for b in ORDER}
BASE3_HIP = rest_rel(tb[HIP]).to_3x3()   # Hip's parent (Root) never poses, so this is constant

# ---------------------------------------------------------------- per-donor reference frames
def prep_donor(D):
    src, mp, ch = D['obj'], D['map'], D['child']
    sb = src.data.bones
    missing = [k for k in mp if k not in tb] + [v for v in mp.values() if v not in sb]
    assert not missing, "%s missing bones: %s" % (D['key'], missing)

    leg_s = ((sb[mp['L_Thigh']].head_local - sb[mp['L_Calf']].head_local).length +
             (sb[mp['L_Calf']].head_local - sb[mp['L_Foot']].head_local).length)
    leg_t = ((tb['L_Thigh'].head_local - tb['L_Calf'].head_local).length +
             (tb['L_Calf'].head_local - tb['L_Foot'].head_local).length)
    D['ratio'] = leg_t / leg_s
    D['restq'] = {b.name: (src.matrix_world @ b.matrix_local).to_quaternion() for b in sb}
    D['hip_rest'] = sb[D['hip']].matrix_local.translation.copy()

    print("\n[%s] leg length donor=%.4f target=%.4f  hip-translation ratio=%.4f"
          % (D['key'], leg_s, leg_t, D['ratio']))
    print("%-13s -> %-18s %-6s donor rest dir        target rest dir       delta" %
          ("TRIPO", D['key'].upper(), "align"))
    for t, s in sorted(mp.items()):
        ds = anat_dir(src, s, ch)
        dt = anat_dir(tgt, t, CHILD_T)
        print("%-13s -> %-18s %-6s (%6.3f,%6.3f,%6.3f)  (%6.3f,%6.3f,%6.3f)  %5.1f deg" %
              (t, s, 'YES' if t in ALIGN else '-', ds.x, ds.y, ds.z, dt.x, dt.y, dt.z,
               math.degrees(ds.angle(dt))))

    # T[]: the target's rest, pre-rotated so each limb's anatomical axis matches the
    # donor's rest axis (the virtual T-pose). Hierarchical, so parents feed children.
    T = {}
    for b in ORDER:
        base = (T[b.parent.name] @ REL[b.name]) if b.parent else REL[b.name].copy()
        if b.name in ALIGN and b.name in mp:
            u = b.matrix_local.to_3x3().inverted() @ anat_dir(tgt, b.name, CHILD_T)
            cur = (base.to_3x3() @ u).normalized()
            want = anat_dir(src, mp[b.name], ch)
            Rc = cur.rotation_difference(want).to_matrix()
            m = (Rc @ base.to_3x3()).to_4x4()
            m.translation = base.translation
            T[b.name] = m
        else:
            T[b.name] = base
    D['T'] = T
    print("[%s] T-pose reference built; shoulder correction = %.1f deg, hip/torso = %.1f deg" % (
        D['key'],
        math.degrees((T['L_Upperarm'].to_3x3().to_quaternion().rotation_difference(
            tb['L_Upperarm'].matrix_local.to_3x3().to_quaternion())).angle),
        math.degrees((T['Hip'].to_3x3().to_quaternion().rotation_difference(
            tb['Hip'].matrix_local.to_3x3().to_quaternion())).angle)))

    # damping pivot: the donor's own idle stance
    idle = D['acts'][D['idle']]
    set_action(src, idle)
    sc.frame_set(frange(idle)[0])
    bpy.context.view_layer.update()
    D['dref'] = {n: (src.matrix_world @ src.pose.bones[n].matrix).to_quaternion()
                 @ D['restq'][n].inverted() for n in set(mp.values())}
    D['dref_hip'] = src.pose.bones[D['hip']].matrix.translation - D['hip_rest']

for key in sorted({c['donor'] for c in CLIPS}):
    prep_donor(DONORS[key])

for pb in tgt.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# ---------------------------------------------------------------- target measurements
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
print("damping (legs,arms,torso) =", DAMP, " leg-stance correction:", "ON" if STANCE_ON else "OFF")

IDQ = Quaternion((1, 0, 0, 0))

def damped(D, dW, sname, k):
    if k >= 0.999:
        return dW[sname]
    rel = D['dref'][sname].inverted() @ dW[sname]
    if rel.w < 0:
        rel.negate()
    return D['dref'][sname] @ IDQ.slerp(rel, k)

# ---------------------------------------------------------------- pose evaluation
def eval_pose(D, clip, f, corr):
    """Pose the target rig from donor frame f. Returns {bone: world matrix}."""
    sc.frame_set(f)
    bpy.context.view_layer.update()
    src, mp = D['obj'], D['map']
    dW = {}
    for name in set(mp.values()):
        q = (src.matrix_world @ src.pose.bones[name].matrix).to_quaternion()
        dW[name] = q @ D['restq'][name].inverted()
    raw_hip = src.pose.bones[D['hip']].matrix.translation - D['hip_rest']
    hip_off = (D['dref_hip'] + (raw_hip - D['dref_hip']) * damp_k('L_Thigh', clip)) * D['ratio']

    W = {}
    for b in ORDER:
        base = (W[b.parent.name] @ REL[b.name]) if b.parent else REL[b.name].copy()
        pb = tgt.pose.bones[b.name]
        if b.name in mp:
            want3 = damped(D, dW, mp[b.name], damp_k(b.name, clip)).to_matrix() @ D['T'][b.name].to_3x3()
            C = corr.get(b.name)
            if C is not None:
                want3 = C.to_matrix() @ want3       # constant world-space offset
            basis3 = base.to_3x3().inverted() @ want3
        else:
            basis3 = Matrix.Identity(3)
        mb = basis3.to_4x4()
        if b.name == HIP:
            mb.translation = base.to_3x3().inverted() @ hip_off
        pb.matrix_basis = mb
        W[b.name] = base @ mb
    return W

def limb_axes(W, s):
    """(upper arm, forearm, thigh, shin, foot) unit axes, world space."""
    p = lambda n: W[s + n].translation
    return ((p('_Forearm') - p('_Upperarm')).normalized(),
            (p('_Hand') - p('_Forearm')).normalized(),
            (p('_Calf') - p('_Thigh')).normalized(),
            (p('_Foot') - p('_Calf')).normalized(),
            (p('_ToeBase') - p('_Foot')).normalized())

def toe_yaw(v):
    """Degrees the toe direction is turned away from dead ahead (+ = toward +x)."""
    return math.degrees(math.atan2(v.x, -v.y))

def mean_axes(D, clip, act, corr):
    """Mean limb axes over the whole clip, as a {side: [5 vectors]} dict."""
    f0, f1 = frange(act)
    set_action(D['obj'], act)
    acc = {s: [Vector() for _ in range(5)] for s in 'LR'}
    for f in range(f0, f1 + 1):
        W = eval_pose(D, clip, f, corr)
        for s in 'LR':
            for i, v in enumerate(limb_axes(W, s)):
                acc[s][i] += v
    return {s: [v.normalized() for v in acc[s]] for s in 'LR'}

# --------------------------------------------------- solve the constant offsets
# (see the SHOULDER OFFSET / LEG STANCE sections above; measure -> decide -> solve)
def solve_arms(D, clip, act, label, hang_name):
    t_upper, t_fore = ARM_HANG[hang_name]
    m = mean_axes(D, clip, act, {})
    print("\nARM SOLVE  [%s]  (mean over %s frames %d..%d, '%s' hang: upper %s forearm %s)"
          % (label, act.name, *frange(act), hang_name, t_upper, t_fore))
    worst_el = max(math.degrees(m[s][0].angle(Vector((0, 0, -1)))) for s in 'LR')
    bends = [math.degrees(m[s][1].angle(m[s][0])) for s in 'LR']
    for s in 'LR':
        print("  %s raw upperarm elev %5.1f (abd %5.1f fwd %5.1f)   forearm elev %5.1f "
              "(abd %5.1f fwd %5.1f)   elbow %5.1f" %
              ((s,) + report(m[s][0]) + report(m[s][1]) + (math.degrees(m[s][1].angle(m[s][0])),)))
    if worst_el <= ARM_BAR and ELBOW_OK[0] <= min(bends) and max(bends) <= ELBOW_OK[1]:
        print("  -> donor already inside the bar (worst elev %.1f <= %.1f, elbow %.1f..%.1f)"
              ": NO shoulder offset applied." % (worst_el, ARM_BAR, min(bends), max(bends)))
        return {}
    print("  -> outside the bar (worst upper-arm elev %.1f, bar %.1f; elbow %.1f..%.1f, bar %s)"
          ": solving constant offsets." % (worst_el, ARM_BAR, min(bends), max(bends), ELBOW_OK))
    corr = {}
    for s, sx in (('L', 1.0), ('R', -1.0)):
        u, fo = m[s][0], m[s][1]
        want_u = tdir(sx, *t_upper[s])
        Cs = u.rotation_difference(want_u)
        want_f = tdir(sx, *t_fore[s])
        Ce = (Cs @ fo).rotation_difference(want_f)
        corr[s + '_Upperarm'] = Cs
        corr[s + '_Forearm'] = Ce @ Cs
        corr[s + '_Hand'] = Ce @ Cs
        print("  %s upperarm  before elev %5.1f (abd %5.1f fwd %5.1f) -> after elev %5.1f "
              "(abd %5.1f fwd %5.1f)   Cs = %.1f deg" %
              ((s,) + report(u) + report(want_u) + (math.degrees(Cs.angle),)))
        print("  %s forearm   before elev %5.1f (abd %5.1f fwd %5.1f) -> after elev %5.1f "
              "(abd %5.1f fwd %5.1f)   Ce = %.1f deg   elbow bend %.1f -> %.1f deg" %
              ((s,) + report(fo) + report(want_f) +
               (math.degrees(Ce.angle), math.degrees(fo.angle(u)),
                math.degrees(want_f.angle(want_u)))))
    return corr

def solve_stance(D, clip, act, arm_corr, label):
    """Idle-only: thigh+shin constant offsets, foot deliberately left alone."""
    m = mean_axes(D, clip, act, arm_corr)
    print("\nLEG STANCE SOLVE  [%s]  (mean over %s frames %d..%d)" % (label, act.name, *frange(act)))
    worst_th = max(math.degrees(m[s][2].angle(Vector((0, 0, -1)))) for s in 'LR')
    knees = [math.degrees(m[s][3].angle(m[s][2])) for s in 'LR']
    for s in 'LR':
        print("  %s raw thigh elev %5.1f (abd %5.1f fwd %5.1f)   shin elev %5.1f "
              "(abd %5.1f fwd %5.1f)   knee %5.1f" %
              ((s,) + report(m[s][2]) + report(m[s][3]) + (math.degrees(m[s][3].angle(m[s][2])),)))
    if not STANCE_ON:
        print("  -> stance=off requested: NO leg offset applied.")
        return {}
    if worst_th <= THIGH_BAR and max(knees) <= KNEE_BAR:
        print("  -> donor already stands under its hips (worst thigh %.1f <= %.1f, knee "
              "%.1f <= %.1f): NO leg offset applied." % (worst_th, THIGH_BAR, max(knees), KNEE_BAR))
        return {}
    print("  -> outside the bar (worst thigh elev %.1f, bar %.1f; worst knee %.1f, bar %.1f)"
          ": solving constant offsets." % (worst_th, THIGH_BAR, max(knees), KNEE_BAR))
    corr = {}
    for s, sx in (('L', 1.0), ('R', -1.0)):
        th, ca = m[s][2], m[s][3]
        want_t = tdir(sx, *TARGET_THIGH[s])
        Ct = th.rotation_difference(want_t)
        want_c = tdir(sx, *TARGET_CALF[s])
        Ck = (Ct @ ca).rotation_difference(want_c)
        corr[s + '_Thigh'] = Ct
        corr[s + '_Calf'] = Ck @ Ct
        print("  %s thigh     before elev %5.1f (abd %5.1f fwd %5.1f) -> after elev %5.1f "
              "(abd %5.1f fwd %5.1f)   Ct = %.1f deg" %
              ((s,) + report(th) + report(want_t) + (math.degrees(Ct.angle),)))
        print("  %s calf      before elev %5.1f (abd %5.1f fwd %5.1f) -> after elev %5.1f "
              "(abd %5.1f fwd %5.1f)   Ck = %.1f deg   knee bend %.1f -> %.1f deg" %
              ((s,) + report(ca) + report(want_c) +
               (math.degrees(Ck.angle), math.degrees(ca.angle(th)),
                math.degrees(want_c.angle(want_t)))))
    # FOOT YAW (see the LEG STANCE note): straightening the stance leaves the donor's
    # foot DIRECTION untouched, and a staggered donor idle turns its BACK foot far out
    # (UAL: right toe 44 deg) -- which, once the leg is brought under the hip, reads as
    # one duck foot. Correct it with a rotation about the WORLD VERTICAL only, so the
    # sole stays exactly as flat on the ground as it was.
    #   Applied from the KNEE DOWN (shin+foot+toe), not from the hip. Anatomically the
    #   hip is where a turned-out foot comes from, and that was the first attempt -- but
    #   MEASURED: her coat is skinned to the thigh bones, so a 37 deg thigh rotation
    #   swings the coat's flare into her hand and cuts the right hand's clearance from
    #   +0.035 to +0.004. The shin only carries the legging and the boot shaft, both
    #   rotationally symmetric, and the corrected knee is 2 deg from straight, so turning
    #   there is invisible and touches nothing else.
    for s, sx in (('L', 1.0), ('R', -1.0)):
        yaw = toe_yaw(m[s][4])
        want = sx * TARGET_TOE[s]
        if abs(want - yaw) <= TOE_BAR:
            print("  %s toe       yaw %+5.1f deg, within %.1f of the %+.1f target: left alone"
                  % (s, yaw, TOE_BAR, want))
            continue
        Cf = Quaternion(Vector((0, 0, 1)), math.radians(want - yaw))
        corr[s + '_Calf'] = Cf @ corr[s + '_Calf']
        corr[s + '_Foot'] = Cf
        corr[s + '_ToeBase'] = Cf
        print("  %s toe       yaw %+5.1f -> %+5.1f deg   Cf = %+.1f deg about vertical "
              "(knee down)" % (s, yaw, want, want - yaw))
    return corr

# Donors whose clips all share one neutral (KayKit) solve the arm offset ONCE, from their
# own idle, and reuse it -- the jump has no neutral of its own to solve against.
IDLE_CORR = {}
for key in sorted({c['donor'] for c in CLIPS}):
    D = DONORS[key]
    if D['arm_solve'] != 'idle':
        continue
    hangs = {c['hang'] for c in CLIPS if c['donor'] == key}
    assert len(hangs) == 1, "%s clips disagree on the arm hang %s -- a shared solve " \
        "cannot serve two targets" % (key, sorted(hangs))
    h = hangs.pop()
    IDLE_CORR[key] = solve_arms(D, 'Idle', D['acts'][D['idle']],
                                '%s idle (shared)' % key, h)

# ---------------------------------------------------------------- bake
if not tgt.animation_data:
    tgt.animation_data_create()

made = []
for spec in CLIPS:
    clip, D = spec['name'], DONORS[spec['donor']]
    sact = D['acts'].get(spec['src'])
    if sact is None:
        raise SystemExit("donor clip missing: %s.%s (have %s)"
                         % (D['key'], spec['src'], sorted(D['acts'])))
    print("\n================ %s  <-  %s '%s'" % (clip, D['key'], sact.name))
    set_action(D['obj'], sact)
    f0, f1 = frange(sact)

    clip_corr = dict(IDLE_CORR[D['key']]) if D['arm_solve'] == 'idle' \
        else solve_arms(D, clip, sact, '%s %s' % (D['key'], clip), spec['hang'])
    if spec['stance']:
        clip_corr.update(solve_stance(D, clip, sact, clip_corr, '%s %s' % (D['key'], clip)))

    # NB: the donors' own actions can be called Idle/Walking_A/..., so bake under a
    # prefix and rename after the donors are purged -- otherwise actions.new() silently
    # yields "Idle.001", the cleanup pass drops it, and the exporter ships a DONOR's
    # clip (which targets donor bone names) as constant channels. That bug shipped a
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

    stats = {s: [Vector() for _ in range(5)] for s in 'LR'}
    arms = {s: [] for s in 'LR'}
    for f in range(f0, f1 + 1):
        W = eval_pose(D, clip, f, clip_corr)
        for s in 'LR':
            ax = limb_axes(W, s)
            arms[s].append(math.degrees(ax[0].angle(Vector((0, 0, -1)))))
            for i, v in enumerate(ax):
                stats[s][i] += v
        for b in ORDER:
            pb = tgt.pose.bones[b.name]
            if b.name in D['map']:
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
    made.append((clip, D['key'], sact.name, f0, f1, (f1 - f0) / sc.render.fps))
    print("baked %-18s frames %d..%d  (%.3fs)  foot z %.4f..%.4f  hip lift %+.4f  span %.3f"
          % (clip, f0, f1, (f1 - f0) / sc.render.fps, min(zs), max(zs), lift, span))
    print("   upper-arm off-vertical: " + "  ".join(
        "%s mean %5.1f  range %5.1f..%5.1f" % (s, sum(arms[s]) / len(arms[s]),
                                               min(arms[s]), max(arms[s])) for s in 'LR'))
    for s in 'LR':
        u, fo, th, ca, to = [v.normalized() for v in stats[s]]
        print("   %s FINAL mean upper %5.1f (abd %5.1f fwd %5.1f) elbow %5.1f | "
              "thigh %5.1f (abd %5.1f fwd %5.1f) knee %5.1f | toe yaw %+5.1f" %
              ((s,) + report(u) + (math.degrees(fo.angle(u)),) + report(th) +
               (math.degrees(ca.angle(th)), toe_yaw(to))))

# ---------------------------------------------------------------- strip the donors
sc.frame_set(0)
for key in list(DONORS):
    D = DONORS[key]
    if 'obj' not in D:
        continue
    if D['obj'].animation_data:
        D['obj'].animation_data_clear()
for o in donor_objs:
    try:
        bpy.data.objects.remove(o, do_unlink=True)
    except ReferenceError:
        pass          # already gone (e.g. purged as an importer Icosphere)
for a in list(bpy.data.actions):
    if not a.name.startswith(BAKE_PREFIX):
        bpy.data.actions.remove(a)
for a in bpy.data.actions:
    a.name = a.name[len(BAKE_PREFIX):]
assert sorted(a.name for a in bpy.data.actions) == sorted(c['name'] for c in CLIPS), \
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
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
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
for c in made:
    print("CLIP %-18s <- %-7s %-20s frames %d..%d  %.3fs" % c)
