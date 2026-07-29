"""veg_prefix_migrate.py — the town-wide `veg_` no-stand rename (cross-cutting).

  Blender -b tools/blends/dellhollow-master.blend -P tools/veg_prefix_migrate.py -- [save]

Commit `5e2d7fc` made `veg_` the runtime NO-STAND prefix (`play3d.html`:
`water_` / `lm_` / `veg_`), because tree canopies were climbable terrain.
Locksfoot was built after that ruling and named its own foliage `veg_lf_*`;
the Boatyard, the Boatyard seam and the Waterfront were all built BEFORE it,
so ~350 bushes, ferns, creepers, grass tufts and rim crowns are still solid
ground the player can walk up.  This migrates them.

RENAME ONLY.  No vertex is touched, no object is moved, nothing is added or
removed — so `master_walk_qa` and `geometry_audit` must return exactly the same
numbers afterwards (`geometry_audit`'s VEG list already carries a bare `veg_`,
and its GROUND test is a substring match, so `veg_farcrown_0` still reads as
context).

NOT renamed, deliberately:
  * `v10_src_*` — the harvested DONOR prototypes the Boatyard and Waterfront
    clone from.  `town_export.py` strips `^(fx_|FOG|.*haze|ridge_upstream|
    far_town|v10_)` from the runtime GLB, so they are already invisible to the
    player; giving them a `veg_` name would take them OUT of that net and ship
    two stray bushes standing at the harvest origin.
  * the gate branch's `gate_*` foliage — it lives in
    `dellhollow-master-gate-branch.blend`, which another agent holds.  The merge
    custodian applies the same rename there, after the merge.

The generators are updated in the same commit (`boatyard_build.py`,
`waterfront_build.py`, `master_weld.py`, `waterfront_light.py`) so a rebuild
from the backup reproduces the `veg_` names rather than re-creating the old
ones beside them.
"""
import bpy, sys
from collections import Counter

SAVE = "save" in sys.argv

# longest-first: `wf_creeper_` must not be matched by the bare `creeper_` rule
RULES = [
    # ---- Waterfront (DIST_waterfront_VEG) --------------------------------
    "wf_creeper_", "wf_fern_", "wf_rimclump_", "wf_tuft_",
    # ---- the Boatyard seam (SEAM_WELD) -----------------------------------
    "seam_tuft_",
    # ---- Boatyard (DIST_boatyard) ----------------------------------------
    "creeper_", "farwallcrown_", "farcrown_", "rimclump_", "rimtree_", "tuft_",
]
RULES.sort(key=len, reverse=True)

KEEP = ("v10_",)          # donors: already stripped from the runtime export


def bucket(n):
    if n.startswith("veg_"):
        return None                       # already migrated — idempotent
    if n.startswith(KEEP):
        return None
    for r in RULES:
        if n.startswith(r):
            return r
    return None


print("=" * 78)
print("VEG PREFIX MIGRATION   (runtime no-stand convention, commit 5e2d7fc)")
print("=" * 78)


def inventory(title):
    c = Counter()
    for o in bpy.data.objects:
        n = o.name
        if n.startswith("veg_"):
            c["veg_ (migrated)"] += 1
        elif bucket(n):
            c[bucket(n) + "(standable)"] += 1
        elif n.startswith(KEEP) and ("tuft" in n or "creeper" in n or "clump" in n):
            c["v10_src_ donor (exempt)"] += 1
    print("\n%s" % title)
    for k in sorted(c):
        print("    %-32s %4d" % (k, c[k]))
    print("    %-32s %4d" % ("TOTAL", sum(c.values())))
    return c


before = inventory("BEFORE")

todo = [o for o in bpy.data.objects if bucket(o.name)]
clash = [o for o in todo if bpy.data.objects.get("veg_" + o.name) is not None]
assert not clash, "target names already taken: %s" % [o.name for o in clash][:5]

per_rule = Counter()
for o in todo:
    per_rule[bucket(o.name)] += 1
    old = o.name
    o.name = "veg_" + old
    # the object name is what the runtime and both audits key off; the mesh
    # datablock is renamed alongside it only when it is this object's alone, so
    # the two never drift apart in a handover (finding 117, other way round)
    if o.data is not None and o.data.users == 1 and o.data.name == old:
        o.data.name = o.name

print("\nRENAMED")
for r in sorted(per_rule, key=lambda r: -per_rule[r]):
    print("    %-20s -> veg_%-20s %4d" % (r + "*", r + "*", per_rule[r]))
print("    %-46s %4d" % ("TOTAL RENAMED", sum(per_rule.values())))

after = inventory("AFTER")
assert after.get("veg_ (migrated)", 0) == before.get("veg_ (migrated)", 0) + sum(per_rule.values())
assert not [k for k in after if k.endswith("(standable)")], \
    "foliage still standable: %s" % [k for k in after if k.endswith("(standable)")]

# nothing but names may have changed
print("\nobjects in file: %d   meshes: %d" % (
    len(bpy.data.objects), sum(1 for o in bpy.data.objects if o.type == 'MESH')))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
