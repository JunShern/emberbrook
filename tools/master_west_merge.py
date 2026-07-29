"""master_west_merge.py — replay the WEST BRANCH into the live master.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_west_merge.py -- <step> [save]

Steps (run in order; each is idempotent and asserts its own preconditions):

  delete   replay the deletion manifests: exactly the object names listed in
           gate_branch_deletions.json (7) + shelf_branch_deletions.json (10),
           verified against the recorded vertex count and bbox before removal.
           Nothing else is touched.
  append   append GATE_DISTRICT and SHELF_DISTRICT from the branch blend.  The
           branch is opened READ-ONLY by libraries/append and is never written.
           A full datablock census is printed before and after: an append leak
           (finding 180) is invisible in every render, so the count is the proof.
  dedup    reconcile the append's duplicates.  Every `<base>.NNN` material or
           image created by the append is compared to the local `<base>` by node
           signature (the same signature master_mat_dedup.py uses) and, if
           interchangeable, user_remap'ped onto it and removed.  Divergent ones
           are REPORTED, not eaten.
  hide     apply manifest-51 render-hiding to the gate/shelf tiers' walk_/bar_
           ribbons — hide_render only, hide_viewport NEVER (finding 51: viewport
           hiding drops the object from the GLB and the runtime loses collision).
           The footprint is the MAP's parcel bounds for p-gate / p-shelf-w /
           p-shelf-e, not the branch shot scripts' render filters: those are
           deliberately loose (shelf_shots covers x 0..60 z>13) and would also
           hide the QUAY-MARKET tier, whose ribbons are still its only visible
           paths because that tier is unbuilt gray.

`save` writes the master.  Without it nothing is written (dry run).
"""
import bpy, sys, os, re, json
from collections import defaultdict
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
# `ob.bound_box` / `ob.matrix_world` are stale in a headless session (no depsgraph
# evaluation), so every extent here comes from live vertices — the same helper the
# deletion manifests were RECORDED with, or the bboxes would not compare.
from boatyard_lib import world_bbox

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
BRANCH = REPO + "/tools/blends/dellhollow-master-gate-branch.blend"
MAP = REPO + "/public/townmap/dellhollow.map.json"
DEL_MANIFESTS = [REPO + "/tools/blends/districts/gate_branch_deletions.json",
                 REPO + "/tools/blends/districts/shelf_branch_deletions.json"]
COLLS = ["GATE_DISTRICT", "SHELF_DISTRICT"]
HIDE_PARCELS = ["p-gate", "p-shelf-w", "p-shelf-e"]

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = argv[0] if argv else "census"
SAVE = "save" in argv

assert bpy.data.filepath.endswith("dellhollow-master.blend"), \
    "this script edits the LIVE MASTER only, got %s" % bpy.data.filepath


def realfile(img):
    """The file an image actually resolves to.  `bpy.path.abspath` expands `//` but
    does NOT collapse `..`, so `//../textures/x.jpg` and `/tools/textures/x.jpg` —
    the branch's and the master's spellings of one JPEG — compare unequal without
    realpath, and every material sampling them then looks divergent."""
    return os.path.realpath(bpy.path.abspath(img.filepath))


def census(tag):
    n = {"objects": len(bpy.data.objects), "materials": len(bpy.data.materials),
         "meshes": len(bpy.data.meshes), "images": len(bpy.data.images),
         "lights": len(bpy.data.lights), "collections": len(bpy.data.collections),
         "node_groups": len(bpy.data.node_groups)}
    n["total_ids"] = sum(len(getattr(bpy.data, a)) for a in dir(bpy.data)
                         if not a.startswith("_") and hasattr(getattr(bpy.data, a), "__len__"))
    print("  CENSUS %-8s " % tag + "  ".join("%s=%d" % (k, v) for k, v in sorted(n.items())))
    return n


