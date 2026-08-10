"""emb_padlevel.py — A DOORSTEP TAKES ITS HEIGHT FROM THE ROAD IT STANDS ON, NOT FROM THE
HOUSE BEHIND IT.  This is the source reconciliation of Emberbrook's three walk heights.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_padlevel.py -- [save] [revert save] [census]
        [--nudge 0.004] [--minfrac 0.25] [--maxmove 0.25] [--force]

=============================== WHAT WAS MEASURED ================================

Round 2's headline, `tools/emb_padstack.mjs`: **106.0 m2 of Emberbrook's 1,510 m2 of
paving is TWO walk surfaces on one plan cell, at a median step of 70 mm**, because
`walk_pad_*` takes its height from `DOOR[i][2]` (the LANDMARK's own map z), `walk_e_*`
from a chaikin-smoothed chain of lane waypoints, and `walk_lm_*` from the area's own
floor — three sources, never compared.  Round 1 shipped a 4 mm nudge (the z-fighting 5%)
and round 2 a rim taper (the riser); both are CARRIERS on the SYMPTOM, and round 2 said
so: *"double coverage is unchanged at 106.0 m2 — it is a GENERATION fact."*

ROUND 3 DECOMPOSED THE 106.0 m2 BY MECHANISM, which nobody had:

    pad over ribbon   51.77 m2   83 pairs      <- a flat doorstep on a graded lane
    area over ribbon  34.69 m2   42 pairs      <- the 0.6 m rim overlap, by design
    area over pad      9.94 m2    9 pairs      <- the "coplanar" threshold, off by 70 mm
    pad over pad       5.02 m2    6 pairs
    ribbon over ribbon 4.57 m2   67 pairs      <- segment joints at corners
    area over area     0.02 m2    5 pairs

**66.7 m2 OF THE 106.0 IS A PAD**, and the mechanism is arithmetic: a ribbon starts at
`DOOR` with `DOOR`'s own z and then CLIMBS toward the next waypoint, while the pad is a
FLAT 3.0 m box centred on that same point — so at the pad's far edge the lane has gained
1.5 m x the local grade, which is the measured 70 mm.  And `emb_blockout`'s own comment on
the threshold pads says they are emitted *"coplanar with it, so `eff_top` still has nothing
to choose between"* — measured, the bakery's threshold stands **70 mm** over the plaza.

THE FIX IS ONE RULE, NOT THREE.  A pad's height is no longer an independent source: it is
read off the walk surface the pad actually stands on — the MEDIAN, over the pad's own plan
cells, of the highest OTHER walk surface there — plus `--nudge` (4 mm), which is round 1's
`emb_padcoplanar` result kept on purpose: two walk surfaces at exactly 0.000 m rendered as
a pitch-black hole (`walk_pad_lake-home`), so the target is FLUSH, never COINCIDENT.

MEASURED PREDICTION, ON THE SHIPPED BUNDLE, BEFORE ANY BLENDER RAN (`--sim` in this file's
sibling census; the same rasteriser `emb_padstack` uses):

    band          before    after
    <= 2 mm         5.20     6.86     the z-fight band, +1.66 (the nudge is a MEDIAN)
    2-20 mm         8.38    42.17     where the mass goes
    20-60 mm       28.79    30.02
    60-120 mm      38.05     3.66     THE MODAL BAND — the lit riser and its shadow line
    120-250 mm     11.40     9.11
    > 250 mm       14.20    14.20     real terraces, untouched by construction

A PAD WITH NOTHING UNDER IT IS NOT RECONCILED WITH ANYTHING and keeps its own height:
`--minfrac` of its cells must carry another walk surface (measured: eight of Emberbrook's
23 pads are the only walk surface on 100% of their own area).  A pad that would have to
move more than `--maxmove` is REFUSED AND PRINTED — that is a terrace, and lowering a
doorstep 0.3 m is a design change, not a fix.

WHAT IT DOES NOT DO.  It moves no vertex in x or y, adds and removes no geometry, and
changes no mesh's name, so the walk network's EXTENT is identical to the metre and
`scenegraph_derive`'s door triggers and return spawns keep their pads.  It never touches a
ribbon or an area floor: those two are each internally consistent, and the pad is the one
of the three sources that is derived from something that is not a walk surface at all.

ORDER, ASSERTED.  `emb_pavechop` seats each pad's rim onto the ground/paving under it, so
this must run BEFORE it or the seat would be carried up or down with the plate.  Per blend:
`emb_pavechop -- revert save`, `emb_padfill`, this, then `emb_pavechop -- save`.  Aborts if
any walk mesh still carries pavechop's `embpc`.

`revert save` restores every moved vertex (the `embpl` snapshot).  Not idempotent by
construction — a second run would re-derive against the already-moved pad — so a blend
carrying the snapshot aborts unless `--force`.
"""
import bpy, sys, os, json, math

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(REPO, "tools/blends/districts/emb_padlevel.%s.json"
                        % os.path.splitext(os.path.basename(bpy.data.filepath or "unknown"))[0])
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
CENSUS = "census" in argv
FORCE = "--force" in argv


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


