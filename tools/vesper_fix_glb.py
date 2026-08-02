#!/usr/bin/env python3
"""
Repair the Tripo-exported vesper.glb skin.

THE BUG (found 2026-07-30): Tripo wrote every joint node with NO transform at all
(no matrix, no TRS -> identity), so the joint hierarchy carries none of the rig.
The entire skeleton is encoded only in skin.inverseBindMatrices, and those are in a
DIFFERENT coordinate frame than the mesh: IBM^-1 translations are Z-up
(head at z=0.794, hands at y=+-0.19) while mesh POSITION is Y-up
(y 0..0.9785, hands at x=+-0.21). glTF skinning gives
skinMatrix = jointGlobal @ IBM = I @ IBM = IBM != I, so the mesh renders shredded in
ANY conformant viewer (three.js included) and Blender imports a rest pose that does
not match the geometry.

THE FIX: the two frames are related by the exact axis permutation P:(x,y,z)->(y,z,x)
(verified against skin-weight centroids: every joint lands anatomically after P, rms
3% of body height) plus a uniform 1.022 scale baked into the IBMs. So we rebuild each
joint's global bind transform as

    G_j = P @ normalize3x3(IBM_j^-1)          (rigid: rotation + P-mapped translation)

write it into the node hierarchy as a local matrix (inv(G_parent) @ G_j), and rewrite
inverseBindMatrices as inv(G_j). Then jointGlobal @ IBM = I at rest: the mesh is
undeformed, the joints sit anatomically inside it, and the file is valid glTF.

Mesh data, weights, materials and textures are untouched.
"""
import struct, json, sys
import numpy as np

# GENERALISED 2026-08-02.  This was written for vesper.glb with both paths hardcoded,
# and then Lake's delivery arrived with the SAME defect (max |jointGlobal @ IBM - I|
# = 1.970, worst joint L_Hand, against Vesper's 1.95) — the repair is per-EXPORTER,
# not per-character, because it undoes a Tripo behaviour: 0 of N joint nodes carrying
# a transform, so the whole rig lives in the IBMs in a permuted frame.  Two positional
# args now, with the old vesper defaults kept so any existing caller is unaffected.
#     python3 tools/vesper_fix_glb.py <src.glb> <dst.glb>
_V = "/Users/junshernchan/projects/multiplayer-rpg/public/assets/characters/vesper/vesper.glb"
_a = [x for x in sys.argv[1:] if not x.startswith('-')]
if len(_a) >= 2:
    SRC, DST = _a[0], _a[1]
elif len(_a) == 1:
    SRC, DST = _V, _a[0]            # legacy form: one arg was the DESTINATION
else:
    SRC, DST = _V, "/tmp/vesper-fixed.glb"

# axis permutation taking the IBM (bind) frame -> the mesh frame: (x,y,z) -> (y,z,x)
P = np.array([[0., 1., 0.],
              [0., 0., 1.],
              [1., 0., 0.]])
assert abs(np.linalg.det(P) - 1.0) < 1e-9, "P must be a proper rotation"


