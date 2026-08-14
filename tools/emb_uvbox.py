"""emb_uvbox.py — BAKE EMBERBROOK'S TRI-PLANAR PROJECTION INTO A UV LAYER, SO THE
EXPORTER CAN SAY WHAT CYCLES WAS ALREADY DRAWING.

    Blender -b tools/blends/emberbrook-realtime.blend --python-exit-code 1 \
        -P tools/emb_uvbox.py -- --census
    Blender -b tools/blends/emberbrook-realtime.blend --python-exit-code 1 \
        -P tools/emb_uvbox.py -- --apply --save

============================== WHY THIS EXISTS ==============================

`rt_visual_gate` measured it on 2026-08-12 and it is the largest visual defect in
the shipped walkable town: 3,918 of 8,366 drawn `emb-townwalk` meshes wear a
material that samples a TEXTURE while their geometry carries NO UV ATTRIBUTE, so
three.js samples `uv` as (0,0) and paints ONE TEXEL over the whole surface.
Hiding exactly that set moves 93.2% of the homerow frame.

THE CAUSE IS NOT A BUG IN ANYBODY'S EXPORTER.  Every Emberbrook Image Texture is
driven `Geometry>Position -> Mapping -> Image Texture(projection=BOX)` — world-space
tri-planar.  Cycles evaluates that per shading point, which is why every shipped
PLATE is correct.  glTF has no way to express it: a glTF material samples a
TEXCOORD attribute and nothing else.  The plate tier and the walkable tier were
drawn by two different projections and only one of them survives an export.

WHAT THIS DOES, AND THE ONE THING IT DELIBERATELY DOES NOT DO.  It writes a UV
layer holding the box projection's own answer, per face corner.  IT DOES NOT TOUCH
A SINGLE MATERIAL.  Cycles keeps reading `Geometry>Position` and is bit-identical;
the glTF exporter, which has no UVMap node to follow, falls through to TEXCOORD_0
and now finds one.  ONE ARTIFACT GAINS A FIX AND THE OTHER CANNOT MOVE, because the
renderer that makes the plates never reads the attribute this writes.

  AND THE PLATES ARE SAFER STILL: `emb_dress` writes two tiers to two files.
  Plates bake from `emberbrook-dressed.blend`; the walkable bundle exports from
  `emberbrook-realtime.blend`.  This runs on the realtime blend only.

===================== THE CONVENTION IS MEASURED, NOT RECALLED =====================

`--selftest` replays the calibration this was derived from (tools/../docs/qa/rtvis/
uvbox-cal.json): a uv-encoding image (R=u, G=v) sampled through the real node chain
at `projection=BOX`, photographed by an orthographic camera so every pixel's world
position is known.  72 of 72 samples fit ONE formula, and it carries a trap:

  THE AXIS IS CHOSEN FROM THE OBJECT-SPACE NORMAL.  THE COORDINATE IS THE
  WORLD-SPACE POSITION.

That asymmetry was proved by a control — one quad, IDENTICAL world pose, the object
rotated 90 degrees about X with the mesh counter-rotated — whose sampled axis moved
from Z to Y.  It is not a detail here: 2,445 of the 3,918 targets share ONE mesh
datablock (`dt_cube`) instanced at arbitrary rotations, so an implementation that
picked the axis from the WORLD normal would be wrong on most of the town and would
still produce a UV layer that passes every count-based gate.

  co = A . p_world + t      (the node chain, evaluated as an affine map)
  a  = argmax |n_object|
  |N.x| : u = (N.x<0) ? 1-co.y : co.y ,  v = co.z
  |N.y| : u = (N.y>0) ? 1-co.x : co.x ,  v = co.z
  |N.z| : u = (N.z>0) ? 1-co.y : co.y ,  v = co.x
  FLAT  : u = co.x , v = co.y

=========================== WHAT IT CANNOT REPRODUCE ===========================

`projection_blend = 0.3` on every BOX material.  Cycles blends up to three
projections where a normal sits near an axis boundary; ONE UV set is one projection
and cannot. THE COST IS BOUNDED AND MEASURED, not assumed: `--census` reports the
share of target area whose face normal is within the blend band.  A face whose
normal lies ON an axis — which is what a town of boxes, shingles and planks mostly
is — takes weight 1 on that axis and is reproduced EXACTLY.

Two further residuals, both printed by `--census` rather than hidden:
  * a material whose textures do not share ONE transform cannot be served by one UV
    layer.  `emb_dress_ground` is the only one (3 textures, 2 scales); the dominant
    transform wins and the odd map tiles at a measured ratio.
  * SMOOTH-shaded faces: Cycles picks the axis per shading point from the
    interpolated normal, this picks it per FACE.  Reported as an area share.

MESH SHARING IS THE STRUCTURAL COST.  A UV layer lives on the MESH; a world-space
projection is a function of the OBJECT's transform.  Any datablock with more than
one user among the targets must therefore be made single-user, and `--census`
prints the bill before `--apply` pays it.
"""
import bpy, bmesh, json, math, os, sys, collections
from mathutils import Vector, Matrix

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def has(flag):
    return flag in argv


