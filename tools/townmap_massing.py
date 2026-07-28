"""
townmap_massing.py — town graph (JSON) -> abstract 3D diagram, in Blender.

Reads public/townmap/<town>.map.json and generates a spatial DIAGRAM of the
town graph: labelled pins for landmarks, thin connection lines for edges,
wireframe parcel bounds, and one ortho camera per parcel.

DESIGN RULE (deliberate, do not "improve" this):
    The generated geometry is NEVER representational. There are no buildings,
    roofs, docks, signs or machinery. Every landmark gets the SAME abstract
    marker regardless of `kind`; kind may tint colour but must never change
    shape. Reason: massing geometry must not influence or constrain town
    design. A future underground town's "shop" is a cave, not a box, and a
    diagram that already drew a box would quietly pre-decide that.

Town-agnostic: set TOWN (and REPO_ROOT if the script is not in <repo>/tools).

Axes match the town graph exactly (both are Z-up):
    x = along gorge, y = cliff (0) toward river (~30), z = height (water ~0)

Outputs
    tools/blends/<town>-massing.blend
    docs/qa/townmap/<town>/overview-elevation.png   1600x900
    docs/qa/townmap/<town>/overview-plan.png        1600x900
    docs/qa/townmap/<town>/parcel-<parcelId>.png    1344x768  (one per parcel)

Object naming
    massing_<landmarkId>      the pin marker (cylinder + head sphere)
    label_<landmarkId>        upright name label (readable in elevation / 3-4)
    labelplan_<landmarkId>    flat name label (readable in the top-down plan)
    edge_<from>__<to>         connection line (dashed for stairs)
    parcel_<parcelId>         wireframe bounds box
    cam_<parcelId>            ortho 3/4 camera framing that parcel
    cam_overview_elevation / cam_overview_plan

Stair climbability is a DATA check, not geometry: see stairs_report().

Run headless:
    blender -b -P tools/townmap_massing.py
Run inside a live Blender (or over the Blender MCP), in stages:
    ns = {}; exec(open(PATH).read(), ns)
    ns["build_scene"](); ns["save_blend"](); ns["render_all"]()

Blender 5.x notes observed while writing this:
  - Camera.calc_matrix_camera is REMOVED; framing here is done with plain
    matrix math on the 8 bounds corners, so nothing camera-internal is needed.
  - scene.node_tree / compositor is reworked; this script never touches it.
  - EEVEE's engine id moved around across versions, so it is resolved against
    the live enum rather than hardcoded.
  - bmesh.ops.create_icosphere takes `radius` (older builds took `diameter`);
    both spellings are attempted.
  - Keep source ASCII: no unicode minus signs.
"""

import bpy
import bmesh
import json
import math
import os
from mathutils import Vector, Matrix

# ============================================================== configuration

TOWN = "dellhollow"

# Repo root: auto-detect from this file's location (<repo>/tools/...), with a
# literal fallback for when __file__ is undefined (exec'd over the MCP).
try:
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    REPO_ROOT = "/Users/junshernchan/projects/multiplayer-rpg"

MAP_PATH   = os.path.join(REPO_ROOT, "public", "townmap", TOWN + ".map.json")
BLEND_PATH = os.path.join(REPO_ROOT, "tools", "blends", TOWN + "-massing.blend")
QA_DIR     = os.path.join(REPO_ROOT, "docs", "qa", "townmap", TOWN)

RES_OVERVIEW = (1600, 900)
RES_PARCEL   = (1344, 768)

# --- marker geometry (identical for every landmark kind) --------------------
PIN_RADIUS   = 0.15
PIN_HEIGHT   = 2.0
HEAD_RADIUS  = 0.38
LABEL_SIZE   = 0.8
LABEL_STAGGER = (0.0, 1.15, 2.30)   # cycled per landmark so labels miss each other

