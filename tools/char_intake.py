#!/usr/bin/env python3
"""THE INTAKE GATE for a Tripo (or any glTF) character delivery — byte level, no Blender.

    python3 tools/char_intake.py <file.glb> [--garment] [--thick 0.020]

CLAUDE.md's character factory puts an intake gate at step 4: "joint x IBM ~= I probe;
repair via tools/vesper_fix_glb.py if broken". This is that probe, and it exists as its
own tool because the two instruments we already had BOTH pass a file whose rig is dead:

  * tools/char_inspect.py goes through Blender's glTF importer, which imported the
    lake delivery without an error and reported a clean "41 bones" — while every bone
    head in the resulting armature was NaN (measured 2026-08-02).
  * tools/vesper_fix_glb.py is the REPAIR for one known break (Tripo writing identity
    joint nodes so the rig lives only in the inverse bind matrices). It is hard-coded to
    vesper.glb and it assumes the IBMs are intact — which is the thing to check first.

WHAT IT MEASURES

1. FILE INTEGRITY, before any glTF semantics. Declared vs actual length, chunk layout,
   bufferView coverage of the BIN chunk, and whether the tail of the file repeats its
   own head — the signature of a chunked/resumed download writing a retry at the wrong
   offset. That is exactly how the lake delivery arrived: correct total length, correct
   JSON, and the final 2,624 bytes (which were the whole inverseBindMatrices bufferView,
   the LAST thing in the buffer) replaced by a byte-identical copy of the file's first
   2,624 bytes. Mesh, weights and textures were untouched; the skeleton was gone.

2. THE BIND GATE:  max | jointGlobal @ IBM - I |  over every joint. Calibrated on this
   repo's own deliveries (2026-08-02):

       finn.glb    1.9e-06   PASS, shipped
       maren.glb   1.3e-06   PASS, shipped
       vesper.glb  1.95      FAIL — the known Tripo axis-permutation break, and the
                             magnitude to expect from it; repairable by vesper_fix_glb
       lake.glb    1.8e+37   FAIL — garbage, i.e. not a rig at all. A number this size
                             is a CORRUPT FILE, not a fixable export.

   So read the magnitude, not just the verdict: O(1) is a wrong frame and repairable;
   O(1e30) means the bytes are not matrices and the only fix is a fresh download.

3. Whether the joint nodes carry any transform. Healthy Tripo deliveries write TRS on
   every joint (finn 41/43, maren 41/43). When they do not (vesper, lake), the ENTIRE
   rig is encoded in the IBMs — which makes a damaged IBM block unrecoverable, and is
   why that fact is printed next to the gate.

4. --garment: WHERE A CLOAK/COAT/SKIRT IS SKINNED. Tripo's auto-rigger binds by
   proximity, so a garment that hangs away from the body gets bound to whatever limb
   is nearest — which smears it through a walk cycle. The garment is found without any
   rig, by LOCAL SHEET THICKNESS (a cloak is a thin flange of the shell, a limb is a
   thick tube), then region-grown over mesh adjacency so the cloak comes out as one
   region and fingers/hair come out as their own. Each region reports the share of its
   skin weight held by ARM / LEG / TORSO / HEAD bones.

   Calibrated, same day: the shipped bodies' largest sheet region is 1.6k verts and is
   a collar or a hair shell. Lake's two largest were 7.7k and 6.8k verts running from
   8% to 72% of body height — his cloak — at 86% and 67% ARM-weighted, with a fifth of
   the second one on the calf twists. THE INSTRUMENT IS A SCREEN, NOT A VERDICT: it
   segments by thickness, so anything thin (fingers, hair, a hood brim) also lands in
   the sheet set. Read the REGIONS, which is what separates them, and confirm a
   suspicious region by eye before acting on it.
"""
import struct, json, sys
import numpy as np

