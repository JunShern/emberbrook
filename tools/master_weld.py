"""master_weld.py — seam-weld the Boatyard district INTO tools/blends/dellhollow-master.blend.

ARCHITECTURE CANON: the town is ONE model.  This script edits the master IN PLACE
(open -> edit -> save).  It never copies the town out and never touches a walk_/bar_
mesh's geometry: walk topology is canonical and is only ever hidden from the beauty
render (exactly as the district blend does) so the detailed art can be what you see.

Run headless, one phase at a time:

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_weld.py -- cleanup
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_weld.py -- seam
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_weld.py -- fixes

Phases
  cleanup : delete the composite's leftovers (probe-space donor set that lost its
            hidden collection during the composite, doubled blockout massing),
            unify the lighting on the district's quality-gated sunset rig, hide
            the in-district walk ribbons from the beauty render.
  seam    : build the transition geometry along the district border (bank terrain
            continuing east under the blockout ribbon, kerbs, piles, gate posts,
            rope handline, rocks + tufts scattered over the join).
  fixes   : geometry-coherence fixes found by tools/geometry_audit.py.

Every destructive action prints a WELD-LOG line.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, coll, link, new_mesh, box, beam, cyl, offset_poly,
                          point_in_poly, plane_z_fn, dist_poly2, world_bbox, Corridor)

MASTER = REPO + "/tools/blends/dellhollow-master.blend"
DISTRICT = REPO + "/tools/blends/districts/boatyard.blend"
WALK_REF = REPO + "/tools/blends/districts/walk_reference.json"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASE = argv[0] if argv else "cleanup"
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("WELD-LOG %-9s %-46s %s" % (kind, what, why))


def M(name):
    return bpy.data.materials.get(name)


# ===========================================================================
# the composite's leftovers: boatyard.blend keeps its harvested probe donors in
# a collection PROBE_SRC with hide_render/hide_viewport set ON THE COLLECTION.
# town_master.py re-linked every appended object into one flat DIST_boatyard
# collection, which dropped those flags — so 54 donor objects (probe-space
# duplicates of yard buildings, kit prototypes, a second copy of every rig light,
# two fog boxes and the vegetation prototypes) became VISIBLE, most of them
# standing in the middle of the town at probe coordinates.
# ===========================================================================
PROBE_SRC = [
    "FILL_bounce", "FOG_BOX", "REF_human_1p7", "RIM_gorge", "SUN_key", "boat_shed",
    "cliff_back", "cliff_back2", "cliff_port", "cliff_stbd", "gate_spray",
    "hull_blocks", "hull_clinker", "hull_frames", "hull_shores", "kettle_fire",
    "kit_barrel", "kit_beam", "kit_bucket", "kit_crate", "kit_lantern_hanging",
    "kit_lantern_light", "kit_railing_1m", "kit_railing_post", "kit_rope_coil",
    "kit_stilt_trestle", "lantern_posts", "lock_four", "pilings", "pitch_kettle",
    "v10_apron", "v10_barge_mid", "v10_barge_port", "v10_barge_stbd", "v10_bunting",
    "v10_chandlery", "v10_embers", "v10_far_town", "v10_foreclutter", "v10_gallows",
    "v10_haze_far", "v10_haze_mid", "v10_haze_rim", "v10_kettle_smoke", "v10_netloft",
    "v10_paintwork", "v10_redcrates", "v10_shed_leanto", "v10_src_clump_a",
    "v10_src_clump_b", "v10_src_clump_far", "v10_src_creeper_a", "v10_src_creeper_b",
    "v10_src_tree_a", "v10_src_tree_b", "v10_src_tuft_fern", "v10_src_tuft_grass",
    "yard_clutter",
]
# donors that stay alive until the seam phase has used them as scatter prototypes
PROTO = ("v10_src_tuft_grass", "v10_src_tuft_fern", "v10_src_clump_a", "v10_src_clump_b",
         "kit_railing_post", "kit_rope_coil", "kit_barrel")

# blockout massing the district already replaced with detailed geometry
DOUBLED = {
    "dam_dam-four_crest": "replaced by lock_four_dam / dam4_lip",
    "dam_dam-four_wall": "replaced by lock_four_dam",
    "dam_dam-four_foam": "replaced by dam4_foam / dam4_spray",
    "e_winch-head__winch-foot": "replaced by cargo_winch_foot (detailed winch incline)",
}


def phase_cleanup():
    sc = bpy.context.scene

    # ---- 1. probe-space donor leftovers ------------------------------------
    n = 0
    for nm in PROBE_SRC:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        if nm in PROTO:
            ob.hide_render = True
            ob.hide_viewport = True
            log("HIDE", nm, "probe-space donor kept as scatter prototype (render+viewport off)")
            continue
        log("DELETE", nm, "probe-space donor leftover (was PROBE_SRC/hidden in the district)")
        bpy.data.objects.remove(ob, do_unlink=True)
        n += 1
    print("   -> %d donor leftovers deleted" % n)

    # ---- 2. doubled blockout massing ---------------------------------------
    for nm, why in DOUBLED.items():
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        assert not nm.startswith(("walk_", "bar_")), "refusing to touch canonical topology"
        log("DELETE", nm, why)
        bpy.data.objects.remove(ob, do_unlink=True)

    # ---- 3. build-time reference figure ------------------------------------
    ob = bpy.data.objects.get("REF_human_scale")
    if ob:
        log("DELETE", "REF_human_scale", "1.7u scale mannequin — build aid, not set dressing")
        bpy.data.objects.remove(ob, do_unlink=True)

    # ---- 4. lighting: ONE sunset key ---------------------------------------
    ob = bpy.data.objects.get("sun")
    if ob:
        log("DELETE", "sun (LIGHT)", "blockout's flat 3.2W sun — superseded by the district SUN_key")
        bpy.data.objects.remove(ob, do_unlink=True)
    for a, b in (("SUN_key.001", "SUN_key"), ("FILL_bounce.001", "FILL_bounce"),
                 ("RIM_gorge.001", "RIM_gorge"), ("kettle_fire.001", "kettle_fire"),
                 ("v10_haze_far.001", "v10_haze_far"), ("v10_haze_mid.001", "v10_haze_mid"),
                 ("v10_haze_rim.001", "v10_haze_rim")):
        o = bpy.data.objects.get(a)
        if o and bpy.data.objects.get(b) is None:
            o.name = b
            log("RENAME", "%s -> %s" % (a, b), "donor gone, drop the composite suffix")

    # unbounded fog: a 448 x 384 x 102 box over the whole town.  KITLIB_MANIFEST
    # finding 1/2: fog must be BOUNDED and must contain the far geometry — this one
    # contains the entire map and hazes the town to a flat brown card.  The three
    # v10_haze_* slabs (all west of x=-23) keep the distance layering.
    for nm in ("FOG_BOX", "FOG_BOX.001"):
        o = bpy.data.objects.get(nm)
        if o:
            log("DELETE", nm, "town-wide volume box — hazed the whole map flat (bounded fog only)")
            bpy.data.objects.remove(o, do_unlink=True)

    # ---- 4b. CONVENTION: every non-diegetic object carries the fx_ prefix ---
    # Render-only helpers (volume boxes, hazed backdrop masses, silhouettes) were
    # exporting into the runtime GLB as giant opaque boxes — a wall through the
    # river in the player view.  The durable rule is the NAME: fx_* is stripped by
    # the runtime exporter, so anything non-diegetic must be prefixed here.
    FX_MATS = ("mat_fog", "mat_smoke", "mat_spray", "mat_haze_far", "mat_haze_mid",
               "mat_haze_rim", "mat_silhouette")
    FX_NAMES = ("v10_haze_far", "v10_haze_mid", "v10_haze_rim", "ridge_upstream",
                "ridge_upstream_mid", "far_town_silhouette", "v10_far_town")
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or o.name.startswith("fx_"):
            continue
        vol = any(ms and ms.name in FX_MATS for ms in o.data.materials)
        if not (vol or o.name in FX_NAMES or o.name.endswith(("_smoke", "_plume", "_spray"))):
            continue
        old = o.name
        base = old
        for p in ("v10_", "k_v10_", "k_"):
            if base.startswith(p):
                base = base[len(p):]
        o.name = "fx_" + base
        log("RENAME", "%s -> %s" % (old, o.name), "render-only helper (non-diegetic; stripped from the GLB)")

    # the district's quality-gated sunset sky + grade
    if "DellhollowSunset" not in bpy.data.worlds:
        with bpy.data.libraries.load(DISTRICT) as (src, dst):
            dst.worlds = [w for w in src.worlds if w == "DellhollowSunset"]
    w = bpy.data.worlds.get("DellhollowSunset")
    if w:
        assert not (w.use_nodes and w.node_tree.nodes["World Output"].inputs["Volume"].is_linked), \
            "world volume would extinguish sun+sky (manifest finding 1)"
        sc.world = w
        log("WORLD", "DellhollowSunset", "district's gated sunset sky replaces the flat blockout world")
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.52
    log("GRADE", "AgX / Medium High Contrast / -0.52 EV", "matches the district's accepted grade")

    # EEVEE shadow atlas: 24 lights overflowed the default pool
    try:
        sc.eevee.shadow_pool_size = '512'
        log("EEVEE", "shadow_pool_size=512", "24 shadowed lights overflowed the default atlas")
    except Exception as e:
        print("   (shadow_pool_size unavailable: %s)" % e)

    # ---- 5. the town's water is the district's river -----------------------
    mw = M("mat_water")
    if mw:
        for nm in ("water_pool-upstream", "water_pool-mid", "water_pool-downstream"):
            o = bpy.data.objects.get(nm)
            if o:
                o.data.materials.clear()
                o.data.materials.append(mw)
                log("MATERIAL", nm, "m_water -> mat_water (one river, district's tuned water)")

    # ---- 6. walk ribbons inside the district: collision only ---------------
    ref = json.load(open(WALK_REF))
    hid = 0
    for nm in sorted(ref):
        o = bpy.data.objects.get(nm)
        if o:
            o.hide_render = True
            hid += 1
    log("HIDE_RENDER", "%d walk meshes (district footprint)" % hid,
        "blockout slabs were showing through the detailed decking; geometry untouched")
    # bar_ railings standing inside the detailed yard are blockout stand-ins too
    R = ((2.0, 32.0), (19.0, 33.0))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("bar_"):
            b = world_bbox(o)
            if b[0] >= R[0][0] - 1 and b[1] <= R[0][1] + 4 and b[2] >= R[1][0] - 1 and b[3] <= R[1][1] + 1:
                o.hide_render = True
                log("HIDE_RENDER", o.name, "blockout railing inside the detailed yard")


# ===========================================================================
# SEAM GEOMETRY
# ===========================================================================
# The district's own ground function, reused verbatim so the new bank leaves the
# yard at exactly the height (and the same noise phase) the yard arrives with.
def gh_noise(x, y):
    return (math.sin(x * 1.31 + y * 0.77) * 0.5 + math.sin(x * 0.43 - y * 2.11) * 0.32 +
            math.sin(x * 3.7 + y * 2.9) * 0.13) * 0.13


def seam_h(x, y):
    """Bank profile east of the yard.

    t runs 0 (the yard's last ground column, x=34.9) -> 1 (x=40.1).  Over that
    run the toe of the cliff walks north (the gorge opens out downstream), the
    shoreline walks south (the bank narrows and the walkway goes onto piles) and
    the cliff mass sheds height so the parcel ends as a rock spur in the river
    instead of a sawn-off wall.
    """
    t = max(0.0, min(1.0, (x - 34.9) / 5.2))
    toe = 21.4 + 2.7 * t
    ysh = 30.3 - 4.2 * t
    b = 3.15 - 0.030 * (x - 8.0)
    h = b - 0.10 * max(0.0, y - 24.0) - 1.35 * max(0.0, y - ysh)
    h += 2.60 * max(0.0, toe - y) ** 1.30 * (1.0 - 0.55 * t)
    h += gh_noise(x, y)
    # the spur plunges to the river bed over the last 0.8 m
    if x > 39.3:
        h -= (x - 39.3) / 0.8 * (h + 4.6)
    return h


def phase_seam():
    sc = bpy.context.scene
    rng = random.Random(70129)
    MROCK = M("mat_rock")
    MTIMBER = M("mat_timber")
    MDECK = M("mat_deck")
    MROPE = M("mat_rope")
    assert MROCK and MTIMBER and MDECK and MROPE, "district materials missing"

    # idempotent: a re-run replaces the weld, it does not stack a second one
    old = bpy.data.collections.get("SEAM_WELD")
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        log("REBUILD", "SEAM_WELD", "previous weld geometry cleared before rebuild")

    # the blockout's upstream pool runs to y=26 and so lies ON TOP of the yard's
    # lock-four walkways; the district had already pulled its own waterline back
    # to y=30.35, but the composite kept the blockout slab.  Re-cut it.
    w = bpy.data.objects.get("water_pool-upstream")
    if w:
        wz = max((w.matrix_world @ v.co).z for v in w.data.vertices)
        for v in w.data.vertices:
            p = w.matrix_world @ v.co
            if p.y < 30.35:
                v.co = w.matrix_world.inverted() @ Vector((p.x, 30.35, p.z))
        log("EDIT", "water_pool-upstream", "waterline y 26.0 -> 30.35 (it was lying over the "
            "lock-four walkways; matches the district's own water plane) top z=%.2f" % wz)

    walks = [o for o in bpy.data.objects
             if o.type == 'MESH' and o.name.startswith("walk_") and not o.hide_viewport]
    COR = Corridor(walks, margin=0.0)
    KEEPOUT = Corridor(walks, margin=0.45)

    def clear_of_walks(x, y, r, z):
        """No part of a footprint of radius r may sit in a walk corridor."""
        for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r),
                       (r * .7, r * .7), (-r * .7, r * .7), (r * .7, -r * .7), (-r * .7, -r * .7)):
            if KEEPOUT.blocked((x + dx, y + dy, z)):
                return False
            top = KEEPOUT.top_at(x + dx, y + dy)
            if top is not None and z > top - 0.30:
                return False
        return True
    tops = [(poly, fn, raw, nm) for poly, fn, raw, nm in COR.tops]

    def clamp_walks(x, y, h):
        for poly, fn, raw, nm in tops:
            d = dist_poly2(x, y, raw)
            if d < 3.4:
                h = min(h, fn(x, y) - 0.42 + d * 1.15)
        return h

    # ---- 1. the bank: terrain continuing east under the blockout ribbon ----
    x0, x1, y0, y1, st = 34.9, 40.1, 14.6, 30.2, 0.40
    nx = int(round((x1 - x0) / st)) + 1
    ny = int(round((y1 - y0) / st)) + 1
    verts, faces = [], []
    for i in range(nx):
        for j in range(ny):
            x = x0 + i * st
            y = y0 + j * st
            h = clamp_walks(x, y, seam_h(x, y))
            verts.append((x, y, max(h, -4.6)))
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            faces.append((a, a + ny, a + ny + 1, a + 1))
    new_mesh("seam_bank", verts, faces, MROCK, "SEAM_WELD")
    log("BUILD", "seam_bank", "%d x %d grid, x %.1f..%.1f y %.1f..%.1f — the yard's ground "
        "carried east under the blockout ribbon and stairs" % (nx, ny, x0, x1, y0, y1))

    # ---- 2. the ribbon the yard hands over to -----------------------------
    rib = bpy.data.objects.get("walk_e_fish-dock__winch-foot_l2")
    assert rib, "east seam ribbon missing"
    Mx = rib.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    top = None
    for p in rib.data.polygons:
        if (N @ p.normal).normalized().z > 0.9:
            top = [Mx @ rib.data.vertices[i].co for i in p.vertices]
            break
    assert top, "no top face on the seam ribbon"
    ztop = sum(v.z for v in top) / len(top)
    out = [(p.x, p.y) for p in offset_poly(top, 0.42)]   # outside footprint + QA margin (0.30)
    # order the offset quad: south edge (low y) and north edge (high y), west first
    cy = sum(p[1] for p in out) / len(out)
    south = sorted([p for p in out if p[1] < cy])
    north = sorted([p for p in out if p[1] >= cy])

    def edge_run(a, b, name, w, h, mat, upto=6.0):
        """A kerb beam from a, running toward b, at most `upto` metres."""
        ax, ay = a
        bx, by = b
        L = math.hypot(bx - ax, by - ay)
        f = min(1.0, upto / max(L, 1e-6))
        return beam(name, (ax, ay, ztop - h * 0.55), (ax + (bx - ax) * f, ay + (by - ay) * f, ztop - h * 0.55),
                    w, h, mat, "SEAM_WELD")

    kerbs = []
    kerbs.append(edge_run(south[0], south[1], "seam_kerb_s", 0.20, 0.22, MTIMBER, 5.4))
    kerbs.append(edge_run(north[0], north[1], "seam_kerb_n", 0.20, 0.22, MTIMBER, 4.2))
    log("BUILD", "seam_kerb_s / seam_kerb_n",
        "timber kerbs flanking the first metres of the blockout ribbon (outside the corridor)")

    # ---- 3. piles under the ribbon's river side ---------------------------
    piles = []
    sx, sy = north[0]
    ex, ey = north[1]
    for k in range(4):
        f = 0.18 + 0.26 * k
        px = sx + (ex - sx) * f
        py = sy + (ey - sy) * f
        gz = seam_h(px, py)
        piles.append(cyl("seam_pile_%d" % k, (px, py, min(gz, -0.3)), (px, py, ztop - 0.16),
                         0.17, 8, MTIMBER, "SEAM_WELD"))
    log("BUILD", "seam_pile_0..3", "the blockout ribbon now stands on piles where the bank runs out")

    # ---- 4. the yard's east gate: post pair + high rope swag --------------
    gx, gy = 35.35, 0.0
    posts = []
    for side, (px, py) in (("s", south[0]), ("n", north[0])):
        gz = clamp_walks(px, py, seam_h(px, py))
        top = ztop + (2.95 if side == "n" else 3.15)
        posts.append(beam("seam_gatepost_%s" % side, (px, py, gz - 0.35), (px, py, top),
                          0.26, 0.26, MTIMBER, "SEAM_WELD"))
    a = posts[0].location if False else None
    pA = (south[0][0], south[0][1], ztop + 2.95)
    pB = (north[0][0], north[0][1], ztop + 2.80)
    seg = []
    N = 12
    for k in range(N):
        f0, f1 = k / N, (k + 1) / N
        def swag(f):
            x = pA[0] + (pB[0] - pA[0]) * f
            y = pA[1] + (pB[1] - pA[1]) * f
            z = pA[2] + (pB[2] - pA[2]) * f - 0.50 * math.sin(math.pi * f)
            return (x, y, z)
        seg.append(cyl("seam_swag_%d" % k, swag(f0), swag(f1), 0.035, 6, MROPE, "SEAM_WELD"))
    log("BUILD", "seam_gatepost_s/n + seam_swag",
        "gate posts flanking the hand-over point, rope swag 2.1 m clear of the walk top")

    # ---- 5. rope handline along the water side ----------------------------
    rails = []
    for k in range(3):
        f = 0.30 + 0.30 * k
        px = sx + (ex - sx) * f
        py = sy + (ey - sy) * f
        rails.append((px, py))
    proto_post = bpy.data.objects.get("kit_railing_post")
    parts = []
    for k, (px, py) in enumerate(rails):
        parts.append(beam("seam_railpost_%d" % k, (px, py, ztop - 0.25), (px, py, ztop + 1.02),
                          0.11, 0.11, MTIMBER, "SEAM_WELD"))
    for k in range(len(rails) - 1):
        (ax, ay), (bx, by) = rails[k], rails[k + 1]
        for s in range(6):
            f0, f1 = s / 6, (s + 1) / 6
            def hl(f):
                return (ax + (bx - ax) * f, ay + (by - ay) * f,
                        ztop + 0.94 - 0.10 * math.sin(math.pi * f))
            cyl("seam_handline_%d_%d" % (k, s), hl(f0), hl(f1), 0.028, 6, MROPE, "SEAM_WELD")
    log("BUILD", "seam_railpost_0..2 + seam_handline",
        "rope handline on the river side of the hand-over — the boardwalk language continues")

    # ---- 6. rocks + tufts over the join -----------------------------------
    rocks = []
    for k in range(26):
        rx = 34.4 + rng.random() * 5.2
        ry = 19.0 + rng.random() * 9.0
        gz = clamp_walks(rx, ry, seam_h(rx, ry))
        if gz < -1.0 or gz > 9.0:
            continue
        r = 0.32 + rng.random() * 0.55
        if not clear_of_walks(rx, ry, r * 1.6, gz + r * 0.5):
            continue
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        for v in bm.verts:
            v.co.x *= 1.0 + rng.random() * 0.5
            v.co.y *= 1.0 + rng.random() * 0.4
            v.co.z *= 0.52 + rng.random() * 0.25
            v.co += Vector((rng.random() - 0.5, rng.random() - 0.5, rng.random() - 0.5)) * r * 0.28
        me = bpy.data.meshes.new("seam_rock_%d" % k)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(MROCK)
        ob = bpy.data.objects.new("seam_rock_%d" % k, me)
        link(ob, "SEAM_WELD")
        ob.location = (rx, ry, gz + r * 0.22)
        ob.rotation_euler = (0, 0, rng.random() * 6.28)
        rocks.append(ob)
    log("BUILD", "seam_rock_* (%d)" % len(rocks), "boulders bedded along the ground/blockout join")

    tufts = 0
    protos = [bpy.data.objects.get(n) for n in ("v10_src_tuft_grass", "v10_src_tuft_fern",
                                               "v10_src_clump_a", "v10_src_clump_b")]
    protos = [p for p in protos if p]
    for k in range(80):
        px = 34.2 + rng.random() * 5.4
        py = 17.6 + rng.random() * 11.4
        gz = clamp_walks(px, py, seam_h(px, py))
        if gz < 0.15 or gz > 12.0:
            continue
        if not clear_of_walks(px, py, 0.55, gz + 0.45):
            continue
        src = protos[k % len(protos)] if k % 3 else protos[0]
        ob = src.copy()
        ob.data = src.data
        ob.hide_render = False
        ob.hide_viewport = False
        link(ob, "SEAM_WELD")
        ob.location = (px, py, gz - 0.05)
        ob.rotation_euler = (0, 0, rng.random() * 6.28)
        s = 0.8 + rng.random() * 0.55
        ob.scale = (s, s, s)
        ob.name = "seam_tuft_%d" % k
        tufts += 1
    log("BUILD", "seam_tuft_* (%d)" % tufts, "grass/fern/clump scatter carried over the join")


def phase_palette():
    """The blockout's placeholder palette, re-valued for the sunset key.

    The gray-town materials were authored under the blockout's flat 3.2 W neutral
    sun.  Under the district's 5 W sunset key at -0.52 EV a 0.5-albedo surface
    lands on the AgX shoulder: every ribbon, stair and landmark block renders
    pale salmon, and the detailed district — whose textures are darkened 0.42..0.62
    with a moss layer over them — reads as a dark hole beside it.  That value gap,
    not the geometry, is what makes the two datasets look like two datasets.
    Nothing here touches geometry; it is the placeholder palette only.
    """
    TUNE = {           # name: (multiplier, roughness or None)
        "m_wood": (0.46, None),
        "m_stair": (0.44, None),
        "m_gray": (0.42, None),
        "m_port": (0.40, None),
        "m_rock": (0.52, None),
        "m_foam": (0.70, None),
        "m_dam": (0.85, None),
    }
    for nm, (mul, rough) in TUNE.items():
        m = M(nm)
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                c = n.inputs["Base Color"].default_value
                old = tuple(round(v, 3) for v in c[:3])
                n.inputs["Base Color"].default_value = (c[0] * mul, c[1] * mul, c[2] * mul, 1.0)
                if rough is not None:
                    n.inputs["Roughness"].default_value = rough
                log("PALETTE", nm, "base %s -> %s (x%.2f)" %
                    (old, tuple(round(v * mul, 3) for v in old), mul))
    # the river: one water surface for the whole town, in the district's key
    m = M("m_water")
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs["Base Color"].default_value = (0.040, 0.105, 0.120, 1.0)
                n.inputs["Roughness"].default_value = 0.10
                log("PALETTE", "m_water", "pale flat blue -> deep teal, glossy (rough 0.10)")


def phase_fixes():
    """Geometry-coherence fixes (see tools/geometry_audit.py for how they were found)."""
    import master_weld_fixes as F
    F.apply(log)


if __name__ == "__main__":
    print("=" * 74)
    print("MASTER WELD — phase:", PHASE)
    print("=" * 74)
    if PHASE == "cleanup":
        phase_cleanup()
    elif PHASE == "seam":
        phase_seam()
    elif PHASE == "palette":
        phase_palette()
    elif PHASE == "fixes":
        phase_fixes()
    else:
        raise SystemExit("unknown phase %s" % PHASE)
    bpy.ops.wm.save_as_mainfile(filepath=MASTER)
    print("-" * 74)
    print("%d log entries | objects now %d | saved %s" % (len(LOG), len(bpy.data.objects), MASTER))