# --- edge geometry ----------------------------------------------------------
LINE_RADIUS  = 0.08     # road / deck / path / stairs dashes
CABLE_RADIUS = 0.05     # winch: thinnest, clearly not a route
DASH_FILL    = 0.55     # fraction of each slot a stairs dash occupies
MAX_DASHES   = 40

# --- stair data check (no geometry involved) --------------------------------
TREAD_RISE_AIM = 0.4    # implied tread count = ceil(rise / this)
MAX_TREAD_RISE = 0.5    # hard rule the implied tread count must satisfy

CAMERA_MARGIN   = 1.10  # ortho framing slack (~10%)
ADD_DATUM_PLANE = True  # neutral z=0 reference plane so heights read

DEFAULT_CAM_DIR = (1.0, -1.0, 0.78)   # classic 3/4: +X, -Y, +Z off the centre
DEFAULT_CAM_MARGIN = 0.10             # fraction, matching the JSON schema

# Flat district hues, assigned in districts[] order (any distinct hues).
DISTRICT_PALETTE = [
    (1.00, 0.62, 0.35), (0.44, 0.83, 1.00), (0.71, 0.55, 1.00),
    (0.49, 0.88, 0.54), (1.00, 0.84, 0.37), (1.00, 0.48, 0.61),
    (0.35, 0.83, 0.75), (0.79, 0.63, 0.42), (0.62, 0.71, 1.00),
    (1.00, 0.63, 0.85),
]
HIDDEN_TINT = 0.46      # mapVisible:false markers are this fraction as bright

EDGE_COLORS = {
    "road":   (0.62, 0.70, 0.80),
    "deck":   (0.42, 0.49, 0.58),
    "stairs": (1.00, 0.84, 0.37),
    "path":   (0.49, 0.88, 0.54),
    "winch":  (1.00, 0.48, 0.61),
}
EDGE_FALLBACK_COLOR = (0.50, 0.50, 0.50)
PARCEL_WIRE_COLOR   = (0.42, 0.46, 0.52)
PARCEL_ACTIVE_COLOR = (1.00, 0.70, 0.20)   # the parcel a per-parcel render is about
DATUM_COLOR         = (0.06, 0.11, 0.16)

# Build log, filled by build_scene(), consumed by self_check().
REPORT = {"landmarks": [], "edges": [], "parcels": [], "stairs": [], "warnings": []}


# ==================================================================== helpers

def log(*a):
    print("[massing]", *a)


def load_map(path):
    with open(path, "r") as f:
        return json.load(f)


def reset_scene():
    """Wipe everything so the build is reproducible from any starting state."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.curves):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def get_collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def flat_material(name, rgb, emission=0.35):
    """Flat, self-lit-ish material. A diagram wants legible colour, not shading."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.95
        for spec_key in ("Specular IOR Level", "Specular"):
            if spec_key in bsdf.inputs:
                bsdf.inputs[spec_key].default_value = 0.05
                break
        # a little emission keeps thin pins and lines readable against the dark
        if "Emission Color" in bsdf.inputs and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return mat


# ------------------------------------------------------------ bmesh primitives

def bm_box(bm, cx, cy, cz, sx, sy, sz):
    """Axis-aligned box, centred on (cx, cy, cz)."""
    mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((sx, sy, sz, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def bm_cylinder(bm, p1, p2, radius, segments=10):
    """Capped cylinder spanning p1 -> p2."""
    a, b = Vector(p1), Vector(p2)
    d = b - a
    length = d.length
    if length < 1e-6:
        return
    rot = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    mat = Matrix.Translation((a + b) * 0.5) @ rot
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=length, matrix=mat)


def bm_sphere(bm, centre, radius, subdivisions=2):
    """Small sphere; `radius` was spelled `diameter` in older bmesh builds."""
    mat = Matrix.Translation(centre)
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=subdivisions,
                                   radius=radius, matrix=mat)
    except TypeError:
        bmesh.ops.create_icosphere(bm, subdivisions=subdivisions,
                                   diameter=radius, matrix=mat)