def opt(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


UVNAME = "uv_box"
BLEND_BAND_DEG = None  # derived from projection_blend per material


# --------------------------------------------------------------------------
# the node chain, evaluated as an affine map  co = A . p + t
# --------------------------------------------------------------------------
class Unsupported(Exception):
    pass


# Cycles' Object Info > Random, MEASURED not recalled: 24 of 24 real town object
# names fitted exactly by rendering ObjectInfo.Random through an Emission shader
# (tools/../docs/qa/rtvis/uvbox-cal.json, `random`).  It is
# hash_uint2(hash_string(name), 0) / 0xFFFFFFFF with Cycles' own two hashes.
_M32 = 0xFFFFFFFF


def _rot(x, k):
    return ((x << k) | (x >> (32 - k))) & _M32


def _final(a, b, c):
    c ^= b; c = (c - _rot(b, 14)) & _M32
    a ^= c; a = (a - _rot(c, 11)) & _M32
    b ^= a; b = (b - _rot(a, 25)) & _M32
    c ^= b; c = (c - _rot(b, 16)) & _M32
    a ^= c; a = (a - _rot(c, 4)) & _M32
    b ^= a; b = (b - _rot(a, 14)) & _M32
    c ^= b; c = (c - _rot(b, 24)) & _M32
    return c


def _hash_uint2(kx, ky):
    a = b = c = (0xdeadbeef + (2 << 2) + 13) & _M32
    b = (b + ky) & _M32
    a = (a + kx) & _M32
    return _final(a, b, c)


def _hash_string(s):
    i = 0
    for ch in s.encode():
        i = (i * 37 + ch) & _M32
    return i


def object_random(name):
    return _hash_uint2(_hash_string(name), 0) / float(_M32)


def const_of(socket, ob):
    """Evaluate a socket that must be a per-object CONSTANT vector."""
    if not socket.links:
        v = socket.default_value
        try:
            return Vector((v[0], v[1], v[2]))
        except TypeError:
            return Vector((v, v, v))
    n = socket.links[0].from_node
    sock = socket.links[0].from_socket.name
    if n.type == 'OBJECT_INFO':
        if sock == 'Location':
            return Vector(ob.matrix_world.translation)
        if sock == 'Random':
            r = object_random(ob.name)
            return Vector((r, r, r))
        raise Unsupported("OBJECT_INFO output %s" % sock)
    if n.type == 'VALUE':
        v = n.outputs[0].default_value
        return Vector((v, v, v))
    if n.type == 'RGB':
        v = n.outputs[0].default_value
        return Vector((v[0], v[1], v[2]))
    if n.type == 'COMBXYZ':
        return Vector((const_of(n.inputs[0], ob).x, const_of(n.inputs[1], ob).x,
                       const_of(n.inputs[2], ob).x))
    if n.type == 'VECT_MATH':
        a = const_of(n.inputs[0], ob)
        b = const_of(n.inputs[1], ob)
        if n.operation == 'ADD':
            return a + b
        if n.operation == 'SUBTRACT':
            return a - b
        if n.operation == 'MULTIPLY':
            return Vector((a.x * b.x, a.y * b.y, a.z * b.z))
        if n.operation == 'SCALE':
            return a * const_of(n.inputs['Scale'], ob).x
        raise Unsupported("VECT_MATH %s (const)" % n.operation)
    if n.type == 'MAPPING':
        A, t = Matrix.Identity(3), const_of(n.inputs['Vector'], ob)
        return mapping_apply(n, ob, A, t)[1]
    if n.type == 'REROUTE':
        return const_of(n.inputs[0], ob)
    raise Unsupported("const node %s" % n.type)


def mapping_apply(n, ob, A, t):
    """Blender Mapping (POINT): out = R . (v * S) + L."""
    from mathutils import Euler
    if n.vector_type != 'POINT':
        raise Unsupported("Mapping vector_type %s" % n.vector_type)
    S = const_of(n.inputs['Scale'], ob)
    L = const_of(n.inputs['Location'], ob)
    R = const_of(n.inputs['Rotation'], ob)
    M = Matrix.Diagonal(S).to_3x3()
    if R.length > 1e-12:
        M = Euler((R.x, R.y, R.z), 'XYZ').to_matrix() @ M
    return M @ A, M @ t + L


def affine_of(tex_node, ob):
    """Walk back from an Image Texture's Vector input, returning (A, t) with
    co = A . p_world + t.  Hard-fails on anything it does not understand."""
    vec = tex_node.inputs["Vector"]
    if not vec.links:
        raise Unsupported("unlinked Vector (already reads the active uv layer)")
    A, t = Matrix.Identity(3), Vector((0, 0, 0))
    stack = []
    n = vec.links[0].from_node
    sock = vec.links[0].from_socket.name
    guard = 0
    while guard < 24:
        guard += 1
        if n.type == 'NEW_GEOMETRY':
            if sock != 'Position':
                raise Unsupported("Geometry output %s" % sock)
            break
        if n.type == 'TEX_COORD':
            if sock == 'Object':
                # object-space coords: p_object = M^-1 . p_world
                stack.append(('objspace', None))
                break
            raise Unsupported("TexCoord output %s" % sock)
        if n.type == 'REROUTE':
            nx = n.inputs[0]
        elif n.type == 'MAPPING':
            stack.append(('mapping', n))
            nx = n.inputs['Vector']
        elif n.type == 'VECT_MATH':
            stack.append(('vmath', n))
            nx = n.inputs[0]
        else:
            raise Unsupported("node %s" % n.type)
        if not nx.links:
            raise Unsupported("chain ends at an unlinked %s input" % n.type)
        sock = nx.links[0].from_socket.name
        n = nx.links[0].from_node
    else:
        raise Unsupported("chain deeper than 24 nodes")

    for kind, node in reversed(stack):
        if kind == 'objspace':
            Mi = ob.matrix_world.inverted().to_3x3()
            A = Mi @ A
            t = Mi @ t + ob.matrix_world.inverted().translation
        elif kind == 'mapping':
            A, t = mapping_apply(node, ob, A, t)
        elif kind == 'vmath':
            b = const_of(node.inputs[1], ob)
            op = node.operation
            if op == 'ADD':
                t = t + b
            elif op == 'SUBTRACT':
                t = t - b
            elif op == 'MULTIPLY':
                D = Matrix.Diagonal(b)
                A, t = D @ A, D @ t
            elif op == 'SCALE':
                s = const_of(node.inputs['Scale'], ob).x
                A, t = A * s, t * s
            else:
                raise Unsupported("VECT_MATH %s" % op)
    return A, t


def mat_recipe(mat):
    """One (proj, blend, tex_node) recipe per material, asserting the textures
    agree on their drive.  Returns None for a material with no image texture."""
    if not mat or not mat.node_tree:
        return None
    texs = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    if not texs:
        return None
    return texs


# --------------------------------------------------------------------------
# the measured box convention
# --------------------------------------------------------------------------
def box_uv(co, n_obj):
    ax = max(range(3), key=lambda i: abs(n_obj[i]))
    if ax == 0:
        return ((1.0 - co.y) if n_obj.x < 0 else co.y, co.z)
    if ax == 1:
        return ((1.0 - co.x) if n_obj.y > 0 else co.x, co.z)
    return ((1.0 - co.y) if n_obj.z > 0 else co.y, co.x)


def flat_uv(co, n_obj):
    return (co.x, co.y)


# --------------------------------------------------------------------------
def textured(o):
    for s in o.material_slots:
        if mat_recipe(s.material):
            return True
    return False


def targets():
    return [o for o in bpy.data.objects
            if o.type == 'MESH' and len(o.data.uv_layers) == 0 and textured(o)]


def run():
    bpy.context.view_layer.update()
    tg = targets()
    by_me = collections.defaultdict(list)
    for o in tg:
        by_me[o.data.name].append(o)
    shared = {k: v for k, v in by_me.items() if len(v) > 1}

    rep = {
        "blend": bpy.data.filepath,
        "targets": len(tg),
        "datablocks": len(by_me),
        "shared_datablocks": len(shared),
        "objs_on_shared": sum(len(v) for v in shared.values()),
        "shared_detail": [{"mesh": k, "users": len(v), "polys": len(bpy.data.meshes[k].polygons)}
                          for k, v in sorted(shared.items(), key=lambda kv: -len(kv[1]))[:10]],
    }

    # ---- resolve every material's chain once, on a representative object -----
    # The affine map is a function of the OBJECT (object_random, object location),
    # so the map is re-derived per object at bake time; what is decided here, ONCE
    # and object-independently, is WHICH texture node's transform the single uv
    # layer serves when a material's textures disagree.
    mats = {}
    fails = {}
    global MATREP
    MATREP = {}
    for o in tg:
        for s in o.material_slots:
            m = s.material
            if not m or m.name in mats or m.name in fails:
                continue
            texs = mat_recipe(m)
            if not texs:
                continue
            try:
                maps = []
                for tnode in texs:
                    A, t = affine_of(tnode, o)
                    maps.append((tuple(round(x, 8) for r in A for x in r),
                                 tnode.projection, round(tnode.projection_blend, 6)))
                votes = collections.Counter(maps)
                win, nwin = votes.most_common(1)[0]
                # deterministic: first node carrying the winning transform
                rep_i = next(i for i, k in enumerate(maps) if k == win)
                MATREP[m.name] = rep_i
                mats[m.name] = {
                    "ntex": len(texs),
                    "distinct": len(votes),
                    "served": nwin,
                    "rep_img": texs[rep_i].image.name,
                    "unserved": [texs[i].image.name for i, k in enumerate(maps) if k != win],
                    "proj": sorted(set(c for _, c, _ in maps)),
                    "blend": sorted(set(d for _, _, d in maps)),
                }
            except Unsupported as e:
                fails[m.name] = str(e)
    rep["materials"] = mats
    rep["unsupported"] = fails

    # ---- area census -------------------------------------------------------
    # NO GUESSED THRESHOLD.  `projection_blend` softens the axis pick over a band
    # whose exact width is Cycles' business; what is reported here is the
    # ASSUMPTION-FREE quantity that bounds it — the share of target area whose face
    # normal is more than X degrees off its nearest axis.  A face ON an axis takes
    # weight 1 on that axis and this bake reproduces Cycles EXACTLY there, whatever
    # the blend is set to.
    smooth = total = multi = 0.0
    offax = collections.OrderedDict((d, 0.0) for d in (1, 5, 15, 30))
    for o in tg:
        me = o.data
        M = o.matrix_world
        sl = [s.material.name if s.material else None for s in o.material_slots]
        sc = M.to_scale()
        wa = abs(sc.x * sc.y)
        for p in me.polygons:
            a = p.area * wa
            total += a
            mn = sl[p.material_index] if p.material_index < len(sl) else None
            info = mats.get(mn)
            if not info:
                continue
            if info["distinct"] > 1:
                multi += a
            if p.use_smooth:
                smooth += a
            if 'BOX' in info["proj"]:
                n = p.normal
                hi = max(abs(n.x), abs(n.y), abs(n.z))
                ln = n.length
                if ln > 1e-9:
                    ang = math.degrees(math.acos(min(1.0, hi / ln)))
                    for d in offax:
                        if ang > d:
                            offax[d] += a
    rep["area"] = {
        "total": round(total, 3),
        "smooth_pct": round(100.0 * smooth / total, 4) if total else 0.0,
        "multi_transform_pct": round(100.0 * multi / total, 4) if total else 0.0,
        "off_axis_pct": {("gt%ddeg" % d): (round(100.0 * v / total, 4) if total else 0.0)
                         for d, v in offax.items()},
    }

    if has("--census"):
        print(json.dumps(rep, indent=1))
        out = opt("--report")
        if out:
            open(out, "w").write(json.dumps(rep, indent=1))
        print("CENSUS targets %d  unsupported-materials %d  off-axis>5deg %.3f%%  smooth %.3f%%"
              % (len(tg), len(fails), rep["area"]["off_axis_pct"]["gt5deg"],
                 rep["area"]["smooth_pct"]))
        return rep

    # ------------------------------ APPLY ------------------------------------
    if fails:
        raise SystemExit("REFUSING: %d material(s) whose drive is not affine: %s"
                         % (len(fails), fails))

    # 1. unshare — a world-space projection is a function of the OBJECT transform
    unshared = 0
    for k, v in shared.items():
        for o in v:
            o.data = o.data.copy()
            unshared += 1
    bpy.context.view_layer.update()

    # 2. write the layer
    done = 0
    loops = 0
    for o in tg:
        me = o.data
        M = o.matrix_world
        sl = [s.material for s in o.material_slots]
        cache = {}
        for i, m in enumerate(sl):
            if m and mat_recipe(m):
                texs = mat_recipe(m)
                tn = texs[MATREP.get(m.name, 0)]
                A, t = affine_of(tn, o)
                cache[i] = (A, t, tn.projection)
        if not cache:
            continue
        uv = me.uv_layers.new(name=UVNAME, do_init=False)
        data = uv.data
        co_cache = [M @ v.co for v in me.vertices]
        for p in me.polygons:
            ent = cache.get(p.material_index)
            if ent is None:
                for li in p.loop_indices:
                    data[li].uv = (0.0, 0.0)
                continue
            A, t, proj = ent
            n = p.normal
            f = box_uv if proj == 'BOX' else flat_uv
            for li in p.loop_indices:
                vi = me.loops[li].vertex_index
                co = A @ co_cache[vi] + t
                data[li].uv = f(co, n)
                loops += 1
        uv.active = True
        uv.active_render = True
        done += 1

    rep["applied"] = {"objects": done, "loops": loops, "unshared": unshared}
    print("APPLIED uv=%s objects=%d loops=%d unshared=%d" % (UVNAME, done, loops, unshared))

    if has("--save"):
        path = opt("--out", bpy.data.filepath)
        bpy.ops.wm.save_as_mainfile(filepath=path)
        print("SAVED", path, os.path.getsize(path))
    out = opt("--report")
    if out:
        open(out, "w").write(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    run()
