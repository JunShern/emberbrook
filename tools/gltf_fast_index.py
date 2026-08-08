# gltf_fast_index.py — MAKE BLENDER'S glTF EXPORTER LINEAR AGAIN.
#
#   import gltf_fast_index; gltf_fast_index.apply()      # before bpy.ops.export_scene.gltf
#   EMB_GLTF_FAST_INDEX=0 <blender ...>                  # kill switch: run the vendor code
#   /Applications/Blender.app/Contents/MacOS/Blender -b --python-exit-code 1 \
#       -P tools/gltf_fast_index.py -- --selftest        # the semantics proof, 1 s
#
# =============================== THE DEFECT ===================================
# THE QUADRATIC IS IN VENDOR CODE AND THIS FILE DOES NOT HIDE THAT. It is
#
#   Blender.app/Contents/Resources/5.1/scripts/addons_core/io_scene_gltf2/
#       blender/exp/exporter.py:413   GlTF2Exporter.__append_unique_and_get_index
#
#       @staticmethod
#       def __append_unique_and_get_index(target: list, obj):
#           if obj in target:            # O(len(target))
#               return target.index(obj) # O(len(target)) AGAIN
#           index = len(target); target.append(obj); return index
#
# `__to_reference()` calls it once for EVERY child-of-root property the exporter
# produces — every node, mesh, accessor, bufferView, material, texture, image,
# sampler, skin, scene, animation, camera, buffer — against the list that is
# still being built. So the cost of writing the Nth accessor is O(N), and the
# cost of the export is O(N^2). None of those classes (io/com/gltf2_io.py) defines
# `__eq__`, so every one of those comparisons is `object_richcompare`, identity.
#
# MEASURED HERE (2026-08-07/08, `sample <pid>` on the running Blender, macOS's own
# stack sampler): with the cyclic GC already frozen by cine_bake.py, 4355 of 4431
# main-thread samples of the stalled Emberbrook export were
# `list_contains -> PyObject_RichCompareBool -> object_richcompare`. Four runs of
# `cine_bake.py --town emberbrook --glb` against the DRESSED master crossed the
# 26-33 minute band and none of them finished. The scene is why: emberbrook-dressed
# carries 1993 collection-instance empties (searsia x444, grass_bermuda x92 of 21
# objects each, ...) which the exporter expands into ~17.9k nodes and a matching
# tail of meshes/accessors/bufferViews, against Emberbrook-gray's 2304 nodes.
# 8x the objects is 64x this function.
#
# ================================ THE FIX =====================================
# A SET, NOT A LIST — but the list also defines the OUTPUT ORDER (a glTF reference
# IS an index into it), so the list stays and an index side-table is added purely
# for membership. Exactness is the whole job:
#
#   * FAST PATH ONLY FOR IDENTITY-COMPARABLE OBJECTS. `type(obj).__eq__ is
#     object.__eq__` means `==` on this object can never be anything but `is`, so
#     an id()-keyed dict is not an approximation of `in`, it is the same predicate.
#     Everything else — notably the STRINGS appended to extensions_used /
#     extensions_required, which dedup BY VALUE — falls through to the vendor's own
#     two lines, unchanged. Those lists have single-digit lengths.
#   * A HIT IS CONFIRMED AGAINST THE LIST (`target[i] is obj`) before it is
#     returned, and the table is rebuilt whenever `len(target)` moved without us.
#     So any mutation by code that does not come through here (the
#     EXT_mesh_gpu_instancing pass rebuilds gltf.nodes) can make the table stale
#     but cannot make it wrong.
#   * The table is keyed by `id(target)` and holds a reference to the list, so a
#     recycled id is caught by `ent[0] is not target`.
#
# WHY IT LIVES HERE AND NOT IN THE ADDON: patching the Blender installation is
# invisible to git, is lost on every Blender update, and changes the behaviour of
# every other tool on this machine. This module patches the in-memory class from
# OUR process, is version-controlled, prints what it did on every run, and is
# switched off by one environment variable. It is a WORKAROUND WITH AN OWNER, not
# a fork. THE REAL FIX IS UPSTREAM (glTF-Blender-IO); this note is the bug report.

import os
import sys

_APPLIED = {}


def _identity_only(obj):
    """True when `==` on this object provably cannot be anything but `is`."""
    return type(obj).__eq__ is object.__eq__