def finish(bm, name, material, collection):
    """Turn a bmesh into one named object with one material."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    if material is not None:
        obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def make_text(name, body, location, rotation, material, collection,
              size=LABEL_SIZE, align_x="CENTER", align_y="BOTTOM"):
    td = bpy.data.curves.new(name, type="FONT")
    td.body = body
    td.size = size
    td.align_x = align_x
    td.align_y = align_y
    obj = bpy.data.objects.new(name, td)
    obj.location = location
    obj.rotation_euler = rotation
    if material is not None:
        obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


# ======================================================== landmark markers

def build_landmark(lm, material, coll_pins, coll_labels, idx=0):
    """
    ONE abstract marker per landmark, identical for every kind:
    a thin vertical pin from z to z + PIN_HEIGHT, topped with a small sphere,
    plus two name labels (one upright for elevation/three-quarter views, one
    flat for the top-down plan view).

    Kind is recorded as a custom property only. It must never change the shape.
    """
    x, y, z = lm["pos"]
    lid = lm["id"]

    bm = bmesh.new()
    bm_cylinder(bm, (x, y, z), (x, y, z + PIN_HEIGHT), PIN_RADIUS, segments=8)
    bm_sphere(bm, (x, y, z + PIN_HEIGHT), HEAD_RADIUS)
    obj = finish(bm, "massing_" + lid, material, coll_pins)
    obj["landmark_id"] = lid
    obj["kind"] = lm.get("kind", "")
    obj["district"] = lm.get("district", "")
    obj["map_visible"] = bool(lm.get("mapVisible", True))

    name = lm.get("name", lid)
    # Landmarks on the same district tier share a z, so their labels would
    # collide in elevation. Stagger by index: deterministic, and enough to
    # separate neighbours along a street.
    tier = LABEL_STAGGER[idx % len(LABEL_STAGGER)]

    # upright: text plane rotated into XZ so it faces -Y (the elevation camera)
    make_text("label_" + lid, name,
              (x, y, z + PIN_HEIGHT + HEAD_RADIUS + 0.25 + tier),
              (math.radians(90.0), 0.0, 0.0), material, coll_labels)
    # flat: text left in XY so it reads from directly above (the plan camera)
    make_text("labelplan_" + lid, name,
              (x, y + HEAD_RADIUS + 0.5 + tier, z + PIN_HEIGHT + 0.4),
              (0.0, 0.0, 0.0), material, coll_labels)

    REPORT["landmarks"].append((lid, lm.get("kind", ""), obj.name))
    return obj


# ============================================================ edge connectors

def build_dashes(bm, a, b, radius, dashes):
    """A run of short segments along a->b, so an edge reads as 'stepped'."""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, min(int(dashes), MAX_DASHES))
    slot = 1.0 / n
    for i in range(n):
        t0 = i * slot
        t1 = t0 + slot * DASH_FILL
        bm_cylinder(bm, a + d * t0, a + d * t1, radius, segments=6)


def build_edge(edge, lm_by_id, materials, coll):
    """
    A thin line between the two landmark positions, at their true z.
    No walkable surface is generated: this is a diagram of connectivity, and
    the real traversal geometry is the scene builder's decision, not ours.
    """
    a_lm = lm_by_id.get(edge["from"])
    b_lm = lm_by_id.get(edge["to"])
    name = "edge_%s__%s" % (edge["from"], edge["to"])
    if a_lm is None or b_lm is None:
        REPORT["warnings"].append(
            "SKIPPED %s: dangling endpoint (%s present: %s / %s present: %s)"
            % (name, edge["from"], a_lm is not None, edge["to"], b_lm is not None))
        return None

    a, b = a_lm["pos"], b_lm["pos"]
    etype = edge.get("type", "path")
    # lift to the pin head so lines meet the markers rather than the ground
    az = (a[0], a[1], a[2] + PIN_HEIGHT * 0.5)
    bz = (b[0], b[1], b[2] + PIN_HEIGHT * 0.5)

    bm = bmesh.new()
    if etype == "stairs":
        rise = abs(b[2] - a[2])
        treads = max(2, int(math.ceil(rise / TREAD_RISE_AIM)))
        build_dashes(bm, az, bz, LINE_RADIUS, treads)
    elif etype == "winch":
        bm_cylinder(bm, az, bz, CABLE_RADIUS, segments=6)
    else:
        bm_cylinder(bm, az, bz, LINE_RADIUS, segments=8)

    mat = materials.get("edge_" + etype, materials["edge_other"])
    obj = finish(bm, name, mat, coll)
    obj["edge_type"] = etype
    obj["walkable"] = etype != "winch"
    REPORT["edges"].append((name, etype, obj.name))
    return obj


# ================================================================ parcel boxes

def build_parcel_box(parcel, material, coll):
    """Bounds box rendered as a wireframe cage (Wireframe modifier on a cube)."""
    mn, mx = parcel["bounds"]["min"], parcel["bounds"]["max"]
    cx, cy, cz = [(mn[i] + mx[i]) * 0.5 for i in range(3)]
    sx, sy, sz = [max(mx[i] - mn[i], 0.01) for i in range(3)]
    bm = bmesh.new()
    bm_box(bm, cx, cy, cz, sx, sy, sz)
    obj = finish(bm, "parcel_" + parcel["id"], material, coll)
    mod = obj.modifiers.new("wire", "WIREFRAME")
    mod.thickness = 0.16
    mod.use_replace = True
    obj["parcel_id"] = parcel["id"]
    obj["scene_key"] = parcel.get("sceneKey", "")
    REPORT["parcels"].append((parcel["id"], obj.name))
    return obj


# ===================================================================== cameras

def _corners(mn, mx):
    return [Vector((mn[0] if i & 1 else mx[0],
                    mn[1] if i & 2 else mx[1],
                    mn[2] if i & 4 else mx[2])) for i in range(8)]


def make_ortho_camera(name, mn, mx, direction, res, coll, margin=CAMERA_MARGIN):
    """
    Orthographic camera looking at the centre of the box (mn..mx) from
    `direction`, with ortho_scale sized to frame all 8 corners plus margin.

    Blender 5.x removed Camera.calc_matrix_camera, so framing is computed by
    transforming the corners into camera space directly. ortho_scale spans the
    LARGER sensor axis, i.e. the width when aspect >= 1.
    """
    centre = Vector(((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5))
    diag = (Vector(mx) - Vector(mn)).length
    d = Vector(direction).normalized()
    dist = max(diag * 1.6, 10.0)
    loc = centre + d * dist

    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = loc
    # look from loc toward centre; Blender cameras aim down local -Z
    cam_obj.rotation_euler = (centre - loc).to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(cam_obj)
    bpy.context.view_layer.update()

    inv = cam_obj.matrix_world.inverted()
    max_x = max_y = max_depth = 0.0
    for c in _corners(mn, mx):
        p = inv @ c
        max_x = max(max_x, abs(p.x))
        max_y = max(max_y, abs(p.y))
        max_depth = max(max_depth, abs(p.z))

    aspect = float(res[0]) / float(res[1])
    if aspect >= 1.0:
        scale = max(2.0 * max_x, 2.0 * max_y * aspect)
    else:
        scale = max(2.0 * max_y, 2.0 * max_x / aspect)
    cam_data.ortho_scale = max(scale * margin, 1.0)
    cam_data.clip_start = 0.1
    cam_data.clip_end = max_depth + dist + diag + 200.0
    return cam_obj


def parcel_camera_spec(parcel):
    """
    Direction and framing margin for one parcel's scene camera.

    MIRRORS deriveParcelCamera() in public/townmap/viewer.html, so the frustum
    reviewed in the browser's 3D tab is exactly the shot rendered here. If you
    change one, change the other.

    Optional per-parcel override in the town JSON:
        parcels[].camera = { "yaw": <deg about the up axis>,
                             "pitch": <deg above the horizon>,
                             "margin": <fraction, default 0.1> }
    Absent -> the deterministic default above.

    Returns (direction, margin_multiplier, authored, yaw_deg, pitch_deg).
    """
    ov = parcel.get("camera") or {}
    d0 = DEFAULT_CAM_DIR
    yaw = float(ov.get("yaw", math.degrees(math.atan2(d0[1], d0[0]))))
    pitch = float(ov.get("pitch",
                  math.degrees(math.atan2(d0[2], math.hypot(d0[0], d0[1])))))
    margin = float(ov.get("margin", DEFAULT_CAM_MARGIN))
    ry, rp = math.radians(yaw), math.radians(pitch)
    direction = (math.cos(rp) * math.cos(ry),
                 math.cos(rp) * math.sin(ry),
                 math.sin(rp))
    return direction, 1.0 + margin, bool(ov), yaw, pitch


def town_bounds(town):
    """Union of every parcel box and every landmark position."""
    mn = [1e9, 1e9, 1e9]
    mx = [-1e9, -1e9, -1e9]
    def eat(p):
        for i in range(3):
            mn[i] = min(mn[i], p[i])
            mx[i] = max(mx[i], p[i])
    for lm in town.get("landmarks", []):
        eat(lm["pos"])
    for p in town.get("parcels", []):
        eat(p["bounds"]["min"])
        eat(p["bounds"]["max"])
    if mn[0] > mx[0]:
        mn, mx = [0, 0, 0], [10, 10, 10]
    pad = 4.0
    return ([mn[i] - pad for i in range(3)], [mx[i] + pad for i in range(3)])


# ================================================================ scene set-up

def pick_engine():
    """EEVEE's enum id has moved between versions; resolve against the live enum."""
    try:
        items = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
        ids = [i.identifier for i in items]
    except Exception:
        ids = []
    for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if candidate in ids:
            return candidate
    return ids[0] if ids else "BLENDER_EEVEE"


