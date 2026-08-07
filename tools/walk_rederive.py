"""walk_rederive.py — re-derive a NAMED map edge's walk records into the master.

    Blender -b tools/blends/dellhollow-master.blend -P tools/walk_rederive.py \
        --python-exit-code 1 -- --edge valley-gate__winch-head [save]
    Blender -b tools/blends/dellhollow-master.blend -P tools/walk_rederive.py \
        --python-exit-code 1 -- --report            # what is stale, nothing touched
    Blender ... -- --edge <a__b> revert             # put the snapshots back

WHY THIS EXISTS, AND WHY IT IS NOT `ls_reorigin.py`.  That tool is this idea's first
instance, hardcoded to one edge (`shelf-homes__quay-deck` -> `loop-landing__quay-deck`)
because at the time there was exactly one.  Its own docstring set the rule for what to do
when a third appeared: put it in a general place rather than adding a third special case.
This is that general place.  `ls_reorigin.py` is DELETED (2026-08-07, with Bet 2's
loop-landing branch — map note `_bet2_2026-08-06b`): the edge it owned is gone, so the
fork-specific rail gap it carried retired with it.  Mentions of it below are history.

THE HOLE IT FILLS is CLAUDE.md's own doctrine: "a conflict fix is a landmark move or a
lane waypoint — ONE LINE OF MAP, ONE COMMAND TO RE-DERIVE."  `town_blockout.py` raises
the whole town into a SEPARATE blend and wipes the scene doing it; every district builder
is additive and reads the walk network as given.  So a map walk-record change has nowhere
to land in the master, which is how `dellhollow-town.blend` came to be six hours older
than its map with stale `bar_` rails across five districts.

WHAT IT DOES.  Nothing is reimplemented: `town_blockout.py` regenerates the blockout from
the stamped map and this APPENDS the named edge's records out of that blend, so the new
ribbons are bit-identical to a full blockout's.  There is no second generator to drift.

THREE THINGS IT CHECKS THAT A NAIVE COPY WOULD NOT:

 1  PEER SETTINGS COME FROM THE RECORDS BEING REPLACED, not from an assumption.  The
    outgoing objects are read for collection / hide_render / hide_viewport / materials
    BEFORE they are withdrawn, and the incoming ones are given exactly those, per class
    (`walk_` and `bar_` differ: a bar_ is render-hidden, a walk_ is not necessarily).
    An imported record that renders is the mistake the crossing already taught.

 2  A `bar_` IS NOT NON-SOLID.  play3d.html's `noStand` list is water_/lm_/veg_ only, so
    a bar_ blocks the body exactly like a wall.  Re-deriving an edge can therefore lay an
    INVISIBLE WALL across a way on — the loop-stairs fork's defect, found only by walking
    it with a body box.  Every rebuilt `bar_` is swept against every OTHER edge's walk
    ribbon here, offline, and any crossing is reported loudly with its position.  A
    crossing is not auto-cut: cutting one is a judgement (the loop-stairs gap needed to
    keep the rest of the rail), and a tool that silently deletes collision is worse than
    one that tells you where to look.

 3  THE DEPSGRAPH TRAP, twice-learned in ls_reorigin: a just-appended object's
    `matrix_world` is IDENTITY until the view layer is updated, so anything measured
    before that reads a unit cube at the origin.  Update first, measure second — and an
    assert holds it, because the first time this was missed the tool printed "NO RAIL
    CROSSED THE FORK" while a rail stood across the stair.

IDEMPOTENT AND REVERTIBLE.  Outgoing objects are snapshotted as WRD_SRC_* with a fake
user AND a record of their collections, because restore means RE-LINK, not just rename:
an object in no collection with no fake user has zero users and Blender garbage-collects
it on the next save (ls_reorigin destroyed twenty that way once).  A second run against
an already-current edge is a no-op.

WHAT IT DOES NOT MOVE: `lm_*` blockout massing (the master carries zero — every one has
been replaced by real art) and `walk_pad_*` for portal landmarks where a landing mesh
already covers the landmark.  Both are ls_reorigin's documented exceptions and both are
re-stated here as skips rather than silently inherited.

`--lm <id>` — A LANDMARK PAD IS A RECORD WITH NO EDGE (added 2026-08-01).  `walk_lm_*`
carries no `a__b` in its name, so `--edge` cannot name one and the report files them under
"(no edge)".  The footprint ruling made that a live case: a class-`area` landmark's pad is
now derived from its measured `footprint` rect-list rather than from `extent`, and the
four waterfront pads had to reach the master.  The job is IDENTICAL in every other respect
— the blockout is still the only generator, peer settings still come from the records being
replaced, the snapshot/revert path is the same — so this is one more selector, not a second
code path.  A landmark job carries no `bar_` records, so the invisible-wall sweep has
nothing to sweep for it and says so.
"""
import bpy, bmesh, json, sys, os, math
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg/"
MASTER = ROOT + "tools/blends/dellhollow-master.blend"
BLOCKOUT = ROOT + "tools/blends/dellhollow-town.blend"
MAP = json.load(open(ROOT + "public/townmap/dellhollow.map.json"))
SNAP = "WRD_SRC_"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


