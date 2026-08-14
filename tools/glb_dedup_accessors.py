"""glb_dedup_accessors.py — TWO PRIMITIVES MAY SHARE AN ACCESSOR; BLENDER'S EXPORTER
NEVER LETS THEM.

    python3 tools/glb_dedup_accessors.py <in.glb> [-o <out.glb>] [--dry]

WHY THIS EXISTS.  `emb_uvbox` has to make 2,445 users of one `dt_cube` datablock
single-user, because a world-space projection is a function of the OBJECT transform
and a uv layer lives on the MESH.  Blender then writes 2,445 glTF meshes — and their
POSITION, NORMAL and index data are BYTE-IDENTICAL, because glTF keeps geometry in
mesh-local space and puts the transform on the NODE.  Measured on emb-townwalk: of
the +20.1 MB the unshare cost, only TEXCOORD_0 (+5.89 MB) is new information;
POSITION (+6.32) and NORMAL (+6.32) are the same cube written 2,445 times.

That mattered for a hard reason, not a tidy one: **GitHub refuses a file over 100 MiB
and the bundle went 89.7 -> 109.0 MiB**, so the fix could not be pushed at all.
(The bundle was already within 10 MiB of that wall before this lane touched it — see
the note at the bottom.)

WHAT IT DOES.  Groups accessors by (componentType, type, count, normalized, the SHA-256
of their bytes), points every reference at one representative, drops the bufferViews
that nothing reads any more, and repacks the binary chunk at 4-byte alignment.  Image
bufferViews are carried through untouched.

WHY IT IS SAFE, AND THE PROOF IS NOT AN ARGUMENT.  The gate is a CONTENT IDENTITY
check, not a size check: for every primitive of every mesh, in order, the tool records
`{attribute -> sha256(bytes)}` plus the index hash BEFORE and AFTER and refuses unless
all of them agree.  A dedupe that changed one vertex would fail it.  It also asserts
that nothing outside `meshes` references an accessor (no skins, no animation samplers,
no sparse accessors in this bundle) rather than silently mis-remapping one.

NOT A COMPRESSOR.  It removes DUPLICATION only; it never quantises, never re-encodes an
image and never touches the scene graph.  If a bundle needs to get smaller than its own
unique data, that is a different decision and belongs to the deploy's `--compress`.
"""
import sys, json, struct, hashlib, os, collections

CT = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}


def read_glb(path):
    with open(path, 'rb') as f:
        magic, ver, total = struct.unpack('<4sII', f.read(12))
        assert magic == b'glTF' and ver == 2, (magic, ver)
        doc = None
        bin_ = b''
        while f.tell() < total:
            clen, ctype = struct.unpack('<II', f.read(8))
            data = f.read(clen)
            if ctype == 0x4E4F534A:
                doc = json.loads(data.decode('utf-8'))
            elif ctype == 0x004E4942:
                bin_ = data
    return doc, bin_


