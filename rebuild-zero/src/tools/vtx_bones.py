"""python -I vtx_bones.py <v53 mdl>... : the embedded VTX hardware-bone setup the renderer skins with.
Per strip: bone count, bone-state-change table (hardware slot -> model bone); per vertex: VTX boneID (slot)
vs the VVD vertex bone (model bone). If a renderer used slots as model bones, any strip whose slot->bone
map is not identity would skin to the wrong bones."""
import struct
import sys
from collections import Counter

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdl_lib import Mdl


def find_vtx(d):
    checksum = struct.unpack_from("<i", d, 8)[0]
    hits = []
    o = d.find(struct.pack("<i", 7))
    while o >= 0:
        if o + 36 <= len(d) and struct.unpack_from("<i", d, o + 16)[0] == checksum and struct.unpack_from("<i", d, o + 20)[0] in range(1, 9):
            hits.append(o)
        o = d.find(struct.pack("<i", 7), o + 1)
    return hits


for path in sys.argv[1:]:
    m = Mdl(path)
    d = m.d
    bones = m.bones()
    v = d.find(b"IDSV")
    nverts = struct.unpack_from("<i", d, v + 16)[0]
    vstart = struct.unpack_from("<i", d, v + 56)[0]
    vvd_bones = [struct.unpack_from("<3B", d, v + vstart + k * 48 + 12) + (d[v + vstart + k * 48 + 15],) for k in range(nverts)]
    hits = find_vtx(d)
    print(f"FILE {path}\n  bones {len(bones)}  vvd verts {nverts}  vtx candidates {hits}")
    if not hits:
        continue
    x = hits[0]
    ver, cache, mbs, mbt, mbv, chk, nlod, mrl, nbp, bpo = struct.unpack_from("<iiHHiiiiii", d, x)
    print(f"  VTX version {ver} maxBonesPerStrip {mbs} maxBonesPerTri {mbt} maxBonesPerVert {mbv} lods {nlod} bodyparts {nbp}")
    totals = Counter()
    vtx_hist = Counter()
    vvd_hist = Counter(bones[b] for vb in vvd_bones for b in vb[:vb[3]])
    for bp in range(nbp):
        b0 = x + bpo + bp * 8
        nmodels, moff = struct.unpack_from("<ii", d, b0)
        for mi in range(nmodels):
            m0 = b0 + moff + mi * 8
            nlods, loff = struct.unpack_from("<ii", d, m0)
            l0 = m0 + loff                                         # LOD0 only
            nmesh, meshoff, _sw = struct.unpack_from("<iif", d, l0)
            for me in range(nmesh):
                me0 = l0 + meshoff + me * 9
                nsg, sgoff, mflags = struct.unpack_from("<iiB", d, me0)
                for sg in range(nsg):
                    g0 = me0 + sgoff + sg * 25
                    nv, voff, ni, ioff, ns, soff, gflags = struct.unpack_from("<iiiiiiB", d, g0)
                    for st in range(ns):
                        s0 = g0 + soff + st * 27
                        sni, sio, snv, svo, snb, sfl, nbsc, bsco = struct.unpack_from("<iiiihBii", d, s0)
                        bsc = [struct.unpack_from("<ii", d, s0 + bsco + k * 8) for k in range(nbsc)]
                        ident = all(h == b for h, b in bsc)
                        totals["strips"] += 1
                        totals["identity" if ident else "remapped"] += 1
                        if bp == 0 and mi == 0 and me < 3 and st < 2:
                            print(f"    bp{bp} model{mi} mesh{me} sg{sg} strip{st}: verts {snv} bones {snb} state changes {nbsc} "
                                  f"identity {ident} first map {[(h, bones[b] if 0 <= b < len(bones) else b) for h, b in bsc[:6]]}")
                    # vertex check: VTX slot -> (strip bone-state map) -> model bone  vs  the VVD vertex bone
                    slot_map = {}
                    for st in range(ns):
                        s0 = g0 + soff + st * 27
                        nbsc, bsco = struct.unpack_from("<ii", d, s0 + 19)
                        for k in range(nbsc):
                            h, b = struct.unpack_from("<ii", d, s0 + bsco + k * 8)
                            slot_map[h] = b
                    for k in range(nv):
                        bw0, bw1, bw2, nb, orig, i0, i1, i2 = struct.unpack_from("<BBBBHBBB", d, g0 + voff + k * 9)
                        totals["vtx_verts"] += 1
                        for i in (i0, i1, i2)[:nb]:
                            b = slot_map.get(i, -1)
                            vtx_hist[bones[b] if 0 <= b < len(bones) else f"UNMAPPED slot {i}"] += 1
    print("  totals", dict(totals))
    diff = {b: (vtx_hist.get(b, 0), vvd_hist.get(b, 0)) for b in set(vtx_hist) | set(vvd_hist) if vtx_hist.get(b, 0) != vvd_hist.get(b, 0)}
    print(f"  bone-link histogram VTX(after slot map) vs VVD: {len(diff)} bones differ")
    for b, (a_, v_) in sorted(diff.items(), key=lambda kv: -abs(kv[1][0] - kv[1][1]))[:15]:
        print(f"     {b:32s} vtx {a_:6d}  vvd {v_:6d}")
