"""emb_carriers.py — WHICH CARRIERS OWN STATE IN THIS BLEND, AND WHICH ONES A RE-DRESS
DROPPED.  The gate for a defect class this town has already shipped twice.

    Blender -b tools/blends/<blend> --python-exit-code 1 -P tools/emb_carriers.py --
    Blender -b tools/blends/<blend> --python-exit-code 1 -P tools/emb_carriers.py -- --record
    Blender -b tools/blends/<blend> --python-exit-code 1 -P tools/emb_carriers.py -- --print
    ... -- --as emberbrook-dressed      (check a scratch build against another's ledger)

Default mode CHECKS the blend against its own ledger (`tools/blends/districts/
emb_carriers.<stem>.json`) and EXITS 1 naming every carrier whose footprint has gone or
shrunk, with the command that puts it back.  `--record` writes that ledger from the blend
in front of it (do this on a blend you have just brought up to date, never on one you are
about to fix).  `--print` censuses and exits 0.  Everything outside `__main__` is
import-safe: `emb_dress.py` imports `census()` and `check()` and prints the same report at
the end of every build, so the receipt reaches the person who caused the loss.

=============================== WHY THIS EXISTS =================================

MEASURED 2026-08-12, round 4.  `emb_dress.py` builds `emberbrook-dressed.blend` FROM
`emberbrook-master.blend`, so every fix a CARRIER put on the dressed blend is thrown away
by the next re-dress — silently, with no log line and no gate.  The demonstration was a
full `emb_dress --region all --tier plate --key emberwake --noshoot` into a scratch
`--out`, censused against the shipped blend:

    emb_dress_mill_lucamx*  (emb_millucam)      36 members  ->   0
    lamp glass visible_shadow False (emb_lightbodies)   14  ->   0
    walk pads nudged 4 mm   (emb_padcoplanar)   34 objects  ->   0 (all restored coplanar)
    water_emb_* vert counts (emb_brookchop + emb_water_shader)  welded -> the raft again
                                                        (pond 1556 -> 5664 verts)

Four carriers, three of them fixes with published receipts (half the crushed frame at
homerow; the black hole on the path at `walk_pad_grandmothers-bench`; at-water luminance
p50 0.056 -> 0.108).  Round 3 named ONE of the four and called it a lucam problem.  It is
not a lucam problem: **A GENERATOR THAT REBUILDS ITS OUTPUT FROM AN UPSTREAM SOURCE OWNS
NOTHING A CARRIER PUT ON THAT OUTPUT, AND NOTHING IN THE TREE SAID SO.**

WHAT THIS IS NOT.  It is not a fix and it does not re-run anything — a carrier's own file
is the only thing that knows how to re-apply it, and three of them are order-dependent.
It is the RECEIPT that the re-run is owed.

HOW A CARRIER IS DETECTED.  Every Emberbrook carrier stamps a JSON snapshot: four on the
SCENE (`embmg`, `embml`, `emblb`, `embpad`) and five on the OBJECTS or MATERIALS they
touched (`embpc`, `embpf`, `embpl`, `embbc`, `embws`).  That stamp is the instrument, and
it is sound in the direction that matters — a re-dress rebuilds the scene and the objects
from the master, so the stamp goes with the work.  It is NOT sound in the other direction:
a stamp says the carrier ran, never that its members are still standing.  So the ledger
also records the EFFECT counts that can be measured directly (lucam members, gable boards,
unsealed lamp glass), and a shortfall in EITHER is red.  Only a shortfall: `embpc/embpf/
embpl` are stamped on the MASTER and are inherited by every build from it, and the gable
grows 88 -> 90 when the generator emits it instead of the carrier, so a rise is not a
regression and is not reported as one.
"""
import bpy, sys, json, os

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
LEDGER_DIR = os.path.join(REPO, "tools/blends/districts")

# name -> (where the stamp lives, the command that re-applies it, ordering note)
CARRIERS = {
    "embws":  ("obj+mat", "-P tools/emb_water_shader.py -- save",
               "3rd: AFTER emb_brookchop (it subdivides and bakes the depth->alpha layer)"),
    "embbc":  ("obj",     "-P tools/emb_brookchop.py -- save",
               "2nd: between emb_water_shader's `revert save` and its `save`"),
    "emblb":  ("scene",   "-P tools/emb_lightbodies.py -- save", ""),
    "embpad": ("scene",   "-P tools/emb_padcoplanar.py -- save",
               "the plate master only — it changes the picture, never the walk network"),
    "embmg":  ("scene",   "-P tools/emb_millgable.py -- save",
               "HISTORICAL: emb_dress emits the boards itself since 2026-08-10 and this "
               "carrier now finds no plain gable box to work on"),
    "embml":  ("scene",   "-P tools/emb_millucam.py -- save",
               "emb_dress calls board_lucams() since 2026-08-12, so a fresh dress is "
               "already stamped `by: emb_dress`"),
    "embpc":  ("obj",     "-P tools/emb_pavechop.py -- save", ""),
    "embpf":  ("obj",     "-P tools/emb_padfill.py -- save", ""),
    "embpl":  ("obj",     "-P tools/emb_padlevel.py -- save", ""),
}


