"""door_legibility.py — EVERY ENTERABLE SHOP FRONT READS AS A DOOR (graphics round 1).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/door_legibility.py -- [save]

WHY.  Red-team sweep 20260806-1 (docs/qa/redteam/run-20260806-1-findings.md) upheld
door illegibility on every named shop front the checklist asked about — weapon shop
"darkened wall opening lacks clear door framing or interactive cues", cookhouse
"recessed doorway ... too dark and merges into the surrounding shadowed wood",
Boatmen's Rest / item shop / armor shop "obscured in shadow" — and the user's own
round-1 complaint (5) is the same sentence: every enterable front should read as an
entrance a player recognizes.  Measured on the plates: each doorway today is
`doorway()`'s dark `mat_timber_dark` slab on a dark wall, distinguishable only by
geometry the street shadow erases.

WHAT.  A CARRIER in the gate_rimchop class: ADDITIVE ONLY, onto the live master.
For each of the five enterable fronts it builds, in collection DOOR_LEGIBILITY
(prefix `df_<shop>_`):
  * a PAINTED door panel proud of the existing slab (each shop's own accent paint —
    the door joins the sign in carrying the shop's identity), with plank rails and
    an iron handle;
  * a LIGHT `mat_freshwood` frame — jambs + lintel — the contrast element that
    survives shadow;
  * a stone threshold at the measured street level;
  * a WARM GLOW: a transom light over the door where headroom exists, else two lit
    panes in the door's upper half — the same `mat_*_window_a` emission the town's
    lit windows already bake with, so the read is "someone is in" at exactly the
    strength the plates already speak.
Nothing is deleted, moved or renamed; the old slab stays as the panel's shadow gap.
A re-run replaces the DOOR_LEGIBILITY collection (idempotent).

THE GATE.  The script re-measures the street under each door and REFUSES if it
disagrees with the recorded level (a moved district invalidates the carrier), and
after building it ray-casts each door panel from its OWNING solved camera and
reports what a player of that plate actually first-hits — the occlusion truth the
checklist argued about, measured in the same session that built the fix.
"""
import bpy, sys, json, math
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import obox, beam, cyl, M

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
COLL = "DOOR_LEGIBILITY"

# shop, door centre (slab centre, from the district builders), face, w, h,
# measured street z (2026-08-06, down-probe on the live master), door-bottom z,
# panel paint, glow material, stone, owning camera
DOORS = [
    ("inn",       25.32,  3.80, 'x-', 1.05, 2.05, 19.77, "mat_shelf_paint_madder",
     "mat_shelf_window_a", "mat_shelf_stone", "shelf-west"),
    ("item",      31.35,  5.87, 'y+', 1.02, 2.05, 19.01, "mat_shelf_paint_ochre",
     "mat_shelf_window_a", "mat_shelf_stone", "shelf-west"),
    ("weapon",    36.15,  8.63, 'y-', 1.10, 2.10, 19.02, "mat_shelf_paint_slate",
     "mat_shelf_window_a", "mat_shelf_stone", "shelf-east"),
    ("armor",     43.50, 10.73, 'y-', 1.08, 2.08, 19.04, "mat_shelf_paint_teal",
     "mat_shelf_window_a", "mat_shelf_stone", "shelf-east"),
    ("cookhouse", 39.85, 12.94, 'y-', 1.10, 2.10, 13.99, "mat_qm_paint_bone",
     "mat_qm_window_a",    "mat_qm_stone",    "quay-west"),
]

MFRESH, MTD, MIRON = M("mat_freshwood"), M("mat_timber_dark"), M("mat_iron")
assert MFRESH and MTD and MIRON, "town materials missing"

# idempotent: a re-run replaces the treatment, never stacks a second one
old = bpy.data.collections.get(COLL)
if old:
    for o in list(old.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("REBUILD   %-28s previous door treatment cleared" % COLL)

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
cams_pre = {c["id"]: c for c in json.load(
    open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))["cameras"]}


