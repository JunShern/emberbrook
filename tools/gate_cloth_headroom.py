"""gate_cloth_headroom.py — LIFT THE CLOTH OUT OF THE GATEWAY.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_cloth_headroom.py -- [save]

THE COMPLAINT.  User, right ellipse of docs/qa/refs/user_gate_tier_annotated.png:
*"There seems to be some invisible geometry here blocking me"* — on the gate road,
walking in through the Valley Gate.

THE MEASUREMENT that this pass is built on, and it corrects a figure the slate
carried.  The slate said "the arch banner's 0.71 m clearance" and the DAYLOG
correctly noted no such number is anywhere in the repo.  Measured here on the
master (0.10 m column grid over the banner's own footprint, highest walk surface
under each column):

    t2c_G4_arch_banner   bbox x 15.37..18.22  y 4.04..4.20  z 24.78..28.25
    walk_pad_valley-gate top z 24.040
    clearance            MIN 0.806 m over a sampled column, 0.740 m from the
                         banner's own lowest vertex; median 3.685 m
    8 of 28 columns are under a 1.70 m body; 5 of 28 under the 1.20 m chest

So the claim was RIGHT within 3 cm and the mechanism is not a droop — it is a
vertical hanging cloth whose bottom edge stops 0.74 m off the floor, in the middle
of the town's front door.  It is also `walk_bodygate`'s confirmed 2/2 body blocker
(868 blocked steps town-wide) and a `geometry_audit` survivor (frac 0.047 into
gate_arch, twice called pre-existing).

WHAT THIS DOES.  For each named cloth object it RAISES ONLY THE VERTICES THAT ARE
LOW, on a per-vertex ramp, until the object's lowest point clears `WANT` metres
over the highest walk surface under its own footprint.  The top edge does not
move, so a banner stays hung where it was hung and simply stops short of the
carriageway — a shorter banner, not a floating one.  Nothing is scaled, nothing is
translated bodily, and an object already clear is left untouched (idempotent).

WHY NOT `t2_color_pops.py` (which authored these).  That script places by
SCREEN-SPACE PROBE RECTANGLE and its successor's own docstring says those
rectangles "carried no idea of what was UNDER them" — re-running it re-commits the
same mistake.  The height a cloth must clear is a property of the walk graph, and
that is what is measured here.  A future `t2_color_pops` re-run WILL undo this;
the fix belongs in that placer eventually, and this pass is the interim with its
measurement attached.
"""
import bpy, json, math, os, sys
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
MANIFEST = REPO + "/tools/blends/districts/gate_cloth_headroom.json"