# A CARRIER THE GENERATOR HAS TAKEN OVER IS CHECKED BY ITS EFFECT, NOT BY ITS STAMP —
# otherwise every legitimate fresh dress prints a red line for `embmg` (whose boards
# `emb_dress` now emits under its own names and without the snapshot), and a report that
# cries wolf on every run is a report nobody reads.  The MEMBERS are what the town is
# made of, so the members are what is gated.
SUPERSEDED = {"embmg": "gable_members", "embml": "lucam_members"}


def ledger_path(stem):
    return os.path.join(LEDGER_DIR, "emb_carriers.%s.json" % stem)


def census(stem=None):
    """Count every carrier stamp and every measurable carrier EFFECT in this scene."""
    sc = bpy.context.scene
    n = {k: 0 for k in CARRIERS}
    for k in sc.keys():
        if k in n:
            n[k] += 1
    for o in bpy.data.objects:
        for k in o.keys():
            if k in n:
                n[k] += 1
    for m in bpy.data.materials:
        for k in m.keys():
            if k in n:
                n[k] += 1
    eff = {
        "lucam_members": sum(1 for o in bpy.data.objects
                             if o.name.startswith("emb_dress_mill_lucamx")),
        "gable_members": sum(1 for o in bpy.data.objects
                             if o.name.startswith("emb_dress_mill_gableboard")
                             or o.name.startswith("emb_dress_mill_gablebarge")),
        "lamp_glass_unsealed": sum(1 for o in bpy.data.objects
                                   if o.name.startswith("emb_lamp_")
                                   and o.name.endswith("_glass")
                                   and o.visible_shadow is False),
    }
    by = None
    if sc.get("embml"):
        try:
            by = json.loads(sc["embml"]).get("by")
        except Exception:
            by = "?"
    if stem is None:
        stem = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    return {"blend": stem, "carriers": {k: v for k, v in n.items() if v},
            "effects": eff, "embml_by": by}


def check(cur, stem):
    """Return the list of (what, was, now, cmd, note) that SHRANK against the ledger.
       A missing ledger is a FAILURE, never a pass: an instrument that finds nothing must
       prove it could have found something."""
    p = ledger_path(stem)
    if not os.path.exists(p):
        return None
    old = json.load(open(p))
    bad = []
    for k, v in sorted(old.get("carriers", {}).items()):
        if k in SUPERSEDED:
            continue
        now = cur["carriers"].get(k, 0)
        if now < v:
            bad.append(("carrier %s" % k, v, now, CARRIERS[k][1], CARRIERS[k][2]))
    for k, v in sorted(old.get("effects", {}).items()):
        now = cur["effects"].get(k, 0)
        if now < v:
            bad.append(("effect %s" % k, v, now, "", ""))
    return bad


def report(cur, bad, stem):
    print("=" * 78)
    print("EMBERBROOK CARRIER CENSUS — %s" % stem)
    print("=" * 78)
    for k, v in sorted(cur["carriers"].items()):
        print("  %-8s %4d holder(s)   %s" % (k, v, CARRIERS[k][0]))
    for k, v in sorted(cur["effects"].items()):
        print("  %-24s %4d" % (k, v))
    print("  embml stamped by: %s" % cur["embml_by"])
    if bad is None:
        print("NO LEDGER at %s — run once with `-- --record` on a blend that is up to "
              "date." % ledger_path(stem))
        return
    if not bad:
        print("OK — every carrier in the ledger is still standing.")
        return
    print("-" * 78)
    print("RED — %d carrier footprint(s) SHRANK against the ledger. A re-dress rebuilds "
          "this blend from the master and owns NOTHING a carrier put on it." % len(bad))
    for what, was, now, cmd, note in bad:
        print("  %-22s %d -> %d" % (what, was, now))
        if cmd:
            print("      Blender -b tools/blends/%s.blend --python-exit-code 1 %s"
                  % (stem, cmd))
        if note:
            print("      %s" % note)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    stem = (argv[argv.index("--as") + 1] if "--as" in argv
            else os.path.splitext(os.path.basename(bpy.data.filepath))[0])
    cur = census(stem)
    if "--record" in argv:
        os.makedirs(LEDGER_DIR, exist_ok=True)
        json.dump(cur, open(ledger_path(stem), "w"), indent=1, sort_keys=True)
        report(cur, [], stem)
        print("RECORDED %s" % ledger_path(stem))
        sys.exit(0)
    if "--print" in argv:
        report(cur, [], stem)
        sys.exit(0)
    bad = check(cur, stem)
    report(cur, bad, stem)
    sys.exit(1 if (bad is None or bad) else 0)