def sig(m):
    """Node-tree signature (master_mat_dedup.py): same signature == interchangeable."""
    if not m.node_tree:
        return ("nonodes", tuple(round(c, 6) for c in m.diffuse_color))
    out = []
    for n in sorted(m.node_tree.nodes, key=lambda n: (n.bl_idname, n.name)):
        row = [n.bl_idname]
        if n.bl_idname == "ShaderNodeTexImage":
            # the image is identified by the FILE it resolves to, not by how the
            # path happens to be stored: the master keeps some absolute, the branch
            # keeps the same texture as `//../textures/...`.  Comparing raw strings
            # makes every material that touches such an image look divergent.
            row += [re.sub(r"\.\d{3}$", "", n.image.name) if n.image else None,
                    realfile(n.image) if n.image else None]
        elif n.bl_idname == "ShaderNodeVertexColor":
            row.append(n.layer_name)
        elif n.bl_idname == "ShaderNodeAttribute":
            row.append(n.attribute_name)
        elif n.bl_idname == "ShaderNodeBsdfPrincipled":
            for k in ("Base Color", "Roughness", "Metallic",
                      "Emission Color", "Emission Strength", "Alpha", "IOR"):
                if k not in n.inputs:
                    continue
                v = n.inputs[k].default_value
                row.append((k, tuple(round(x, 5) for x in v)
                            if hasattr(v, "__len__") else round(v, 5)))
        elif n.bl_idname in ("ShaderNodeMix", "ShaderNodeMixRGB"):
            row += [getattr(n, "data_type", ""), getattr(n, "blend_type", "")]
        elif n.bl_idname == "ShaderNodeMapping":
            row.append(n.vector_type)
        elif n.bl_idname == "ShaderNodeTexCoord":
            row.append(bool(n.from_instancer))
        elif n.bl_idname in ("ShaderNodeTexNoise", "ShaderNodeTexVoronoi",
                             "ShaderNodeTexGradient", "ShaderNodeTexWave"):
            row += [tuple(round(i.default_value, 5) for i in n.inputs
                          if not hasattr(i.default_value, "__len__"))]
        out.append(tuple(row))
    return tuple(out)


print("=" * 78)
print("MASTER WEST MERGE  —  step '%s'%s" % (STEP, "  (SAVE)" if SAVE else "  (dry run)"))
print("=" * 78)

# --------------------------------------------------------------------- delete
if STEP in ("delete", "all"):
    census("before")
    want = []
    for path in DEL_MANIFESTS:
        man = json.load(open(path))
        print("\n  manifest %s  (%s / %s): %d names"
              % (os.path.basename(path), man["district"], man["parcel"], len(man["deleted"])))
        for rec in man["deleted"]:
            want.append((rec, os.path.basename(path)))
    assert len(want) == 17, "expected 7 gate + 10 shelf deletions, manifests list %d" % len(want)

    already, todo = [], []
    for rec, src in want:
        ob = bpy.data.objects.get(rec["name"])
        if ob is None:
            already.append(rec["name"])
            continue
        # verify we are deleting the object the manifest recorded, not a namesake
        assert len(ob.data.vertices) == rec["verts"], \
            "%s has %d verts, manifest recorded %d" % (rec["name"], len(ob.data.vertices), rec["verts"])
        b = world_bbox(ob)
        lo = [b[0], b[2], b[4]]
        hi = [b[1], b[3], b[5]]
        for i, ax in enumerate("xyz"):
            assert abs(lo[i] - rec["bbox_min"][i]) < 1e-3 and abs(hi[i] - rec["bbox_max"][i]) < 1e-3, \
                "%s bbox %s..%s != manifest %s..%s" % (rec["name"], lo, hi, rec["bbox_min"], rec["bbox_max"])
        todo.append((ob, rec, src))

    print("\n  %d to delete, %d already absent (idempotent re-run)" % (len(todo), len(already)))
    for ob, rec, src in todo:
        print("    - %-28s %-16s verts=%d  z %.2f..%.2f   [%s]"
              % (ob.name, rec["landmark"], rec["verts"], rec["bbox_min"][2], rec["bbox_max"][2], src))
    if already:
        print("    (absent: %s)" % already)

    victims = [ob for ob, _, _ in todo]
    meshes = [ob.data for ob in victims]
    names = [ob.name for ob in victims]
    for ob in victims:
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in meshes:                              # the shells' meshes are 1:1, drop the orphans
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for n in names:
        assert bpy.data.objects.get(n) is None, "%s survived deletion" % n
    print("\n  deleted %d objects + %d orphan meshes" % (len(victims), len(meshes)))
    census("after")