SAVE = "save" in argv
REVERT = "revert" in argv
REPORT = "--report" in argv
EDGES = [e for e in (arg("--edge") or "").split(",") if e]
LMS = [l for l in (arg("--lm") or "").split(",") if l]
# `--drop` — THE MAP DELETED SOMETHING (added 2026-08-02).  Every other selector asks
# "re-derive this thing from the current map"; a landmark or an edge the map no longer
# has cannot be named that way (`--edge` asserts the id exists, and `edge_of` cannot
# match a name against an edge list that no longer contains it), so its records simply
# stayed in the master and reported as "EXTRA" for ever.  That is not cosmetic: the gate
# tier's carriageway is laid ON the walk graph, so an orphaned 8 x 8 m `walk_lm_` disc
# went on paving a plaza in the frame after the map said the yard was gone.  A drop is
# the same operation as a re-derive with an empty right-hand side, and it uses the same
# snapshot/withdraw path, so `revert` restores it.
DROPS = [d for d in (arg("--drop") or "").split(",") if d]

EDGE_IDS = {"%s__%s" % (e["from"], e["to"]): e for e in MAP["edges"]}
LM_IDS = {l["id"]: l for l in MAP["landmarks"]}


def log(kind, what, why=""):
    print("  %-10s %-46s %s" % (kind, what, why))


def rec_key(o):
    """A record's identity for comparison: name + world verts rounded to 1e-4.

    CONTENT, not the datablock — the master and the blockout are different files and a
    byte compare is meaningless across them (the same reason embint_verify.py digests
    content rather than bytes).
    """
    mw = o.matrix_world
    vs = sorted(tuple(round(c, 4) for c in (mw @ v.co)) for v in o.data.vertices)
    return (len(o.data.vertices), vs)


def edge_of(name):
    """Which map edge does this record belong to?  Longest match wins, so
    `valley-gate__winch-head` is not matched by a shorter sibling."""
    best = None
    for eid in EDGE_IDS:
        if eid in name and (best is None or len(eid) > len(best)):
            best = eid
    return best


def group_of(name):
    """The JOB a record belongs to, for the report: an edge, or a landmark pad.

    Landmark pads used to file under "(no edge)" together with anything else the edge
    match missed, which is where the four stilt-waterfront pads were hiding.  A pad has an
    owner and the report should name it.
    """
    e = edge_of(name)
    if e:
        return e
    for pfx in ("walk_lm_", "walk_pad_"):
        if name.startswith(pfx) and name[len(pfx):] in LM_IDS:
            return "lm:" + name[len(pfx):]
    return "(no edge)"