CT = {5120: 'i1', 5121: 'u1', 5122: 'i2', 5123: 'u2', 5125: 'u4', 5126: 'f4'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'glTF', 'not a GLB: %s' % path
    declared = struct.unpack_from('<I', d, 8)[0]
    off, chunks = 12, []
    while off < len(d):
        ln, ty = struct.unpack_from('<II', d, off)
        off += 8
        chunks.append((ty, off, ln))
        off += ln
    js = json.loads(d[chunks[0][1]:chunks[0][1] + chunks[0][2]].decode('utf-8'))
    bin_off, bin_len = (chunks[1][1], chunks[1][2]) if len(chunks) > 1 else (0, 0)
    return d, js, declared, chunks, bin_off, bin_len


def acc(js, BIN, ai):
    a = js['accessors'][ai]
    dt = np.dtype('<' + CT[a['componentType']])
    nc = NC[a['type']]
    bv = js['bufferViews'][a['bufferView']]
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride') or dt.itemsize * nc
    need = stride * (a['count'] - 1) + dt.itemsize * nc
    raw = np.frombuffer(BIN, dtype=np.uint8, count=need, offset=base)
    if stride == dt.itemsize * nc:
        return raw.view(dt).reshape(a['count'], nc)
    out = np.empty((a['count'], nc), dtype=dt)
    for k in range(a['count']):
        out[k] = np.frombuffer(raw[k * stride:k * stride + dt.itemsize * nc].tobytes(), dtype=dt)
    return out


def node_local(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=np.float64).reshape(4, 4).T
    M = np.eye(4)
    if 'scale' in n:
        M[:3, :3] = M[:3, :3] @ np.diag(n['scale'])
    if 'rotation' in n:
        x, y, z, w = n['rotation']
        M[:3, :3] = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) @ M[:3, :3]
    if 'translation' in n:
        M[:3, 3] = n['translation']
    return M


def grp(nm):
    if any(k in nm for k in ('Clavicle', 'Upperarm', 'Forearm', 'Hand')):
        return 'ARM'
    if any(k in nm for k in ('Thigh', 'Calf', 'Foot', 'ToeBase')):
        return 'LEG'
    if any(k in nm for k in ('Neck', 'Head')):
        return 'HEAD'
    return 'TORSO'


def union_find(n, edges):
    par = np.arange(n)

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b in edges:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            par[rb] = ra
    return np.array([find(i) for i in range(n)])


def main():
    path = sys.argv[1]
    want_garment = '--garment' in sys.argv
    TH = float(sys.argv[sys.argv.index('--thick') + 1]) if '--thick' in sys.argv else 0.020
    d, js, declared, chunks, bin_off, bin_len = read_glb(path)
    BIN = d[bin_off:bin_off + bin_len]
    print("== %s" % path)
    print("generator %s   file %d bytes   declared %d" %
          (js['asset'].get('generator'), len(d), declared))

    # ---- 1. file integrity
    bad = []
    if declared != len(d):
        bad.append("declared length %d != actual %d" % (declared, len(d)))
    if len(d) >= 5200 and d[-2600:] == d[20:20 + 2600]:
        bad.append("THE TAIL OF THE FILE REPEATS ITS OWN HEAD — corrupt/resumed download")
    if len(chunks) > 1:
        cover = 0
        for bv in js.get('bufferViews', []):
            cover = max(cover, bv.get('byteOffset', 0) + bv['byteLength'])
        if cover > bin_len:
            bad.append("bufferViews reach %d, BIN chunk is only %d — TRUNCATED" % (cover, bin_len))
    print("integrity: " + ("OK" if not bad else "FAIL — " + "; ".join(bad)))

    # ---- 2. census
    prim = js['meshes'][0]['primitives'][0]
    P = acc(js, BIN, prim['attributes']['POSITION']).astype(np.float64)
    TRI = acc(js, BIN, prim['indices']).reshape(-1, 3).astype(np.int64)
    print("mesh: %d verts  %d tris  bbox %s..%s  materials %d  images %d  animations %d" %
          (len(P), len(TRI), np.round(P.min(0), 4), np.round(P.max(0), 4),
           len(js.get('materials', [])), len(js.get('images', [])), len(js.get('animations', []))))

    if not js.get('skins'):
        print("NO SKIN — nothing to gate")
        return 1 if bad else 0
    skin = js['skins'][0]
    joints, nodes = skin['joints'], js['nodes']
    JN = [nodes[j].get('name') for j in joints]
    ibm = acc(js, BIN, skin['inverseBindMatrices']).astype(np.float64).reshape(-1, 4, 4).transpose(0, 2, 1)
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            parent[c] = i

    def gof(i):
        m = node_local(nodes[i])
        p = parent.get(i)
        return (gof(p) @ m) if p is not None else m

    with np.errstate(over='ignore', invalid='ignore'):
        errs = np.array([np.abs(gof(j) @ ibm[k] - np.eye(4)).max() for k, j in enumerate(joints)])
    worst = float(np.nanmax(errs))
    posed = sum(1 for j in joints if any(k in nodes[j] for k in
                                         ('matrix', 'translation', 'rotation', 'scale')))
    print("joints %d   joint nodes carrying a transform: %d/%d%s" %
          (len(joints), posed, len(joints),
           "   (rig lives ONLY in the IBMs)" if posed == 0 else ""))
    print("INTAKE GATE  max |jointGlobal @ IBM - I| = %.3e   worst joint %s" %
          (worst, JN[int(np.nanargmax(errs))]))
    ok = worst < 1e-4
    print("VERDICT: " + ("PASS" if ok else
                         "FAIL — %s" % ("CORRUPT (not matrices); re-fetch the delivery"
                                        if worst > 1e6 else
                                        "wrong bind frame; repair (cf. tools/vesper_fix_glb.py)")))

    if want_garment:
        garment(js, BIN, prim, P, TRI, JN, TH)
    return 0 if (ok and not bad) else 1