def apply(verbose=True):
    """Patch GlTF2Exporter.__append_unique_and_get_index. Idempotent. Returns bool."""
    if os.environ.get("EMB_GLTF_FAST_INDEX", "1") == "0":
        if verbose:
            print("GLTFIDX off (EMB_GLTF_FAST_INDEX=0) — vendor O(n^2) "
                  "__append_unique_and_get_index in use")
        return False
    if _APPLIED.get("done"):
        return True
    try:
        from io_scene_gltf2.blender.exp import exporter as _exp
    except Exception as e:                       # pragma: no cover - addon absent
        print("GLTFIDX NOT APPLIED — io_scene_gltf2 not importable (%s)" % e)
        return False

    cls = _exp.GlTF2Exporter
    name = "_GlTF2Exporter__append_unique_and_get_index"
    original = getattr(cls, name, None)
    if original is None:                         # pragma: no cover - upstream renamed it
        print("GLTFIDX NOT APPLIED — %s.%s is gone; the addon changed, re-read "
              "blender/exp/exporter.py before trusting this module" % (cls.__name__, name))
        return False

    tables = {}                                  # id(list) -> [list, {key: index}, len_seen]
    stats = {"calls": 0, "fast": 0, "slow": 0, "rebuilds": 0, "scans_avoided": 0}

    def append_unique_and_get_index(target, obj):
        stats["calls"] += 1
        if not _identity_only(obj):
            # value semantics (strings in extensions_used/required): vendor code verbatim
            stats["slow"] += 1
            if obj in target:
                return target.index(obj)
            index = len(target)
            target.append(obj)
            return index
        stats["fast"] += 1
        stats["scans_avoided"] += len(target)
        ent = tables.get(id(target))
        if ent is None or ent[0] is not target or ent[2] != len(target):
            ent = [target, {}, 0]
            for i, o in enumerate(target):
                if _identity_only(o):
                    ent[1].setdefault(id(o), i)
            ent[2] = len(target)
            tables[id(target)] = ent
            stats["rebuilds"] += 1
        d = ent[1]
        i = d.get(id(obj))
        if i is not None and i < len(target) and target[i] is obj:
            return i
        if i is not None:                        # stale entry: the list moved under us
            ent[1] = d = {}
            for j, o in enumerate(target):
                if _identity_only(o):
                    d.setdefault(id(o), j)
            stats["rebuilds"] += 1
            i = d.get(id(obj))
            if i is not None:
                return i
        index = len(target)
        target.append(obj)
        d[id(obj)] = index
        ent[2] = index + 1
        return index

    setattr(cls, name, staticmethod(append_unique_and_get_index))
    _APPLIED["done"] = True
    _APPLIED["stats"] = stats
    if verbose:
        print("GLTFIDX on  — io_scene_gltf2 blender/exp/exporter.py:413 "
              "__append_unique_and_get_index given an O(1) index side-table "
              "(identity-comparable objects only; value semantics fall through)")
    return True


def report():
    """Print what the patch did. Safe to call when it was never applied."""
    s = _APPLIED.get("stats")
    if not s:
        return
    print("GLTFIDX calls=%d fast=%d value-semantics=%d table-rebuilds=%d "
          "list-comparisons-avoided=%d"
          % (s["calls"], s["fast"], s["slow"], s["rebuilds"], s["scans_avoided"]))


# ------------------------------------------------------------------ selftest --
# THE PATCH IS ONLY WORTH ANYTHING IF IT IS THE SAME FUNCTION. This runs the vendor
# implementation and the replacement side by side over the same call sequence and
# demands the same return value AND the same resulting list, every step.
def selftest():
    from io_scene_gltf2.blender.exp import exporter as _exp
    cls = _exp.GlTF2Exporter
    name = "_GlTF2Exporter__append_unique_and_get_index"
    ref = getattr(cls, name)                     # vendor version (call before apply())

    class Plain:                                 # no __eq__: exactly gltf2_io's shape
        def __init__(self, n): self.n = n

    class ValueEq:                               # __eq__ by value, like a str
        def __init__(self, n): self.n = n
        def __eq__(self, o): return isinstance(o, ValueEq) and o.n == self.n
        def __hash__(self): return hash(self.n)

    class Unhashable:
        __hash__ = None
        def __init__(self, n): self.n = n
        def __eq__(self, o): return isinstance(o, Unhashable) and o.n == self.n

    apply(verbose=False)
    fast = getattr(cls, name)

    cases = []
    a, b, c = Plain(1), Plain(2), Plain(3)
    cases.append(("identity objects, appends and re-hits", [a, b, a, c, b, a, c]))
    cases.append(("strings dedup BY VALUE", ["KHR_a", "KHR_b", "KHR_" + "a", "KHR_b"]))
    cases.append(("value-eq objects", [ValueEq(1), ValueEq(2), ValueEq(1)]))
    cases.append(("unhashable value-eq objects", [Unhashable(1), Unhashable(2), Unhashable(1)]))
    cases.append(("mixed identity + value in one list",
                  [Plain(9), "s", Plain(9), "s", ValueEq(4), "s"]))

    fails = 0
    for label, seq in cases:
        la, lb = [], []
        for obj in seq:
            ra, rb = ref(la, obj), fast(lb, obj)
            if ra != rb or len(la) != len(lb) or any(x is not y for x, y in zip(la, lb)):
                print("SELFTEST FAIL  %-38s obj=%r vendor=%r fast=%r" % (label, obj, ra, rb))
                fails += 1
                break
        else:
            print("SELFTEST ok    %-38s %d calls, final list len %d" % (label, len(seq), len(la)))

    # the list moving under the table (what the gpu-instancing pass does)
    la, lb = [], []
    objs = [Plain(i) for i in range(6)]
    for o in objs:
        ref(la, o); fast(lb, o)
    del la[2]; del lb[2]                          # an external mutation, same on both
    ok = True
    for o in objs:
        if ref(la, o) != fast(lb, o):
            ok = False
    if ok and len(la) == len(lb) and all(x is y for x, y in zip(la, lb)):
        print("SELFTEST ok    %-38s list mutated externally, table rebuilt" % "stale-table recovery")
    else:
        print("SELFTEST FAIL  stale-table recovery")
        fails += 1

    print("SELFTEST %s" % ("ALL PASS" if fails == 0 else "%d FAILURE(S)" % fails))
    return fails


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(1 if selftest() else 0)
    print(__doc__ or "gltf_fast_index: import and call apply()")