# CORRIDOR_H is 2.05 m (gate_lib) — the headroom band the master's walk QA measures
# over a walk surface.  WANT adds a hand's width so a cloth is not exactly on the bar.
WANT = 2.15
TARGETS = ["t2c_G4_arch_banner"]
# THIS NOTE WAS WRONG AND IS CORRECTED HERE (2026-08-02), because it was believed and
# acted on.  It used to read: `t2c_G7_bunting_gate2` "spans several walk levels; one ramp
# leaves 0.669 m — needs a per-span re-hang", and a later lane was dispatched to write
# that per-span re-hang.  The mistake was reading "18.990" as a HEM.  Measured part by
# part (tools/gate_bunting_rehang.py), the run has 24 loose parts and every piece of
# CLOTH in it — 11 rope segments, 11 pennants — lives between z 25.798 and 26.620, which
# is 1.73 m over the gate road at 24.07 and 6.7 m over anything else.  NO CLOTH IN THAT
# OBJECT WAS EVER A BLOCKER.  18.990 was the footing of its EAST MAST: a 7.61 m timber
# pole, 0.16 m square, that `t2_color_pops.py`'s `ground_below(top, 8.0)` had stood on
# the inn tier because the run's last node overhangs the head of the gate stair and the
# down-ray fell past three walk levels.  All 560 of the object's blocked steps were that
# pole.  It is fixed by moving the run's END POINT, not its cloth, and the fix removed
# exactly 560 blocked steps town-wide (205677 -> 205117) — the same signature this
# script's own banner fix left (868).  THE LESSON, and it is the one CLAUDE.md's
# documentation bar names: a z-number in a bbox is not a hem until something measures
# which PART it belongs to.
#
# RE-MEASURED INDEPENDENTLY 2026-08-02 (second lane, fresh instrument, not a re-run of
# gate_bunting_rehang).  Every claim above reproduces on the current master: the run's
# 22 cloth parts sit z 25.798..26.620, the two masts are 2.355 m and 2.629 m and stand
# in ZERO walk triangles, and `walk_bodygate --scene del-cine` no longer lists the
# object at all (town-wide 205117, the exact figure claimed).  Per-vertex — which is
# the only way headroom means anything — the gate2 cloth measures min 1.783 m, median
# 2.285 m, ONE vertex under CORRIDOR_H and NONE under a 1.70 m body.  So it is clear
# for the player and a hair under the band for one vertex: a non-issue, with numbers.
#
# WHAT THAT SURVEY TURNED UP INSTEAD, and it is the part worth keeping.  Sweeping ALL
# 20 cloth objects in the town by this file's own `walk_top()` (per cloth vertex, masts
# excluded, since a pole's footing is not a hem) finds the blockers were never at the
# valley gate.  They are at the DAM CREST, and both agree with `walk_bodygate`:
#
#   object                 verts  min clr  median   <2.05  <1.70   blocked steps
#   lf_bunting_0              80    0.002   0.215      80     80        976
#   t2c_L1_crest_banners      43    1.130   2.701      14     10        582
#
# `lf_bunting_0` is not low, it is ON `walk_pad_dam-crest-gate` — 2 mm at its worst
# vertex, and every one of its 80 cloth vertices passes through a standing character.
# That is this script's exact mechanism (a hanging cloth whose bottom edge stops in the
# carriageway) and its per-vertex ramp would fix both by adding them to TARGETS.
#
# NOT DONE HERE, DELIBERATELY, AND THE REASON IS THE RE-BAKE.  Unlike the 7.61 m mast —
# which was 0/16 visible and so cost nothing to move — both of these are ON SCREEN
# (frustum + occlusion probe against the 16 solved cameras): t2c_L1_crest_banners is
# visible from cottage-steps 11/12, lockfive 7/12, north-landing 2/12; lf_bunting_0 from
# gate, crossing, cottage-steps, lockfive, north-landing.  Lifting them 2 m re-composes
# five plates, and the Emberbrook dressed-plate lane held the GPU for this whole window
# (CLAUDE.md's 1-wide serial rule at that plate size).  Recorded with its measurement
# rather than half-done, which is the same call the note above got wrong by GUESSING.
UNFIXED = {
    "lf_bunting_0": "976 blocked steps; per-vertex min 0.002 m over walk_pad_dam-crest-gate, "
                    "median 0.215, ALL 80 cloth verts under a 1.70 m body. This script's own "
                    "mechanism fixes it — owed a re-bake of gate/crossing/cottage-steps/"
                    "lockfive/north-landing, which is why it is not in TARGETS yet",
    "t2c_L1_crest_banners": "582 blocked steps; per-vertex min 1.130 m, 10 of 43 verts under "
                            "a 1.70 m body. Visible cottage-steps 11/12, lockfive 7/12, "
                            "north-landing 2/12 — same owed re-bake",
    "t2c_N2_nl_bunting": "1240 blocked steps but NOT this defect: per-vertex min 2.439 m, "
                         "nothing under the band. Its two 3.21 m masts are the count, and a "
                         "bunting pole standing on the ground is not a defect",
    # ADDED 2026-08-05 (playtest round 24, PT-20260805-038's measurement). Same
    # mechanism, different street, and it SEVERS A WALKWAY rather than narrowing one.
    # `_court_probe --grid walk:true` over the crossing ribbon (x 73..90, z -25..-20,
    # y band 6..10) shows the corridor blocked at x 78.7..79.6 at EVERY walkable z
    # (-22.1, -22.4, -22.7, -23.0, -23.3), and `--who` names the blocker:
    #     t2c_W9_laundry_planking_5   bbox y 8.78..9.67   walk surface under it 7.50
    #                                 hem clearance 1.28 m — under a 1.70 m body
    #     t2c_W9_laundry_planking_4   bbox y 9.07..9.63   clearance 1.57 m — also under
    # `--comp` over the same box fills the weave side and the crossing side as TWO
    # components (115 / 144 cells) that never join on foot.
    # NOT ON THE STORY'S PATH, WHICH IS WHY IT IS RECORDED RATHER THAN FIXED HERE.
    # `weave>crossing` is a CUT edge whose spawn is 9.3 m east (84.54), past the
    # laundry, so the game steps over the severance: `reach_probe` maren -> Keepers'
    # Cottage door is ok=true via three cut edges. A player who tries to WALK that
    # 6.4 m instead of crossing the seam is the one who meets it.
    "t2c_W9_laundry_planking_5": "SEVERS the crossing walkway at x 78.7..79.6: hem 1.28 m "
                                 "over walk surface 7.50, blocked at every walkable z. "
                                 "This script's own per-vertex ramp is the fix; owed a "
                                 "re-bake of crossing (and whichever of weave/cottage/"
                                 "lockhead the lift re-composes), which is why it is not "
                                 "in TARGETS yet",
    "t2c_W9_laundry_planking_4": "same row, hem 1.57 m over the same walkway — under a "
                                 "1.70 m body, inside _5's blocked span, same owed re-bake",
}

walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
TRIS = []
for o in walks:
    m, me = o.matrix_world, o.data
    for p in me.polygons:
        vs = [m @ me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            TRIS.append((vs[0], vs[k], vs[k + 1], o.name))


def walk_top(x, y, below):
    """Highest walk surface at (x, y) that is under `below`."""
    best, bn = None, None
    for a, b, c, nm in TRIS:
        d1 = (x - c[0]) * (a[1] - c[1]) - (a[0] - c[0]) * (y - c[1])
        d2 = (x - a[0]) * (b[1] - a[1]) - (b[0] - a[0]) * (y - a[1])
        d3 = (x - b[0]) * (c[1] - b[1]) - (c[0] - b[0]) * (y - b[1])
        if (d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0):
            continue
        n = (b - a).cross(c - a)
        if abs(n.z) < 1e-9:
            continue
        z = a.z - (n.x * (x - a.x) + n.y * (y - a.y)) / n.z
        if z <= below + 1e-6 and (best is None or z > best):
            best, bn = z, nm
    return best, bn


report = {}
print("=" * 78)
print("GATE CLOTH HEADROOM — lifting hanging cloth out of the walking corridor")
print("=" * 78)
for name in TARGETS:
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("%-24s NOT IN THIS BLEND — skipped" % name)
        report[name] = dict(present=False)
        continue
    M = ob.matrix_world
    Minv = M.inverted()
    ws = [M @ v.co for v in ob.data.vertices]
    zlo, zhi = min(v.z for v in ws), max(v.z for v in ws)
    # the floor under each vertex, and the lift that vertex needs
    lifts = []
    floors = []
    for p in ws:
        f, fn = walk_top(p.x, p.y, p.z)
        floors.append(f)
        lifts.append(0.0 if f is None else max(0.0, (f + WANT) - p.z))
    need = max(lifts) if lifts else 0.0
    clear_before = min((p.z - f) for p, f in zip(ws, floors) if f is not None) \
        if any(f is not None for f in floors) else None
    if need <= 1e-6:
        print("%-24s already clear (min %.3f m over its walk) — untouched"
              % (name, clear_before if clear_before is not None else float('nan')))
        report[name] = dict(present=True, moved=0, clearance_before=clear_before,
                            clearance_after=clear_before)
        continue
    # PER-VERTEX RAMP: a vertex at the bottom takes the whole lift, one at the top
    # takes none, so the cloth SHORTENS instead of floating.  Linear in the object's
    # own z span, which is what "hangs from its top edge" means.
    span = max(1e-6, zhi - zlo)
    moved = 0
    for v, p, lf in zip(ob.data.vertices, ws, lifts):
        t = (zhi - p.z) / span                     # 1 at the bottom, 0 at the top
        dz = need * t
        if dz <= 1e-6:
            continue
        v.co = Minv @ Vector((p.x, p.y, p.z + dz))
        moved += 1
    ob.data.update()
    ws2 = [ob.matrix_world @ v.co for v in ob.data.vertices]
    clear_after = min((p.z - f) for p, f in zip(ws2, floors) if f is not None)
    print("%-24s bottom edge %.3f -> %.3f ; clearance over its walk %.3f -> %.3f m "
          "(%d of %d verts raised, max lift %.3f m)"
          % (name, zlo, min(v.z for v in ws2), clear_before, clear_after,
             moved, len(ws2), need))
    report[name] = dict(present=True, moved=moved, verts=len(ws2),
                        z_before=[round(zlo, 4), round(zhi, 4)],
                        z_after=[round(min(v.z for v in ws2), 4),
                                 round(max(v.z for v in ws2), 4)],
                        clearance_before=round(clear_before, 4),
                        clearance_after=round(clear_after, 4),
                        max_lift=round(need, 4), want=WANT)

json.dump(dict(_doc=("GENERATED by tools/gate_cloth_headroom.py — hanging cloth over "
                     "the gate carriageway, raised to clear the walk corridor."),
               generator="tools/gate_cloth_headroom.py", want_clearance_m=WANT,
               targets=report, measured_not_fixed=UNFIXED), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, REPO))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