def records_of(job):
    """The record-name predicate for one job id — `a__b` (edge) or `lm:<id>` (pad).

    A LANDMARK OWNS TWO POSSIBLE RECORD NAMES and only one of them ever exists: a
    class-`area` landmark derives `walk_lm_<id>` (the filled footprint), and a
    structure / prop / portal derives `walk_pad_<id>` (the 2.6 m threshold landing,
    town_blockout's second landmark loop).  Matching both is what lets `--lm` install
    a brand-new portal's pad — which is how the gate's overworld exit got moved onto
    the valley road's mouth — without a second selector that means the same thing.
    """
    if job.startswith("lm:"):
        targets = {"walk_lm_" + job[3:], "walk_pad_" + job[3:]}
        return lambda n: n in targets
    return lambda n: edge_of(n) == job


def dropped_records(job):
    """The record-name predicate for a job the map NO LONGER HAS.

    `edge_of` resolves against the CURRENT map, so it cannot name a deleted edge;
    this matches on the name the blockout would have given, which is the only thing
    left to go on once the map entry is gone.
    """
    if job.startswith("lm:"):
        targets = {"walk_lm_" + job[3:], "walk_pad_" + job[3:]}
        return lambda n: n in targets
    return lambda n: (n.startswith("walk_e_" + job) or n.startswith("bar_e_" + job))


# =========================================================================== revert
def do_revert(edges):
    back = 0
    for o in list(bpy.data.objects):
        if not o.name.startswith(SNAP):
            continue
        real = o.name[len(SNAP):]
        if edges and edge_of(real) not in edges:
            continue
        # remove whatever currently holds the name, then restore
        cur = bpy.data.objects.get(real)
        if cur is not None and cur is not o:
            bpy.data.objects.remove(cur, do_unlink=True)
        o.name = real
        linked = False
        for cn in list(o.get("wrd_colls", [])):
            c = bpy.data.collections.get(cn)
            if c and o.name not in c.objects:
                c.objects.link(o)
                linked = True
        if not linked:
            bpy.context.scene.collection.objects.link(o)
        if "wrd_colls" in o:
            del o["wrd_colls"]
        o.use_fake_user = False          # safe ONLY now that it has a real user
        back += 1
    print("REVERTED — %d snapshot(s) restored AND re-linked" % back)
    if back == 0:
        print("  NOTE: no snapshots. The master is git-tracked: "
              "`git checkout tools/blends/dellhollow-master.blend`.")
    return back


# =========================================================================== report
def snapshot_master():
    """The master's OWN records, captured BEFORE anything is appended.

    THIS ORDER IS THE WHOLE CORRECTNESS OF THE REPORT and the first version got it
    wrong: appending first puts the blockout's objects into `bpy.data.objects`, so a
    master index built afterwards contains them too and every record is compared with
    ITSELF — 0 stale, 0 missing, and the master's real contents reported as "extra".
    The numbers looked clean and meant nothing. Capture first, append second.
    """
    return {o.name: (rec_key(o), o) for o in bpy.data.objects
            if o.name.startswith(("walk_", "bar_")) and not o.name.startswith(SNAP)}


def load_blockout_index():
    """true blockout name -> (content key, appended object).

    NAME COLLISIONS ARE THE SECOND TRAP.  Every record we want already exists in the
    master by the same name, so Blender suffixes each appended object `.001`. Matching
    on the object's own `.name` would therefore compare `..._l0.001` against nothing.
    `bpy.data.libraries.load` fills `dst.objects` IN THE ORDER OF THE REQUESTED NAMES,
    so the true name is recovered by zipping the two — never by stripping a suffix,
    which would be guessing.
    """
    with bpy.data.libraries.load(BLOCKOUT, link=False) as (src, dst):
        wanted = sorted(n for n in src.objects if n.startswith(("walk_", "bar_")))
        dst.objects = list(wanted)
    loaded = list(dst.objects)
    assert len(loaded) == len(wanted), (
        "loader returned %d objects for %d requested names — the order-zip below would "
        "mis-associate them" % (len(loaded), len(wanted)))
    # THE DEPSGRAPH TRAP, third instance: `view_layer.update()` is NOT enough on its own.
    # An appended object that is in no collection is not in the view layer at all, so it
    # never evaluates and `matrix_world` stays identity — every record reads as a unit
    # cube at the origin. It has to be LINKED first, then updated, then measured. The
    # assert below is what caught this, which is the whole reason it is an assert.
    tmp = bpy.data.collections.get("WRD_STAGING") or bpy.data.collections.new("WRD_STAGING")
    if tmp.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(tmp)
    for o in loaded:
        if o is not None and o.name not in tmp.objects:
            tmp.objects.link(o)
    bpy.context.view_layer.update()          # link first, THEN update, THEN measure
    probe = next(o for o in loaded if o is not None)
    assert not (len(probe.data.vertices) == 8 and
                max(abs(c) for v in probe.data.vertices
                    for c in (probe.matrix_world @ v.co)) <= 1.001), (
        "appended objects still read as unit cubes at the origin — they were measured "
        "before being linked into the view layer (ls_reorigin's depsgraph trap)")
    idx = {}
    for true_name, o in zip(wanted, loaded):
        if o is None:
            continue
        idx[true_name] = (rec_key(o), o)
    return idx, [o for o in loaded if o is not None]