# --------------------------------------------------------------------- append
if STEP in ("append", "all"):
    before = census("before")
    pre_mats = {m.name for m in bpy.data.materials}
    pre_imgs = {i.name for i in bpy.data.images}
    pre_objs = {o.name for o in bpy.data.objects}
    pre_colls = {c.name for c in bpy.data.collections}
    assert os.path.exists(BRANCH), BRANCH
    branch_mtime = os.path.getmtime(BRANCH)

    for cname in COLLS:
        assert bpy.data.collections.get(cname) is None, \
            "%s already present — append already ran; restore the backup first" % cname
        print("\n  appending %s from %s" % (cname, os.path.basename(BRANCH)))
        bpy.ops.wm.append(filepath=BRANCH + "/Collection/" + cname,
                          directory=BRANCH + "/Collection/",
                          filename=cname,
                          link=False, autoselect=False, instance_collections=False,
                          set_fake=False, use_recursive=True,
                          # deliberately NOT do_reuse_local_id: let the duplicates
                          # appear so the dedup step can COMPARE them to the local
                          # kit and report divergence instead of silently reusing.
                          do_reuse_local_id=False, active_collection=False)
        coll = bpy.data.collections.get(cname)
        assert coll is not None, "append produced no %s" % cname
        print("    -> %d objects" % len(coll.all_objects))

    # the branch must not have been touched
    assert os.path.getmtime(BRANCH) == branch_mtime, "the BRANCH BLEND WAS MODIFIED by the append"

    # wm.append parks an appended collection under an "Appended Data" wrapper.  Every
    # other district in this master is a direct child of the scene collection, so
    # unwrap: re-link the district at the root and drop the empty wrapper.
    root = bpy.context.scene.collection
    for w in [c for c in bpy.data.collections if c.name.startswith("Appended Data")]:
        for child in list(w.children):
            w.children.unlink(child)
            if child.name not in {c.name for c in root.children}:
                root.children.link(child)
        assert not w.objects and not w.children, "wrapper %s is not empty" % w.name
        wname = w.name
        if wname in {c.name for c in root.children}:
            root.children.unlink(w)
        bpy.data.collections.remove(w)
        print("    unwrapped and removed collection '%s'" % wname)
    for cname in COLLS:
        assert cname in {c.name for c in root.children}, "%s is not linked at the scene root" % cname

    after = census("after")
    new_objs = sorted({o.name for o in bpy.data.objects} - pre_objs)
    new_mats = sorted({m.name for m in bpy.data.materials} - pre_mats)
    new_imgs = sorted({i.name for i in bpy.data.images} - pre_imgs)
    print("\n  new objects   %d" % len(new_objs))
    for cname in COLLS:
        inside = {o.name for o in bpy.data.collections[cname].all_objects}
        print("     %-16s %d" % (cname, len(inside)))
    stray = [n for n in new_objs
             if not any(n in {o.name for o in bpy.data.collections[c].all_objects} for c in COLLS)]
    assert not stray, "append brought objects OUTSIDE the two district collections: %s" % stray[:20]
    print("     stray (outside both collections): 0")
    new_colls = sorted({c.name for c in bpy.data.collections} - pre_colls)
    print("  new collections %d: %s" % (len(new_colls), new_colls))
    for cn in new_colls:
        c = bpy.data.collections[cn]
        linked = cn in {x.name for x in bpy.context.scene.collection.children}
        print("     %-18s %3d objects, %d children, in scene root: %s"
              % (cn, len(c.objects), len(c.children), linked))

    dupe_mats = [n for n in new_mats if re.search(r"\.\d{3}$", n)]
    genuine_mats = [n for n in new_mats if n not in dupe_mats]
    dupe_imgs = [n for n in new_imgs if re.search(r"\.\d{3}$", n)]
    genuine_imgs = [n for n in new_imgs if n not in dupe_imgs]
    print("\n  new materials %d  = %d genuinely new + %d append duplicates"
          % (len(new_mats), len(genuine_mats), len(dupe_mats)))
    print("     genuinely new: %s" % genuine_mats)
    print("     duplicates:    %s" % dupe_mats)
    print("  new images    %d  = %d genuinely new + %d append duplicates"
          % (len(new_imgs), len(genuine_imgs), len(dupe_imgs)))
    print("     genuinely new: %s" % genuine_imgs)
    print("     duplicates:    %s" % dupe_imgs)
    print("\n  total datablocks %d -> %d  (+%d)"
          % (before["total_ids"], after["total_ids"], after["total_ids"] - before["total_ids"]))
    json.dump({"new_objects": new_objs, "new_materials": new_mats, "new_images": new_imgs,
               "before": before, "after": after},
              open("/tmp/west_merge_append.json", "w"), indent=1)