def read_glb(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'glTF'
    off, chunks = 12, []
    while off < len(d):
        ln, ty = struct.unpack_from('<II', d, off); off += 8
        chunks.append([ty, bytearray(d[off:off + ln])]); off += ln
    js = json.loads(chunks[0][1].decode('utf-8'))
    return js, chunks


def write_glb(path, js, chunks):
    jb = json.dumps(js, separators=(',', ':')).encode('utf-8')
    jb += b' ' * ((4 - len(jb) % 4) % 4)
    out = [(0x4E4F534A, jb)]
    for ty, data in chunks[1:]:
        data = bytes(data)
        data += b'\0' * ((4 - len(data) % 4) % 4)
        out.append((ty, data))
    total = 12 + sum(8 + len(d) for _, d in out)
    with open(path, 'wb') as f:
        f.write(b'glTF' + struct.pack('<II', 2, total))
        for ty, d in out:
            f.write(struct.pack('<II', len(d), ty)); f.write(d)


js, chunks = read_glb(SRC)
BIN = chunks[1][1]
nodes = js['nodes']
skin = js['skins'][0]
joints = skin['joints']

acc = js['accessors'][skin['inverseBindMatrices']]
bv = js['bufferViews'][acc['bufferView']]
base = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
stride = bv.get('byteStride') or 64
assert acc['type'] == 'MAT4' and acc['componentType'] == 5126
assert acc['count'] == len(joints)

# --- read IBMs, build corrected global bind transforms ---
ibm = []
for k in range(acc['count']):
    v = struct.unpack_from('<16f', BIN, base + k * stride)
    ibm.append(np.array(v, dtype=np.float64).reshape(4, 4).T)  # glTF is column-major

G = {}
scales = []
for jidx, M in zip(joints, ibm):
    Mi = np.linalg.inv(M)                       # joint bind transform, bind frame
    R3 = Mi[:3, :3]
    s = np.linalg.norm(R3[:, 0])
    scales.append(s)
    Rn = R3 / s                                 # drop the uniform 1.022 bake
    assert np.allclose(Rn @ Rn.T, np.eye(3), atol=1e-4), "IBM 3x3 not a scaled rotation"
    g = np.eye(4)
    g[:3, :3] = P @ Rn
    g[:3, 3] = P @ Mi[:3, 3]
    G[jidx] = g
print("IBM uniform scale: min %.5f max %.5f" % (min(scales), max(scales)))

# --- parent map over the whole node graph ---
parent = {}
for i, n in enumerate(nodes):
    for c in n.get('children', []):
        parent[c] = i

# --- write node local matrices for joints ---
for jidx in joints:
    p = parent.get(jidx)
    gp = G.get(p, np.eye(4)) if p is not None else np.eye(4)
    L = np.linalg.inv(gp) @ G[jidx]
    n = nodes[jidx]
    for k in ('translation', 'rotation', 'scale'):
        n.pop(k, None)
    n['matrix'] = [float(x) for x in L.T.reshape(16)]   # column-major

# --- rewrite inverse bind matrices ---
for k, jidx in enumerate(joints):
    inv = np.linalg.inv(G[jidx])
    struct.pack_into('<16f', BIN, base + k * stride, *[float(x) for x in inv.T.reshape(16)])

# --- sanity: reconstruct globals from the node graph, verify skinMatrix == I ---
def global_of(i):
    n = nodes[i]
    m = np.array(n['matrix'], dtype=np.float64).reshape(4, 4).T if 'matrix' in n else np.eye(4)
    p = parent.get(i)
    return (global_of(p) @ m) if p is not None else m

worst = 0.0
for k, jidx in enumerate(joints):
    newibm = np.array(struct.unpack_from('<16f', BIN, base + k * stride),
                      dtype=np.float64).reshape(4, 4).T
    worst = max(worst, np.abs(global_of(jidx) @ newibm - np.eye(4)).max())
print("max |jointGlobal @ IBM - I| = %.2e  (must be ~0)" % worst)
assert worst < 1e-4

js['asset']['generator'] = 'Tripo (skin repaired by tools/vesper_fix_glb.py)'
write_glb(DST, js, chunks)
print("wrote", DST)

# report where a few joints landed, in mesh space
prim = js['meshes'][0]['primitives'][0]
pa = js['accessors'][prim['attributes']['POSITION']]
print("mesh POSITION min", [round(v, 4) for v in pa['min']], "max", [round(v, 4) for v in pa['max']])
byname = {nodes[i].get('name'): i for i in joints}
for nm in ('Root', 'Hip', 'Spine02', 'Head', 'L_Hand', 'R_Hand', 'L_Thigh', 'L_Foot', 'L_ToeBase'):
    t = G[byname[nm]][:3, 3]
    print("  %-10s bind pos in mesh space = (%7.4f,%7.4f,%7.4f)" % (nm, *t))