def setup_world_and_light(coll):
    scene = bpy.context.scene
    scene.render.engine = pick_engine()
    log("render engine:", scene.render.engine)
    scene.render.image_settings.file_format = "PNG"
    # Blender defaults to 15% PNG compression, which makes these flat-colour
    # diagrams ~2 MB each for no reason. Flat art compresses hard.
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 90
    scene.render.film_transparent = False
    ev = getattr(scene, "eevee", None)
    if ev is not None and hasattr(ev, "taa_render_samples"):
        ev.taa_render_samples = 24

    world = bpy.data.worlds.get("massing_world") or bpy.data.worlds.new("massing_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:                       # ambient fill
        bg.inputs[0].default_value = (0.10, 0.12, 0.15, 1.0)
        bg.inputs[1].default_value = 1.1
    scene.world = world

    sun_data = bpy.data.lights.new("sun_key", "SUN")
    sun_data.energy = 3.2
    if hasattr(sun_data, "angle"):
        sun_data.angle = math.radians(3.0)
    # Cast shadows smear streaks across the datum plane and obscure the pins.
    # A diagram wants flat readability: directional shading only, no shadows.
    if hasattr(sun_data, "use_shadow"):
        sun_data.use_shadow = False
    sun = bpy.data.objects.new("sun_key", sun_data)
    sun.rotation_euler = (math.radians(52.0), 0.0, math.radians(38.0))
    sun.location = (0.0, 0.0, 60.0)
    coll.objects.link(sun)


def build_materials(town):
    mats = {}
    for i, d in enumerate(town.get("districts", [])):
        rgb = DISTRICT_PALETTE[i % len(DISTRICT_PALETTE)]
        mats["district_" + d["id"]] = flat_material("mat_district_" + d["id"], rgb)
        dim = tuple(c * HIDDEN_TINT for c in rgb)
        mats["hidden_" + d["id"]] = flat_material("mat_district_" + d["id"] + "_hidden",
                                                  dim, emission=0.12)
    mats["district_unknown"] = flat_material("mat_district_unknown", (0.55, 0.55, 0.58))
    mats["hidden_unknown"] = flat_material("mat_district_unknown_hidden",
                                           (0.19, 0.19, 0.20), emission=0.12)
    for etype, rgb in EDGE_COLORS.items():
        mats["edge_" + etype] = flat_material("mat_edge_" + etype, rgb)
    mats["edge_other"] = flat_material("mat_edge_other", EDGE_FALLBACK_COLOR)
    mats["parcel"] = flat_material("mat_parcel_wire", PARCEL_WIRE_COLOR)
    mats["parcel_active"] = flat_material("mat_parcel_wire_active", PARCEL_ACTIVE_COLOR)
    mats["datum"] = flat_material("mat_datum", DATUM_COLOR, emission=0.0)
    return mats


def landmark_material(lm, mats):
    """Colour by district; markers hidden from the player map are tinted dark."""
    did = str(lm.get("district"))
    hidden = lm.get("mapVisible", True) is False
    prefix = "hidden_" if hidden else "district_"
    return mats.get(prefix + did, mats[prefix + "unknown"])


# =================================================================== the build

def build_scene(map_path=None):
    """Generate the whole diagram. Idempotent: resets the scene first."""
    path = map_path or MAP_PATH
    town = load_map(path)
    log("town:", town.get("displayName", town.get("town")), "from", path)

    for k in REPORT:
        REPORT[k] = []

    reset_scene()
    c_env    = get_collection("env")
    c_pins   = get_collection("landmarks")
    c_labels = get_collection("labels")
    c_edges  = get_collection("edges")
    c_parcel = get_collection("parcels")
    c_cams   = get_collection("cameras")

    setup_world_and_light(c_env)
    mats = build_materials(town)
    lm_by_id = {lm["id"]: lm for lm in town.get("landmarks", [])}

    for idx, lm in enumerate(town.get("landmarks", [])):
        build_landmark(lm, landmark_material(lm, mats), c_pins, c_labels, idx=idx)

    for e in town.get("edges", []):
        build_edge(e, lm_by_id, mats, c_edges)

    for p in town.get("parcels", []):
        build_parcel_box(p, mats["parcel"], c_parcel)
        direction, margin, authored, yaw, pitch = parcel_camera_spec(p)
        cam = make_ortho_camera("cam_" + p["id"], p["bounds"]["min"], p["bounds"]["max"],
                                direction, RES_PARCEL, c_cams, margin=margin)
        log("camera cam_%-14s yaw=%7.2f pitch=%6.2f margin=%4.0f%% ortho=%6.2f  %s"
            % (p["id"], yaw, pitch, (margin - 1.0) * 100, cam.data.ortho_scale,
               "AUTHORED (parcels[].camera)" if authored else "default"))

    mn, mx = town_bounds(town)
    # elevation-ish: look mostly along +Y (x horizontal, z vertical), slight tilt
    make_ortho_camera("cam_overview_elevation", mn, mx, (0.16, -1.0, 0.13),
                      RES_OVERVIEW, c_cams)
    # plan: straight down
    make_ortho_camera("cam_overview_plan", mn, mx, (0.0, 0.0, 1.0),
                      RES_OVERVIEW, c_cams)

    if ADD_DATUM_PLANE:
        bm = bmesh.new()
        bm_box(bm, (mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, -0.6,
               (mx[0] - mn[0]) + 40.0, (mx[1] - mn[1]) + 40.0, 1.2)
        finish(bm, "env_datum_z0", mats["datum"], c_env)

    stairs_report(town)
    self_check(town)
    return town


# ========================================================= stair DATA check

def stairs_report(town):
    """
    Climbability as pure data. No geometry is generated from this.

      rise   = |z2 - z1|
      run    = horizontal distance between the endpoints
      treads = ceil(rise / TREAD_RISE_AIM), so rise/tread <= TREAD_RISE_AIM
      SUSPECT when run < rise, i.e. the flight is steeper than 45 degrees and
      no sane staircase fits between those two points.
    """
    lm_by_id = {lm["id"]: lm for lm in town.get("landmarks", [])}
    REPORT["stairs"] = []
    for e in town.get("edges", []):
        if e.get("type") != "stairs":
            continue
        a = lm_by_id.get(e["from"])
        b = lm_by_id.get(e["to"])
        if a is None or b is None:
            continue
        rise = abs(a["pos"][2] - b["pos"][2])
        run = math.hypot(b["pos"][0] - a["pos"][0], b["pos"][1] - a["pos"][1])
        treads = max(1, int(math.ceil(rise / TREAD_RISE_AIM)))
        per = rise / treads if treads else 0.0
        slope = math.degrees(math.atan2(rise, run)) if run > 1e-9 else 90.0
        REPORT["stairs"].append({
            "edge": "edge_%s__%s" % (e["from"], e["to"]),
            "rise": rise, "run": run, "treads": treads, "per": per,
            "slope_deg": slope,
            "flat": rise == 0.0,
            "suspect": run < rise,
        })
    return REPORT["stairs"]


def self_check(town):
    """Assert the diagram covers the graph, and print the stair data table."""
    log("=" * 74)
    n_lm = len(town.get("landmarks", []))
    n_edge = len(town.get("edges", []))

    built_lm = {r[0] for r in REPORT["landmarks"]}
    missing_lm = [lm["id"] for lm in town.get("landmarks", []) if lm["id"] not in built_lm]
    log("landmarks: %d in graph, %d markers built" % (n_lm, len(REPORT["landmarks"])))
    log("edges:     %d in graph, %d lines built" % (n_edge, len(REPORT["edges"])))
    log("parcels:   %d wire boxes + %d cameras" % (len(REPORT["parcels"]), len(REPORT["parcels"])))

    for lid, _kind, obj_name in REPORT["landmarks"]:
        assert bpy.data.objects.get(obj_name) is not None, "missing marker " + obj_name
        assert bpy.data.objects.get("label_" + lid) is not None, "missing label for " + lid
        assert bpy.data.objects.get("labelplan_" + lid) is not None, "missing plan label " + lid
    assert not missing_lm, "landmarks with no marker: %s" % missing_lm

    for _name, _etype, obj_name in REPORT["edges"]:
        assert bpy.data.objects.get(obj_name) is not None, "missing line " + obj_name

    # every marker must be the same shape: identical vertex count, all kinds
    vcounts = {bpy.data.objects["massing_" + lid].data.vertices.__len__()
               for lid, _k, _o in REPORT["landmarks"]}
    assert len(vcounts) == 1, \
        "markers are not uniform across kinds (vertex counts: %s)" % sorted(vcounts)
    log("marker uniformity: OK (every landmark marker has %d verts, all kinds)"
        % list(vcounts)[0])

    log("- stairs DATA check (geometry-free) -")
    log("  %-46s %6s %7s %6s %7s %6s  %s"
        % ("edge", "rise", "run", "treads", "per", "slope", "verdict"))
    worst = 0.0
    suspects = []
    for s in REPORT["stairs"]:
        verdict = "OK"
        if s["flat"]:
            verdict = "SUSPECT: zero rise for a stairs edge"
        elif s["suspect"]:
            verdict = "SUSPECT: run < rise (steeper than 45 deg)"
            suspects.append(s["edge"])
        worst = max(worst, s["per"])
        log("  %-46s %6.2f %7.2f %6d %7.3f %5.1fd  %s"
            % (s["edge"], s["rise"], s["run"], s["treads"], s["per"],
               s["slope_deg"], verdict))
        assert s["per"] <= MAX_TREAD_RISE + 1e-9, \
            "%s: implied tread rise %.3f exceeds %.2f" % (s["edge"], s["per"], MAX_TREAD_RISE)
    log("  worst implied tread rise: %.3f (hard limit %.2f)" % (worst, MAX_TREAD_RISE))
    log("  suspect flights: %s" % (", ".join(suspects) if suspects else "none"))

    if REPORT["warnings"]:
        log("- warnings -")
        for w in REPORT["warnings"]:
            log("   " + w)
    else:
        log("no warnings: every edge produced a line")

    assert len(REPORT["edges"]) + len(REPORT["warnings"]) == n_edge, \
        "edge accounting mismatch: %d built + %d skipped != %d" % (
            len(REPORT["edges"]), len(REPORT["warnings"]), n_edge)
    log("=" * 74)


# =================================================================== rendering

def _set_label_mode(mode):
    """
    Labels exist twice per landmark because no single orientation reads in both
    a top-down plan and an elevation. Show whichever set faces the camera.
        mode "plan"  -> flat labels only
        mode "upright" -> upright labels only
    """
    for obj in bpy.data.objects:
        if obj.name.startswith("labelplan_"):
            obj.hide_render = (mode != "plan")
        elif obj.name.startswith("label_"):
            obj.hide_render = (mode != "upright")


def _highlight_parcel(parcel_id):
    """
    Recolour one parcel's wire cage so a per-parcel render says which box it is
    about. Neighbouring parcels stay visible on purpose: the overlaps and the
    seams between scenes are exactly what a planning render needs to show.
    Returns a restore callable.
    """
    obj = bpy.data.objects.get("parcel_" + parcel_id) if parcel_id else None
    active = bpy.data.materials.get("mat_parcel_wire_active")
    if obj is None or active is None or not obj.data.materials:
        return lambda: None
    previous = obj.data.materials[0]
    obj.data.materials[0] = active
    def restore():
        obj.data.materials[0] = previous
    return restore


def _render_to(cam_name, out_path, res, highlight=None, labels="upright"):
    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        log("MISSING CAMERA:", cam_name)
        return False
    _set_label_mode(labels)
    restore = _highlight_parcel(highlight)
    scene.camera = cam
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.resolution_percentage = 100
    scene.render.filepath = out_path
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        restore()
    ok = os.path.exists(out_path)
    log("rendered", os.path.basename(out_path), "->", "OK" if ok else "FAILED")
    return ok


def render_all(map_path=None, qa_dir=None):
    """Two town overviews plus one render per parcel camera."""
    town = load_map(map_path or MAP_PATH)
    out_dir = qa_dir or QA_DIR
    os.makedirs(out_dir, exist_ok=True)
    results = [
        _render_to("cam_overview_elevation",
                   os.path.join(out_dir, "overview-elevation.png"),
                   RES_OVERVIEW, labels="upright"),
        _render_to("cam_overview_plan",
                   os.path.join(out_dir, "overview-plan.png"),
                   RES_OVERVIEW, labels="plan"),
    ]
    results += render_parcels(map_path, qa_dir)
    log("renders: %d/%d written to %s" % (sum(1 for r in results if r), len(results), out_dir))
    assert all(results), "some renders failed"
    return results


def render_parcels(map_path=None, qa_dir=None, only=None):
    """Render parcel cameras (subset via `only`, to stay inside RPC timeouts)."""
    town = load_map(map_path or MAP_PATH)
    out_dir = qa_dir or QA_DIR
    os.makedirs(out_dir, exist_ok=True)
    done = []
    for p in town.get("parcels", []):
        if only and p["id"] not in only:
            continue
        done.append(_render_to("cam_" + p["id"],
                               os.path.join(out_dir, "parcel-%s.png" % p["id"]),
                               RES_PARCEL, highlight=p["id"], labels="upright"))
    return done


def save_blend(path=None):
    out = path or BLEND_PATH
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    log("saved blend ->", out)
    return out


def main():
    build_scene()
    save_blend()
    render_all()
    log("done.")


if __name__ == "__main__":
    main()