# ---------------------------------------------------------------------- dedup
if STEP in ("dedup", "all"):
    census("before")
    # IMAGES FIRST.  A material's signature names the image datablock it samples,
    # so collapsing the materials while `mat_deck` and `mat_deck.001` still point at
    # two different image datablocks for the same JPEG makes them look divergent.
    print("\n  IMAGES")
    ifams = defaultdict(list)
    for i in bpy.data.images:
        b = re.sub(r"\.\d{3}$", "", i.name)
        if b != i.name:
            ifams[b].append(i)
    iremap = idiv = 0
    for base in sorted(ifams):
        canon = bpy.data.images.get(base)
        if canon is None:
            ifams[base][0].name = base
            print("    %-40s NO local base — renamed" % base)
            continue
        for im in ifams[base]:
            # compare the RESOLVED file, not the stored string: the master holds a
            # few of these absolute and the branch holds them as `//../textures/...`
            if realfile(im) == realfile(canon):
                if im.filepath != canon.filepath:
                    print("    %-40s same file, path form differs (%s <- %s) — remapped"
                          % (base, canon.filepath, im.filepath))
                im.user_remap(canon)
                bpy.data.images.remove(im)
                iremap += 1
            else:
                idiv += 1
                print("    %-40s resolves to a DIFFERENT file (%s vs %s) — LEFT ALONE"
                      % (im.name, realfile(im), realfile(canon)))
    print("    %d duplicate images remapped+purged, %d divergent kept" % (iremap, idiv))

    print("\n  MATERIALS")
    fams = defaultdict(list)
    for m in bpy.data.materials:
        b = re.sub(r"\.\d{3}$", "", m.name)
        if b != m.name:
            fams[b].append(m)
    remapped = divergent = 0
    for base in sorted(fams):
        canon = bpy.data.materials.get(base)
        if canon is None:
            print("    %-24s NO local base datablock — renaming the copy to the free name" % base)
            fams[base][0].name = base
            continue
        csig = sig(canon)
        for m in fams[base]:
            same = sig(m) == csig
            users = sum(1 for o in bpy.data.objects if o.type == 'MESH'
                        for s in o.data.materials if s is m)
            was = m.name
            if same:
                m.user_remap(canon)
                bpy.data.materials.remove(m)
                remapped += 1
                print("    %-24s -> %-20s  (%d slots)  identical signature" % (was, base, users))
            else:
                divergent += 1
                print("    %-24s DIVERGENT from local %s (%d slots) — LEFT ALONE, inspect"
                      % (m.name, base, users))
    print("    %d duplicate materials remapped+purged, %d divergent kept" % (remapped, divergent))

    left = [m.name for m in bpy.data.materials if re.search(r"\.\d{3}$", m.name)]
    lefti = [i.name for i in bpy.data.images if re.search(r"\.\d{3}$", i.name)]
    print("\n  suffixed datablocks remaining: %d materials %s, %d images %s"
          % (len(left), left, len(lefti), lefti))
    # nothing in the two districts may still point at a suffixed material
    for cname in COLLS:
        for o in bpy.data.collections[cname].all_objects:
            if o.type != 'MESH':
                continue
            for s in o.data.materials:
                assert not (s and re.search(r"\.\d{3}$", s.name)), \
                    "%s still uses %s" % (o.name, s.name)
    # drop orphan meshes/materials the append may have left with 0 users
    orphan_me = [me for me in bpy.data.meshes if me.users == 0]
    for me in orphan_me:
        bpy.data.meshes.remove(me)
    print("  purged %d orphan meshes" % len(orphan_me))
    census("after")

# ----------------------------------------------------------------------- hide
if STEP in ("hide", "all"):
    census("before")
    bounds = {p["id"]: p["bounds"] for p in json.load(open(MAP))["parcels"]}
    PAD = 0.6                                   # a ribbon centre may sit just off the nominal edge
    boxes = []
    for pid in HIDE_PARCELS:
        b = bounds[pid]
        boxes.append((pid, b["min"], b["max"]))
        print("  %-12s x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f"
              % (pid, b["min"][0], b["max"][0], b["min"][1], b["max"][1], b["min"][2], b["max"][2]))
    hidden, per = [], defaultdict(int)
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
            continue
        b = world_bbox(o)
        c = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
        for pid, lo, hi in boxes:
            if (lo[0] - PAD <= c[0] <= hi[0] + PAD and lo[1] - PAD <= c[1] <= hi[1] + PAD
                    and lo[2] - PAD <= c[2] <= hi[2] + PAD):
                if not o.hide_render:
                    o.hide_render = True
                    hidden.append(o.name)
                per[pid] += 1
                break
        assert not o.hide_viewport, "%s is hide_viewport — the GLB would lose it (finding 51)" % o.name
    print("\n  ribbons inside the merged parcels: %s" % dict(per))
    print("  newly hide_render'd: %d" % len(hidden))
    for n in sorted(hidden):
        print("      %s" % n)
    tot = sum(1 for o in bpy.data.objects if o.name.startswith(("walk_", "bar_")) and o.hide_render)
    print("\n  master total render-hidden walk/bar ribbons: %d" % tot)
    assert not [o for o in bpy.data.objects
                if o.name.startswith(("walk_", "bar_")) and o.hide_viewport], \
        "a walk/bar mesh is viewport-hidden"
    census("after")

if STEP == "census":
    census("now")
    for cname in COLLS:
        c = bpy.data.collections.get(cname)
        print("  %-16s %s" % (cname, "%d objects" % len(c.all_objects) if c else "ABSENT"))
    for path in DEL_MANIFESTS:
        man = json.load(open(path))
        live = [r["name"] for r in man["deleted"] if bpy.data.objects.get(r["name"])]
        print("  %-32s %d/%d manifest names still present"
              % (os.path.basename(path), len(live), len(man["deleted"])))

print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved")