def axes(face):
    s = -1.0 if face[1] == '-' else 1.0
    if face[0] == 'x':
        return Vector((s, 0, 0)), Vector((0, 1, 0))       # out, along
    return Vector((0, s, 0)), Vector((1, 0, 0))


made = []


def mk(ob):
    made.append(ob)
    return ob


print("=" * 78)
print("DOOR LEGIBILITY — five enterable fronts, carrier onto the live master")
print("=" * 78)

for shop, cx, cy, face, w, h, ref_street, paint_n, glow_n, stone_n, cam_id in DOORS:
    out, along = axes(face)
    PAINT, GLOW, STONE = M(paint_n), M(glow_n), M(stone_n)
    assert PAINT and GLOW and STONE, "%s: materials %s/%s/%s missing" % (
        shop, paint_n, glow_n, stone_n)

    # ---- gate 1: the street is where the carrier recorded it
    HITS = []
    p = Vector((cx, cy, 0)) + out * 0.55
    z = 40.0
    for _ in range(24):
        hit, loc, _, _, ob, _ = sc.ray_cast(dg, Vector((p.x, p.y, z)),
                                            Vector((0, 0, -1)), distance=60)
        if not hit:
            break
        HITS.append((loc.z, ob.name))
        z = loc.z - 0.03
    near = [hz for hz, _ in HITS if abs(hz - ref_street) < 0.60]
    assert near, ("%s: no surface within 0.6 m of recorded street z %.2f — the "
                  "district moved; re-measure before carrying" % (shop, ref_street))
    street = max(near)
    assert abs(street - ref_street) < 0.08, \
        "%s: street z drifted %.2f -> %.2f" % (shop, ref_street, street)
    bot = street + 0.04                       # door bottom, just over the pavement

    def P(a, o, zz):
        """world point from (along, out, z) relative to the slab centre"""
        return (cx + along.x * a + out.x * o, cy + along.y * a + out.y * o, zz)

    def OB(tag, a, o, zz, sa, so, sz, mat):
        """axis-aligned box sized (along, out, z) centred at (a, o, zz)"""
        wx, wy, wz = P(a, o, zz)
        sx, sy = (sa, so) if face[0] == 'y' else (so, sa)
        return mk(obox("df_%s_%s" % (shop, tag), wx, wy, wz, sx, sy, sz,
                       mat=mat, cname=COLL))

    # ---- gate 2: headroom for a transom, measured not assumed
    hp = P(0, 0.25, bot + h + 0.20)
    up_hit, up_loc, _, _, up_ob, _ = sc.ray_cast(dg, Vector(hp), Vector((0, 0, 1)),
                                                 distance=8.0)
    clear = (up_loc.z - hp[2]) if up_hit else 8.0
    transom = clear >= 0.62

    # ---- the painted panel, proud of the old slab (slab face is at out 0.07)
    OB("panel", 0, 0.105, bot + (h - 0.05) / 2 + 0.01, w - 0.06, 0.055, h - 0.05, PAINT)
    for i, fz in enumerate((0.30, 0.72)):
        OB("rail%d" % i, 0, 0.140, bot + h * fz, w - 0.34, 0.022, 0.13, MTD)
    hx, hy, hz2 = P(w / 2 - 0.22, 0.155, bot + 1.02)
    mk(cyl("df_%s_handle" % shop, (hx, hy, hz2 - 0.05), (hx, hy, hz2 + 0.05),
           0.035, 8, MIRON, COLL))

    # ---- the light frame.  IN-FRAME pilasters, not proud side-jambs: these
    # shopfronts pack windows 15-25 cm off the door edges (armor's window frame
    # OVERLAPS its door slab), so anything outside the doorway footprint clips
    # built art.  Pilasters at the panel's own edges frame the door with zero
    # collision risk by construction; the outer lintel only where headroom
    # (measured above) actually exists.
    for s in (-1.0, 1.0):
        OB("pilaster%s" % ('l' if s < 0 else 'r'), s * (w / 2 - 0.055), 0.125,
           bot + h / 2, 0.11, 0.045, h, MFRESH)
    OB("head", 0, 0.125, bot + h - 0.055, w - 0.06, 0.045, 0.11, MFRESH)
    if not transom and clear >= 0.20:
        OB("lintel", 0, 0.055, bot + h + 0.17 + min(0.15, clear - 0.05) / 2,
           w + 0.44, 0.18, min(0.15, clear - 0.05), MFRESH)

    if transom:
        OB("transom", 0, 0.020, bot + h + 0.38, w - 0.10, 0.05, 0.34, GLOW)
        for k in (-1, 0, 1):
            OB("muntin%d" % (k + 1), k * (w - 0.10) / 3.4, 0.045,
               bot + h + 0.38, 0.045, 0.06, 0.34, MTD)
        OB("lintel", 0, 0.055, bot + h + 0.62, w + 0.44, 0.18, 0.14, MFRESH)
    else:
        # NAMING: pane_l, never "pane"+"l" — "panel" collides with the door
        # panel's own name and Blender silently mints a .001 (caught in the
        # 2026-08-06 townwalk export)
        # PANE HEIGHT IS MEASURED AGAINST THE OWNING CAMERA: at 1.58 the weapon
        # shop's panes sat exactly behind strung lantern shelf_lantern_hang_8
        # (pixel probe, shelf-east px 1182,460..480) — the one glow element the
        # treatment exists for, occluded by a 20 cm lantern 5 m out of frame
        # centre.  The carrier drops to 1.30 when the 1.58 centre's ray from the
        # owning camera first-hits anything that is not this door or its shop.
        pz = 1.58
        ppos = Vector(P(0, 0.16, bot + pz))
        cpos = Vector(cams_pre[cam_id]["pos"]) if cam_id in cams_pre else None
        if cpos is not None:
            dvec = ppos - cpos
            phit, ploc, _, _, pob, _ = sc.ray_cast(dg, cpos, dvec.normalized(),
                                                   distance=dvec.length - 0.05)
            if phit and not pob.name.startswith("df_%s" % shop):
                pz = 1.30
                print("    %s: pane 1.58 occluded by %s from %s -> lowered to 1.30"
                      % (shop, pob.name, cam_id))
        for k in (-1.0, 1.0):
            OB("pane_%s" % ('l' if k < 0 else 'r'), k * w * 0.20, 0.140,
               bot + pz, 0.24, 0.03, 0.34, GLOW)
            OB("panebar_%s" % ('l' if k < 0 else 'r'), k * w * 0.20, 0.150,
               bot + pz, 0.26, 0.02, 0.05, MTD)

    # ---- the stone threshold at the measured street
    OB("step", 0, 0.115, (street - 0.14 + bot) / 2 + 0.01, w + 0.34, 0.36,
       bot - street + 0.16, STONE)

    print("  %-10s street %6.2f  bot %6.2f  headroom %4.2f -> %s" % (
        shop, street, bot, clear, "TRANSOM glow" if transom else "LIT PANES"))

# --------------------------------------------------------------- visibility
print("\nWHAT THE OWNING PLATE'S CAMERA FIRST-HITS AT EACH PANEL (occlusion truth):")
solved = json.load(open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))
cams = {c["id"]: c for c in solved["cameras"]}
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for shop, cx, cy, face, w, h, ref_street, *_rest in DOORS:
    cam_id = _rest[-1]
    out, along = axes(face)
    c = cams[cam_id]
    cpos = Vector(c["pos"])
    tgt = Vector((cx, cy, ref_street + 1.2)) + out * 0.20
    d = (tgt - cpos)
    hit, loc, _, _, ob, _ = sc.ray_cast(dg, cpos, d.normalized(), distance=d.length + 5)
    seen = ob.name if hit else "nothing"
    verdict = "DOOR VISIBLE" if (hit and (ob.name.startswith("df_%s" % shop))) else \
              ("occluded by " + seen if hit and (loc - tgt).length > 0.35 else "front face: " + seen)
    print("  %-10s from %-10s -> %-32s %s" % (shop, cam_id, seen, verdict))

print("\n%d objects in %s" % (len(made), COLL))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