def unstage(o):
    """Take an object out of the staging collection once it has a real home."""
    tmp = bpy.data.collections.get("WRD_STAGING")
    if tmp and o.name in tmp.objects:
        tmp.objects.unlink(o)


def cleanup(objs):
    for o in objs:
        if o is not None and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    tmp = bpy.data.collections.get("WRD_STAGING")
    if tmp is not None:
        if not tmp.objects:
            if tmp.name in [c.name for c in bpy.context.scene.collection.children]:
                bpy.context.scene.collection.children.unlink(tmp)
            bpy.data.collections.remove(tmp)
        else:
            print("  !! %d object(s) left in WRD_STAGING — refusing to drop it"
                  % len(tmp.objects))


if REVERT:
    do_revert(EDGES)
    if SAVE:
        bpy.ops.wm.save_as_mainfile(filepath=MASTER)
        print("SAVED", MASTER)
    sys.exit(0)

print("=" * 92)
print("WALK RE-DERIVE — master vs the blockout raised from the CURRENT map")
print("=" * 92)

MIDX = snapshot_master()                 # BEFORE the append — see snapshot_master()
print("master:   %d walk_/bar_ records" % len(MIDX))
BIDX, BOBJS = load_blockout_index()
print("blockout: %d walk_/bar_ records" % len(BIDX))
master = {n: v[1] for n, v in MIDX.items()}

stale, missing, extra = {}, {}, {}
for n, (k, bo) in BIDX.items():
    mo = master.get(n)
    if mo is None:
        missing.setdefault(group_of(n), []).append(n)
    elif MIDX[n][0] != k:
        # how far did it actually move?  a number, not a boolean
        mv = max((Vector(a) - Vector(b)).length
                 for a, b in zip(MIDX[n][0][1], k[1])) if MIDX[n][0][0] == k[0] else None
        stale.setdefault(group_of(n), []).append((n, mv, len(mo.data.vertices), k[0]))
for n in master:
    if n not in BIDX:
        extra.setdefault(group_of(n), []).append(n)

print("\nSTALE (master disagrees with the current map), by edge / landmark pad:")
tot = 0
for eid in sorted(stale, key=lambda e: -len(stale[e])):
    rows = stale[eid]
    tot += len(rows)
    mvs = [r[1] for r in rows if r[1] is not None]
    vc = [r for r in rows if r[2] != r[3]]
    print("  %-44s %3d record(s)%s%s" % (
        eid, len(rows),
        ("  moved %.3f..%.3f m" % (min(mvs), max(mvs))) if mvs else "",
        ("  %d with a VERTEX-COUNT change" % len(vc)) if vc else ""))
    for n, mv, a, b in rows[:6]:
        print("        %-56s %s" % (n, ("moved %.3f m" % mv) if mv is not None else
                                    "verts %d -> %d" % (a, b)))
print("  TOTAL STALE: %d record(s) across %d job(s)" % (tot, len(stale)))
print("\nMISSING from the master (in the blockout, not in the master): %d"
      % sum(len(v) for v in missing.values()))