NUDGE = float(opt("--nudge", "0.004"))
MINFRAC = float(opt("--minfrac", "0.25"))
MAXMOVE = float(opt("--maxmove", "0.25"))
CELL = 0.05
UP_DOT = 0.5
PROP = "embpl"
sc = bpy.context.scene

if REVERT:
    n = 0
    for o in list(sc.objects):
        if o.type != 'MESH' or not o.get(PROP):
            continue
        st = json.loads(o[PROP])
        for i, z in st["z"]:
            o.data.vertices[i].co.z = z
        o.data.update()
        del o[PROP]
        n += 1
    print("reverted %d pad(s)" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

WALK = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith("walk_")]
assert WALK, "no walk_* meshes in this blend"
held = [o.name for o in WALK if o.get("embpc")]
assert FORCE or not held, (
    "%d walk mesh(es) carry emb_pavechop's 'embpc' snapshot — pavechop has already seated "
    "these rims and this file would carry the seat with the plate. Run "
    "`-P tools/emb_pavechop.py -- revert save` first.\n  %s" % (len(held), ", ".join(held[:5])))
heldme = [o.name for o in WALK if o.get(PROP)]
assert FORCE or not heldme, (
    "%d pad(s) already carry the '%s' snapshot — run `-- revert save` first"
    % (len(heldme), PROP))


def top_faces(o):
    me = o.data
    M = o.matrix_world
    N = M.to_3x3().inverted().transposed()
    plus, minus = [], []
    for p in me.polygons:
        nz = (N @ p.normal).normalized().z
        if nz > UP_DOT:
            plus.append(p.index)
        elif nz < -UP_DOT:
            minus.append(p.index)

    def meanz(idxs):
        if not idxs:
            return -1e9
        vs = [v for i in idxs for v in me.polygons[i].vertices]
        return sum((M @ me.vertices[v].co).z for v in vs) / len(vs)
    return plus if meanz(plus) > meanz(minus) else minus


# --- every walk surface's top, on one plan grid -------------------------------
GRID = {}
for o in WALK:
    me = o.data
    M = o.matrix_world
    for pi in top_faces(o):
        vs = [M @ me.vertices[v].co for v in me.polygons[pi].vertices]
        x0 = min(v.x for v in vs); x1 = max(v.x for v in vs)
        y0 = min(v.y for v in vs); y1 = max(v.y for v in vs)
        z = max(v.z for v in vs)
        for i in range(int(math.floor(x0 / CELL)), int(math.floor(x1 / CELL)) + 1):
            for j in range(int(math.floor(y0 / CELL)), int(math.floor(y1 / CELL)) + 1):
                cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
                if not (x0 - 1e-9 <= cx <= x1 + 1e-9 and y0 - 1e-9 <= cy <= y1 + 1e-9):
                    continue
                d = GRID.setdefault((i, j), {})
                if z > d.get(o.name, -1e9):
                    d[o.name] = z

