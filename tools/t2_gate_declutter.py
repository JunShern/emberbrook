"""t2_gate_declutter.py — THE FIVE PIECES OF ROOF MATERIAL HANGING ABOUT THE ENTRANCE.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_gate_declutter.py -- [dry|save]

USER, on the first walking-in entrance frame (2026-08-01): "a scattering of five
different pieces of random roof material just hanging about" in the arrival area, and
the cliff-hugging structures' roofs are FINE — it is the disconnected pieces.

THE FIVE ARE NAMED, NOT GUESSED. Every thin roof-stock panel standing over the porters'
yard inside the chosen frustum, with its vertex count and a 5 x 5 down-ray census of its
own footprint (`supported` = a surface within 3.2 m, `void` = nothing for 30 m):

    t2c_G6_tarps_cargo      4 verts   2.60 x 2.60 quad   0/25 touching, gap 0.40 m
    t2c_GB4_yard_tarp_big  20 verts   4.80 x 4.00        measured below
    t2c_G1_awning_porters_a 24 verts  3.00 x 2.25        18/25 supported, 7/25 VOID (31.85 m)
    t2c_G2_awning_porters_b 24 verts  3.00 x 2.25        25/25 supported on gate_ground
    t2c_G3_awning_tollyard  80 verts  1.61 x 1.28        24/25 supported on gate_ground

PROVENANCE DECIDES IT, and it is written down in the file that placed them.
`tools/t2_color_pops.py` placed G1, G2, G6 and GB4 from SCREEN-SPACE PROBE RECTANGLES —
its successor's docstring says the quiet part out loud: rectangles "that carried no idea
of what was UNDER them". They were placed to put pops of colour in the OLD gate vista,
the frame the user has now rejected. `t2_gate_awnings.py` is the exception: G3 was
re-seated onto a SEARCHED site against measured ground, and it is the only one of the
five built to a rule.

WHAT THIS SCRIPT DOES, and the rule it follows: a canopy stays if its whole footprint is
carried (0 void samples) AND it is more than a bare quad. So

    CULL   t2c_G6_tarps_cargo      a 4-vertex sheet floating 0.40 m over the walk pad
    CULL   t2c_GB4_yard_tarp_big   (verdict computed at run time, printed)
    CULL   t2c_G1_awning_porters_a a third of it oversails a 31.85 m drop
    KEEP   t2c_G2_awning_porters_b fully carried, and it reads as built
    KEEP   t2c_G3_awning_tollyard  the searched one

Deterministic: an explicit name list, no randomness, no search. Re-running it after the
cull is a no-op and says so.
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
BLEND = bpy.data.filepath

# object -> (who placed it, was its placement rule GROUND-TESTED?)
# "pops" = tools/t2_color_pops.py, screen-space probe rectangles against the OLD gate
#          vista, which the user rejected on 2026-08-01. Not ground-tested; its own
#          successor's docstring says the rectangles "carried no idea of what was UNDER
#          them". The frame those four were composed for no longer exists.
# "searched" = tools/t2_gate_awnings.py, a five-constraint site search against measured
#          ground and 100 camera->staircase sightlines. Still a valid rule.
PROVENANCE = {
    "t2c_G6_tarps_cargo":      ("pops", False),
    "t2c_GB4_yard_tarp_big":   ("pops", False),
    "t2c_G1_awning_porters_a": ("pops", False),
    "t2c_G2_awning_porters_b": ("pops", False),
    "t2c_G3_awning_tollyard":  ("searched", True),
}
CANDIDATES = list(PROVENANCE)
SUPPORT = 3.2                      # a canopy's own posts are shorter than this

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

def census(o):
    ws = [o.matrix_world @ Vector(v) for v in o.bound_box]
    x0, x1 = min(w.x for w in ws), max(w.x for w in ws)
    y0, y1 = min(w.y for w in ws), max(w.y for w in ws)
    zmin = min(w.z for w in ws)
    sup = void = deep = 0
    gap = 1e9
    for i in range(5):
        for j in range(5):
            px = x0 + (x1 - x0) * (0.1 + 0.2 * i)
            py = y0 + (y1 - y0) * (0.1 + 0.2 * j)
            hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector((px, py, zmin - 0.03)),
                                                    Vector((0, 0, -1)), distance=30.0)
            if not hit: void += 1
            else:
                d = zmin - loc.z
                gap = min(gap, d)
                if d <= SUPPORT: sup += 1
                else: deep += 1
    return dict(verts=len(o.data.vertices), zmin=round(zmin, 2),
                dims=[round(x1 - x0, 2), round(y1 - y0, 2),
                      round(max(w.z for w in ws) - zmin, 2)],
                supported=sup, deep=deep, void=void,
                gap=None if gap > 1e8 else round(gap, 2))

print("=" * 78)
print("THE ENTRANCE DECLUTTER — five roof panels, measured before any of them moves")
print("=" * 78)
print("%-26s %5s %-20s %5s %5s %7s %-9s  verdict" %
      ("object", "verts", "dims", "sup", "void", "minGap", "placed by"))
doomed = []
for n in CANDIDATES:
    o = bpy.data.objects.get(n)
    if not o:
        print("%-26s  ALREADY GONE (this pass has run before)" % n)
        continue
    c = census(o)
    who, grounded = PROVENANCE[n]
    bare = c["verts"] <= 8                      # a quad with nothing holding it
    overvoid = c["void"] >= 3                   # >= 12% of the footprint over the gorge
    # THE RULE, and it is provenance first: a prop whose ONLY justification was a frame
    # that has been retired has no standing in the frame that replaced it. The two
    # geometric tests are recorded beside it because two of these fail on their own terms
    # as well, and the next reader should be able to see which argument did the work.
    keep = grounded
    why = ("KEEP — searched site, ground-tested rule" if grounded else
           "CULL — placed for the retired vista" +
           (" + bare quad" if bare else "") +
           (" + %d/25 of footprint over void" % c["void"] if overvoid else ""))
    if not keep: doomed.append(n)
    print("%-26s %5d %-20s %5d %5d %7s %-9s  %s" %
          (n, c["verts"], str(c["dims"]), c["supported"], c["void"], c["gap"], who, why))

print("\nculling %d of %d: %s" % (len(doomed), len(CANDIDATES), ", ".join(doomed) or "nothing"))
for n in doomed:
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
left = [o.name for o in bpy.data.objects if o.name.startswith("t2c_G") and o.type == 'MESH']
print("t2c_G* remaining in the master: %d — %s" % (len(left), ", ".join(sorted(left))))

if SAVE and doomed:
    bpy.ops.wm.save_mainfile(filepath=BLEND)
    print("SAVED %s" % BLEND)
else:
    print("DRY RUN — pass 'save' to write the master")