for eid in sorted(missing):
    print("  %-44s %3d  %s" % (eid, len(missing[eid]), missing[eid][:3]))
print("EXTRA in the master (not in the blockout): %d"
      % sum(len(v) for v in extra.values()))
for eid in sorted(extra, key=lambda e: -len(extra[e]))[:8]:
    print("  %-44s %3d  %s" % (eid, len(extra[eid]), extra[eid][:3]))

if REPORT:
    cleanup(BOBJS)
    print("\n--report: nothing was changed.")
    sys.exit(0)

assert EDGES or LMS or DROPS, ("give --edge <a__b>[,...], --lm <id>[,...] and/or "
                              "--drop <a__b|lm:id>[,...], or --report")
for e in EDGES:
    assert e in EDGE_IDS, "map has no edge %s" % e
for l in LMS:
    assert l in LM_IDS, "map has no landmark %s" % l
    assert LM_IDS[l].get("class", "structure") in ("area", "structure", "prop", "portal"), (
        "%s is class %r — that class derives no walk record at all (town_blockout's "
        "landmark loops cover area -> walk_lm_, and structure/prop/portal -> walk_pad_)"
        % (l, LM_IDS[l].get("class", "structure")))
for d in DROPS:
    assert not (d.startswith("lm:") and d[3:] in LM_IDS), (
        "--drop lm:%s but the map STILL HAS that landmark — use --lm to re-derive it"
        % d[3:])
    assert d.startswith("lm:") or d not in EDGE_IDS, (
        "--drop %s but the map STILL HAS that edge — use --edge to re-derive it" % d)

# JOBS, in the order given: an edge id, or `lm:<id>` for a landmark pad.
JOBS = list(EDGES) + ["lm:" + l for l in LMS]

# ============================================================================= drop
DROPPED_ANY = [False]
if DROPS:
    print("\n" + "=" * 92)
    print("DROPPING (the map no longer carries these): %s" % ", ".join(DROPS))
    print("=" * 92)
    for job in DROPS:
        sel = dropped_records(job)
        have = sorted(n for n in master if sel(n))
        if not have:
            log("SKIP", job, "the master carries no records for it — already gone")
            continue
        DROPPED_ANY[0] = True
        for n in have:
            o = master[n]
            o["wrd_colls"] = [c.name for c in o.users_collection]
            o.name = SNAP + n
            o.use_fake_user = True
            for c in list(o.users_collection):
                c.objects.unlink(o)
            del master[n]
        log("DROPPED", job, "%d record(s) snapshotted %s*, revertible" % (len(have), SNAP))
        for n in have[:8]:
            print("        %s" % n)

# =========================================================================== rebuild
print("\n" + "=" * 92)
print("RE-DERIVING: %s" % (", ".join(JOBS) if JOBS else "(nothing — drops only)"))
print("=" * 92)

SKIP_PREFIX = ("lm_",)