print("=" * 78)
print("emb padlevel — a doorstep takes its height from the road it stands on")
print("blend %s   nudge %.4f m   minfrac %.2f   maxmove %.2f m"
      % (bpy.data.filepath, NUDGE, MINFRAC, MAXMOVE))
print("=" * 78)

PADS = sorted([o for o in WALK if o.name.startswith("walk_pad_")], key=lambda o: o.name)
report = {"blend": bpy.data.filepath, "nudge": NUDGE, "pads": []}
moved = alone = refused = 0
for o in PADS:
    me = o.data
    M = o.matrix_world
    own = set()
    for pi in top_faces(o):
        vs = [M @ me.vertices[v].co for v in me.polygons[pi].vertices]
        x0 = min(v.x for v in vs); x1 = max(v.x for v in vs)
        y0 = min(v.y for v in vs); y1 = max(v.y for v in vs)
        for i in range(int(math.floor(x0 / CELL)), int(math.floor(x1 / CELL)) + 1):
            for j in range(int(math.floor(y0 / CELL)), int(math.floor(y1 / CELL)) + 1):
                cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
                if x0 - 1e-9 <= cx <= x1 + 1e-9 and y0 - 1e-9 <= cy <= y1 + 1e-9:
                    own.add((i, j))
    if not own:
        continue
    unders, who = [], {}
    for k in own:
        others = [(nm, z) for nm, z in GRID.get(k, {}).items() if nm != o.name]
        if not others:
            continue
        nm, z = max(others, key=lambda t: t[1])
        unders.append(z)
        who[nm] = who.get(nm, 0) + 1
    frac = len(unders) / len(own)
    ztop = max((M @ v.co).z for v in me.vertices)
    if frac < MINFRAC:
        alone += 1
        print("  %-30s ALONE — %.0f%% of its %.2f m2 has another walk surface under it "
              "(< %.0f%%); nothing to reconcile with, height kept"
              % (o.name, 100 * frac, len(own) * CELL * CELL, 100 * MINFRAC))
        continue
    unders.sort()
    target = unders[len(unders) // 2] + NUDGE
    dz = target - ztop
    src = ", ".join("%s %.0f%%" % (n, 100 * c / len(own))
                    for n, c in sorted(who.items(), key=lambda t: -t[1])[:2])
    if abs(dz) > MAXMOVE:
        refused += 1
        print("  %-30s REFUSED — would move %+.3f m (> --maxmove %.2f). That is a "
              "terrace, not a step; %s" % (o.name, dz, MAXMOVE, src))
        continue
    print("  %-30s %+.4f m   %.0f%% covered, over %s" % (o.name, dz, 100 * frac, src))
    report["pads"].append({"pad": o.name, "dz": dz, "frac": frac, "over": src})
    moved += 1
    if CENSUS:
        continue
    snap = [[v.index, v.co.z] for v in me.vertices]
    o[PROP] = json.dumps({"z": snap})
    # the pad's own transform may scale z; move in LOCAL units so the world delta is dz
    sz = M.col[2].to_3d().length or 1.0
    for v in me.vertices:
        v.co.z += dz / sz
    me.update()

print("-" * 78)
print("%d pad(s) levelled onto the walk surface under them, %d left ALONE (nothing under "
      "them), %d REFUSED as terraces" % (moved, alone, refused))
report["moved"] = moved
report["alone"] = alone
report["refusedTerrace"] = refused
if CENSUS:
    print("(census only — nothing written)")
    sys.exit(0)
os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
json.dump(report, open(MANIFEST, "w"), indent=1)
print("manifest %s" % MANIFEST)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
