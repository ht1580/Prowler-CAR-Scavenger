"""Rest-pose vertex extents of a v53 MDL (embedded VVD, LOD0), plus where the grip-ish/front mass sits.
Usage: python -I mdl_vvd_bbox.py <mdl> [...]"""
import struct
import sys

for p in sys.argv[1:]:
    d = open(p, "rb").read()
    v = d.find(b"IDSV")
    numlods = struct.unpack_from("<i", d, v + 12)[0]
    nverts = struct.unpack_from("<i", d, v + 16)[0]
    vstart = struct.unpack_from("<i", d, v + 56)[0]
    pts = [struct.unpack_from("<3f", d, v + vstart + k * 48 + 16) for k in range(nverts)]
    mn = [min(q[i] for q in pts) for i in range(3)]
    mx = [max(q[i] for q in pts) for i in range(3)]
    # lowest-hanging part (grip / magazine) along forward axis z
    low = sorted(pts, key=lambda q: q[1])[: max(1, nverts // 50)]
    lowz = sum(q[2] for q in low) / len(low)
    print(f"{p.split(chr(92))[-3] + '/' + p.split(chr(92))[-1]:60s} verts={nverts:6d} "
          f"x[{mn[0]:6.2f},{mx[0]:6.2f}] y[{mn[1]:6.2f},{mx[1]:6.2f}] z[{mn[2]:6.2f},{mx[2]:6.2f}]  lowest-2%-verts mean z={lowz:6.2f}")