# RECORDS A RE-DERIVE MUST NOT SILENTLY REBUILD, each with the reason and the pass that
# earned it.  These are places where the master DELIBERATELY no longer matches a full
# blockout, so "the blockout disagrees" is the CORRECT state and rebuilding them would
# undo a fix.  The tool refuses them unless `force` is passed, because the failure mode
# is invisible: the geometry looks right and the collision is wrong.
DOCUMENTED_EXCEPTIONS = {
    "bar_e_shelf-homes__market-stalls_l0_railB":
        "ls_reorigin.py cut a GAP in this rail (8 verts -> 4) because it ran across the "
        "loop-stairs fork's top tread — an INVISIBLE WALL across a staircase, found only "
        "by walking it with a body box. Re-deriving it from the blockout re-installs the "
        "wall. town_blockout draws a rail per edge knowing nothing about what else leaves.",
    "walk_pad_loop-landing":
        "deliberately NOT imported: the fork platform already exists as the market "
        "flight's own _landing mesh, and the pad swallowed that seam's whole slide "
        "window (seam_test RED, canon §5 failure). ls_reorigin measured this out.",
}
FORCE = "force" in argv
changed_any = False
for eid in JOBS:
    sel = records_of(eid)
    want = sorted(n for n in BIDX if sel(n) and not n.startswith(SKIP_PREFIX))
    have = sorted(n for n in master if sel(n) and not n.startswith(SKIP_PREFIX))
    guarded = [n for n in set(want) | set(have) if n in DOCUMENTED_EXCEPTIONS]
    if guarded and not FORCE:
        for n in guarded:
            log("GUARDED", n, DOCUMENTED_EXCEPTIONS[n][:64] + "...")
            print("             %s" % DOCUMENTED_EXCEPTIONS[n])
        want = [n for n in want if n not in DOCUMENTED_EXCEPTIONS]
        have = [n for n in have if n not in DOCUMENTED_EXCEPTIONS]
        log("", "", "-> %d guarded record(s) held back; pass `force` to override" % len(guarded))
    if not want:
        log("SKIP", eid, "the blockout carries no records for it")
        continue
    if set(want) == set(have) and all(MIDX[n][0] == BIDX[n][0] for n in want):
        log("CURRENT", eid, "%d record(s) already match the map — no-op" % len(want))
        continue
    changed_any = True

    # -- peer settings, read from the records being REPLACED (per class) -----------
    peers = {}
    for n in have:
        o = master[n]
        cls = "bar" if n.startswith("bar_") else "walk"
        if cls not in peers:
            peers[cls] = {
                "colls": [c.name for c in o.users_collection],
                "hide_render": o.hide_render,
                "hide_viewport": o.hide_viewport,
                "mats": [m.name if m else None for m in o.data.materials],
            }
    for cls, p in peers.items():
        log("PEERS", "%s (%s)" % (eid, cls),
            "colls=%s hide_render=%s mats=%s" % (p["colls"], p["hide_render"], p["mats"]))
    if not peers:
        # a brand-new edge: borrow from any sibling of the same class in the master
        for n2, o2 in master.items():
            cls = "bar" if n2.startswith("bar_") else "walk"
            peers.setdefault(cls, {
                "colls": [c.name for c in o2.users_collection],
                "hide_render": o2.hide_render,
                "hide_viewport": o2.hide_viewport,
                "mats": [m.name if m else None for m in o2.data.materials]})

    # -- snapshot + withdraw the old records --------------------------------------
    for n in have:
        o = master[n]
        o["wrd_colls"] = [c.name for c in o.users_collection]
        o.name = SNAP + n
        o.use_fake_user = True
        for c in list(o.users_collection):
            c.objects.unlink(o)
    log("WITHDREW", eid, "%d record(s) snapshotted %s*, revertible" % (len(have), SNAP))

    # -- install the freshly-derived ones -----------------------------------------
    # THE NAME COLLISION, CLOSED.  The blockout's records were appended while the
    # master's still held their names, so Blender suffixed every one `.001`.  Now that
    # the originals are snapshotted to WRD_SRC_*, the true names are free and the
    # incoming records MUST take them: every other tool in the pipeline matches walk
    # records by exact name (cine_solve `owns`, routes_derive, master_walk_qa,
    # seam_test), so shipping `walk_e_..._l0.001` would silently orphan the edge.
    n_in = 0
    for n in want:
        bo = BIDX[n][1]
        if bo.name != n:
            clash = bpy.data.objects.get(n)
            assert clash is None, (
                "cannot rename %s -> %s: the name is still taken by %s"
                % (bo.name, n, clash.name))
            bo.name = n
        cls = "bar" if n.startswith("bar_") else "walk"
        p = peers.get(cls) or list(peers.values())[0]
        for cn in p["colls"]:
            c = bpy.data.collections.get(cn) or bpy.context.scene.collection
            if bo.name not in c.objects:
                c.objects.link(bo)
        bo.hide_render = p["hide_render"]
        bo.hide_viewport = p["hide_viewport"]
        if p["mats"]:
            bo.data.materials.clear()
            for mn in p["mats"]:
                bo.data.materials.append(bpy.data.materials.get(mn) if mn else None)
        unstage(bo)                                    # it has a real collection now
        BOBJS = [x for x in BOBJS if x is not bo]      # keep it: do not clean it up
        n_in += 1
    log("INSTALLED", eid, "%d record(s) from the blockout" % n_in)