def garment(js, BIN, prim, P, TRI, JN, TH):
    N = acc(js, BIN, prim['attributes']['NORMAL']).astype(np.float64)
    J = acc(js, BIN, prim['attributes']['JOINTS_0']).astype(np.int32)
    W = acc(js, BIN, prim['attributes']['WEIGHTS_0']).astype(np.float64)
    nv, H = len(P), P[:, 1].max()
    Nn = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)

    # local sheet thickness: distance to the first surface that sits along -normal and
    # faces back at us. A cloak is thin; a limb is not.
    R = 0.05
    mn = P.min(0)
    gi = np.floor((P - mn) / R).astype(np.int64)
    dims = gi.max(0) + 1
    flat = (gi[:, 0] * dims[1] + gi[:, 1]) * dims[2] + gi[:, 2]
    order = np.argsort(flat)
    fs = flat[order]
    uq, first = np.unique(fs, return_index=True)
    starts = {int(u): (first[k], first[k + 1] if k + 1 < len(uq) else len(fs))
              for k, u in enumerate(uq)}
    offs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
    thick = np.full(nv, np.inf)
    for i in range(nv):
        g, best = gi[i], np.inf
        for o in offs:
            se = starts.get(int(((g[0] + o[0]) * dims[1] + (g[1] + o[1])) * dims[2] + g[2] + o[2]))
            if se is None:
                continue
            idx = order[se[0]:se[1]]
            dd = P[idx] - P[i]
            L = np.linalg.norm(dd, axis=1)
            m = (L > 1e-6) & (L < R)
            if not m.any():
                continue
            idx, dd, L = idx[m], dd[m], L[m]
            m2 = ((dd @ (-Nn[i])) / L > 0.80) & (Nn[idx] @ Nn[i] < -0.5)
            if m2.any():
                best = min(best, L[m2].min())
        thick[i] = best
    sheet = np.isfinite(thick) & (thick < TH)
    print("\nGARMENT PROBE  sheet verts (thickness < %.3f): %d / %d (%.1f%%)" %
          (TH, sheet.sum(), nv, 100.0 * sheet.sum() / nv))

    key = np.round(P, 6)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    E = np.concatenate([TRI[:, [0, 1]], TRI[:, [1, 2]], TRI[:, [2, 0]]])
    keep = sheet[E[:, 0]] & sheet[E[:, 1]]
    root = union_find(inv.max() + 1, np.unique(np.sort(inv[E[keep]], axis=1), axis=0))
    lab = np.where(sheet, root[inv], -1)
    labs, cnt = np.unique(lab[lab >= 0], return_counts=True)
    G = np.array([grp(n) for n in JN])
    print("%d sheet regions; the largest are:" % len(labs))
    for oi in np.argsort(-cnt)[:5]:
        m = lab == labs[oi]
        mm = np.zeros(len(JN))
        for c in range(4):
            np.add.at(mm, J[m][:, c], W[m][:, c])
        t = mm.sum()
        b0, b1 = P[m].min(0), P[m].max(0)
        print("  n=%6d  y %3.0f%%..%3.0f%% of height  x[%.3f,%.3f] z[%.3f,%.3f]  "
              "ARM %4.1f%% LEG %4.1f%% TORSO %4.1f%% HEAD %4.1f%%   %s" %
              (m.sum(), 100 * b0[1] / H, 100 * b1[1] / H, b0[0], b1[0], b0[2], b1[2],
               100 * mm[G == 'ARM'].sum() / t, 100 * mm[G == 'LEG'].sum() / t,
               100 * mm[G == 'TORSO'].sum() / t, 100 * mm[G == 'HEAD'].sum() / t,
               ", ".join("%s %.0f%%" % (JN[k], 100 * mm[k] / t) for k in np.argsort(-mm)[:3])))


if __name__ == '__main__':
    sys.exit(main())
