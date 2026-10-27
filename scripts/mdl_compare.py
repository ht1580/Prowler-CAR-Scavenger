"""Compare index-sensitive name tables of a built v53 MDL against the stock one.
Tables are located by probing header (count,index) pairs whose records resolve to printable names
(validated against the stock model). Usage: python -I mdl_compare.py <stock.mdl> <built.mdl>
"""
import struct
import sys


def cstr(d, o):
    e = d.find(b"\0", o)
    return d[o:e].decode("ascii", "replace") if 0 <= o < len(d) and e > 0 else None


def read(d, off, stride, rel=0):
    n, idx = struct.unpack_from("<2i", d, off)
    if not (0 < n < 400 and 0 < idx < len(d)):
        return None
    out = []
    for i in range(n):
        r = idx + i * stride
        if r + rel + 4 > len(d):
            return None
        s = cstr(d, r + struct.unpack_from("<i", d, r + rel)[0])
        if not s or not s.isprintable() or len(s) > 80:
            return None
        out.append(s)
    return out


TABLES = {"sequence": (192, 232, 4)}
a, b = (open(p, "rb").read() for p in sys.argv[1:3])
# probe attachments (record 92 bytes in v49; try a few) and bodyparts (16 bytes)
for name, strides in (("attachment", (92, 96, 100)), ("bodypart", (16,))):
    for off in range(200, 300, 4):
        hit = next(((off, s, 0) for s in strides if (r := read(a, off, s)) and
                    (name != "attachment" or "muzzle_flash" in r) and (name != "bodypart" or len(r) <= 12)), None)
        if hit and name not in TABLES:
            TABLES[name] = hit
ok = True
for name, (off, stride, rel) in TABLES.items():
    sa, sb = read(a, off, stride, rel), read(b, off, stride, rel)
    bad = [i for i, x in enumerate(sa) if sb is None or i >= len(sb) or sb[i] != x]
    ok &= not bad
    print(f"{name:10s} @{off} stride {stride}: stock {len(sa)} built {len(sb or [])} ->",
          "OK" if not bad else f"MISMATCH at {bad[:6]} stock={[sa[i] for i in bad[:3]]}", "| appended:", (sb or [])[len(sa):])
print("COMPARE_OK" if ok else "COMPARE_FAIL")