cleanup(BOBJS)
bpy.context.view_layer.update()

# ===================================== the invisible-wall sweep (bar_ across a way on)
print("\n" + "=" * 92)
print("INVISIBLE-WALL SWEEP — does any rebuilt `bar_` cross another edge's walk ribbon?")
print("(a bar_ is NOT non-solid: play3d's noStand list is water_/lm_/veg_ only)")
print("=" * 92)
bpy.context.view_layer.update()


def tris_of(o):
    me = o.data
    mw = o.matrix_world
    out = []
    for p in me.polygons:
        vs = [mw @ me.vertices[i].co for i in p.vertices]
        for i in range(1, len(vs) - 1):
            out.append((vs[0], vs[i], vs[i + 1]))
    return out


def aabb(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(v.x for v in bb), max(v.x for v in bb),
            min(v.y for v in bb), max(v.y for v in bb),
            min(v.z for v in bb), max(v.z for v in bb))


rebuilt_bars = [bpy.data.objects[n] for eid in EDGES for n in BIDX
                if edge_of(n) == eid and n.startswith("bar_") and n in bpy.data.objects]
walk_others = [o for o in bpy.data.objects
               if o.name.startswith("walk_") and not o.name.startswith(SNAP)
               and edge_of(o.name) not in EDGES]
print("sweeping %d rebuilt bar_ record(s) against %d other walk record(s)"
      % (len(rebuilt_bars), len(walk_others)))
if not rebuilt_bars:
    # Say it, rather than letting an empty sweep print CLEAN and read as a proof.
    print("  (this run rebuilt no rails at all — a landmark pad job carries none, so the")
    print("   CLEAN below is 'nothing to sweep', not 'swept and clear')")
BODY_R, BODY_H = 0.30, 1.70
hits = []
for b in rebuilt_bars:
    bx0, bx1, by0, by1, bz0, bz1 = aabb(b)
    for w in walk_others:
        wx0, wx1, wy0, wy1, wz0, wz1 = aabb(w)
        if bx1 + BODY_R < wx0 or bx0 - BODY_R > wx1: continue
        if by1 + BODY_R < wy0 or by0 - BODY_R > wy1: continue
        if bz0 > wz1 + BODY_H or bz1 < wz0 - 0.20: continue
        # plan-overlap of the two footprints, area-weighted
        ox = max(0.0, min(bx1, wx1) - max(bx0, wx0))
        oy = max(0.0, min(by1, wy1) - max(by0, wy0))
        if ox * oy < 0.01: continue
        hits.append((b.name, w.name, ox, oy, ox * oy, bz0, wz1))
if hits:
    print("\n  %d POSSIBLE CROSSING(S) — each needs an eye, none is auto-cut:" % len(hits))
    for bn, wn, ox, oy, a, bz0, wz1 in sorted(hits, key=lambda h: -h[4])[:20]:
        print("    %-46s x %-44s overlap %.2f x %.2f m (%.2f m2), rail base z=%.2f vs walk top z=%.2f"
              % (bn, wn, ox, oy, a, bz0, wz1))
    print("\n  A crossing here is the loop-stairs fork's defect: `town_blockout` draws a")
    print("  rail per edge knowing nothing about what else leaves. Cut a GAP inside the")
    print("  crossing edge's own body column (not a deletion) if the rail fences off a")
    print("  way on; leave it if the two merely share a corner.")
else:
    print("\n  CLEAN — no rebuilt rail overlaps another edge's walk ribbon in plan.")

if SAVE and (changed_any or DROPPED_ANY[0]):
    bpy.ops.wm.save_as_mainfile(filepath=MASTER)
    print("\nSAVED %s" % MASTER)
elif SAVE:
    print("\nnothing changed — not saved")
else:
    print("\n(dry run — pass `save` to write the master)")
