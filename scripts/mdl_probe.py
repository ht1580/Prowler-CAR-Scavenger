"""Locate v53 header tables by probing (count,index) pairs whose records carry printable names.
Prints candidate (offset, stride, name_rel) with first names, for stock-model calibration."""
import struct
import sys

d = open(sys.argv[1], "rb").read()


def cstr(o):
    if not 0 <= o < len(d):
        return None
    e = d.find(b"\0", o)
    s = d[o:e]
    try:
        s = s.decode("ascii")
    except Exception:
        return None
    return s if s and s.isprintable() and len(s) < 120 else None


def try_table(off, stride, rel, inline=False):
    n, idx = struct.unpack_from("<2i", d, off)
    if not (0 < n < 2000 and 0 < idx < len(d) - stride):
        return None
    names = []
    for i in range(min(n, 400)):
        r = idx + i * stride
        if r + rel + 4 > len(d):
            return None
        s = cstr(r + rel) if inline else cstr(r + struct.unpack_from("<i", d, r + rel)[0])
        if s is None:
            return None
        names.append(s)
    return n, names


for off in range(96, 420, 4):
    for stride in (8, 12, 16, 20, 24, 32, 44, 48, 56, 64, 68, 72, 80, 88, 92, 96, 100, 104, 112, 116, 120, 128, 144, 148, 152, 160, 176, 232):
        for rel, inline in ((0, False), (4, False), (0, True)):
            r = try_table(off, stride, rel, inline)
            if r and r[0] > 0:
                n, names = r
                print(f"off={off} stride={stride} rel={rel}{' inline' if inline else ''} n={n}: {names[:4]}")