def write_glb(path, doc, bin_):
    js = json.dumps(doc, separators=(',', ':')).encode('utf-8')
    js += b' ' * ((4 - len(js) % 4) % 4)
    bn = bin_ + b'\0' * ((4 - len(bin_) % 4) % 4)
    total = 12 + 8 + len(js) + (8 + len(bn) if bn else 0)
    with open(path, 'wb') as f:
        f.write(struct.pack('<4sII', b'glTF', 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        if bn:
            f.write(struct.pack('<II', len(bn), 0x004E4942)); f.write(bn)
    return total


def acc_bytes(doc, bin_, i):
    """The accessor's element bytes, de-strided, in element order."""
    a = doc['accessors'][i]
    if 'sparse' in a:
        raise SystemExit("REFUSING: accessor %d is sparse" % i)
    if 'bufferView' not in a:
        return b''
    bv = doc['bufferViews'][a['bufferView']]
    esz = CT[a['componentType']] * NC[a['type']]
    stride = bv.get('byteStride') or esz
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    if stride == esz:
        return bin_[base:base + esz * a['count']]
    return b''.join(bin_[base + k * stride: base + k * stride + esz]
                    for k in range(a['count']))


def prim_fingerprint(doc, bin_):
    """{attr -> sha256} per primitive, in mesh/primitive order.  THE gate."""
    out = []
    for me in doc.get('meshes', []):
        for p in me.get('primitives', []):
            e = {k: hashlib.sha256(acc_bytes(doc, bin_, v)).hexdigest()
                 for k, v in p.get('attributes', {}).items()}
            if 'indices' in p:
                e['#i'] = hashlib.sha256(acc_bytes(doc, bin_, p['indices'])).hexdigest()
            out.append(e)
    return out


def run(path, out, dry):
    doc, bin_ = read_glb(path)
    before = prim_fingerprint(doc, bin_)

    # nothing outside `meshes` may reference an accessor, or the remap is unsound
    stray = []
    for key in ('skins', 'animations'):
        if doc.get(key):
            stray.append(key)
    if stray:
        raise SystemExit("REFUSING: %s reference accessors; remap not proven sound" % stray)

    # ---- group by content ---------------------------------------------------
    canon = {}
    key_of = {}
    for i, a in enumerate(doc['accessors']):
        k = (a['componentType'], a['type'], a['count'], bool(a.get('normalized')),
             hashlib.sha256(acc_bytes(doc, bin_, i)).hexdigest())
        key_of[i] = k
        canon.setdefault(k, i)
    remap = {i: canon[key_of[i]] for i in range(len(doc['accessors']))}
    dupes = sum(1 for i, j in remap.items() if i != j)

    for me in doc['meshes']:
        for p in me['primitives']:
            p['attributes'] = {k: remap[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = remap[p['indices']]

    # ---- rebuild: keep only accessors and bufferViews still referenced -------
    used_acc = sorted({v for v in remap.values()})
    img_bv = {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im}
    newbin = bytearray()
    new_bv = []
    acc_new = {}

    def push(payload, stride=None):
        while len(newbin) % 4:
            newbin.append(0)
        off = len(newbin)
        newbin.extend(payload)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(payload)}
        if stride:
            bv["byteStride"] = stride
        new_bv.append(bv)
        return len(new_bv) - 1

    bv_img_map = {}
    for i in sorted(img_bv):
        old = doc['bufferViews'][i]
        s = old.get('byteOffset', 0)
        bv_img_map[i] = push(bin_[s:s + old['byteLength']])

    new_accessors = []
    for i in used_acc:
        a = dict(doc['accessors'][i])
        payload = acc_bytes(doc, bin_, i)
        old_bv = doc['bufferViews'][a['bufferView']]
        a['bufferView'] = push(payload, None)
        a['byteOffset'] = 0
        if 'target' in old_bv:
            new_bv[a['bufferView']]['target'] = old_bv['target']
        acc_new[i] = len(new_accessors)
        new_accessors.append(a)

    for me in doc['meshes']:
        for p in me['primitives']:
            p['attributes'] = {k: acc_new[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = acc_new[p['indices']]
    for im in doc.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = bv_img_map[im['bufferView']]

    doc['accessors'] = new_accessors
    doc['bufferViews'] = new_bv
    doc['buffers'] = [{"byteLength": len(newbin)}]

    after = prim_fingerprint(doc, bytes(newbin))
    if before != after:
        n = sum(1 for a, b in zip(before, after) if a != b)
        raise SystemExit("REFUSING: %d primitive(s) changed content under dedupe" % n)

    old_sz = os.path.getsize(path)
    print("accessors %d -> %d (%d duplicates), bufferViews %d -> %d"
          % (len(remap), len(new_accessors), dupes,
             len(read_glb(path)[0]['bufferViews']), len(new_bv)))
    print("primitive content identity: %d/%d primitives byte-identical" % (len(before), len(before)))
    if dry:
        print("DRY — would be about %.2f MB (was %.2f MB)" % (len(newbin) / 1e6, old_sz / 1e6))
        return
    total = write_glb(out, doc, bytes(newbin))
    print("WROTE %s  %d -> %d bytes  (%.1f%% smaller)"
          % (out, old_sz, total, 100.0 * (old_sz - total) / old_sz))


if __name__ == '__main__':
    a = sys.argv[1:]
    src = a[0]
    out = a[a.index('-o') + 1] if '-o' in a else src
    run(src, out, '--dry' in a)
