"""Compare attachment local matrices (mstudioattachment_t: name@0 flags@4 bone@8 matrix3x4@12) stock vs built.
Usage: python -I mdl_attach.py <stock.mdl> <built.mdl>"""
import math
import struct
import sys


def atts(p):
    d = open(p, "rb").read()
    nb, bi = struct.unpack_from("<2i", d, 160)
    bones = [d[bi + k * 244 + struct.unpack_from("<i", d, bi + k * 244)[0]:].split(b"\0")[0].decode() for k in range(nb)]
    n, idx = struct.unpack_from("<2i", d, 244)
    out = {}
    for k in range(n):
        r = idx + k * 92
        name = d[r + struct.unpack_from("<i", d, r)[0]:].split(b"\0")[0].decode()
        bone = struct.unpack_from("<i", d, r + 8)[0]
        m = struct.unpack_from("<12f", d, r + 12)
        out[name] = (bones[bone], m)
    return out


a, b = atts(sys.argv[1]), atts(sys.argv[2])
for name, (bone, m) in a.items():
    bb, mb = b.get(name, (None, None))
    rot_diff = max(abs(m[i] - mb[i]) for i in (0, 1, 2, 4, 5, 6, 8, 9, 10)) if mb else None
    pos_a = (m[3], m[7], m[11])
    pos_b = (mb[3], mb[7], mb[11]) if mb else None
    flag = "" if rot_diff is not None and rot_diff < 1e-3 else "  <-- ROTATION DIFFERS"
    print(f"{name:20s} bone {bone:18s}->{bb:18s} pos stock({pos_a[0]:7.2f},{pos_a[1]:7.2f},{pos_a[2]:7.2f}) "
          f"ours({pos_b[0]:7.2f},{pos_b[1]:7.2f},{pos_b[2]:7.2f}) maxRotDiff={rot_diff:.4f}{flag}")
