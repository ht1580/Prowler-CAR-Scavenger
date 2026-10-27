"""Compare sequence / attachment / pose-parameter name order of two Titanfall MDL v53 files (stock vs built).
Usage: python -I mdl_seq_order.py <stock.mdl> <built.mdl>
"""
import struct
import sys


def cstr(d, o):
    return d[o:d.index(b"\0", o)].decode("ascii", "replace")


def table(d, count_off, stride, name_rel):
    """Find a (count, index) pair at count_off; names via name_rel offset inside each record."""
    n, idx = struct.unpack_from("<2i", d, count_off)
    out = []
    for i in range(n):
        rec = idx + i * stride
        out.append(cstr(d, rec + struct.unpack_from("<i", d, rec + name_rel)[0]))
    return out


def probe_sequences(d):
    # v53 header is v49 + 4 bytes; v49 localseq is at 188 -> try a small window and stride candidates
    for off in range(184, 212, 4):
        for stride in (212, 216, 220, 224, 228, 232, 236, 240):
            try:
                names = table(d, off, stride, 4)
            except Exception:
                continue
            if names and all(n and n.isprintable() and len(n) < 64 for n in names) and len(names) > 50:
                return off, stride, names
    raise SystemExit("sequence table not found")


a, b = (open(p, "rb").read() for p in sys.argv[1:3])
off, stride, sa = probe_sequences(a)
sb = table(b, off, stride, 4)
print(f"seq table @{off} stride {stride}: stock {len(sa)} built {len(sb)}")
bad = [i for i, n in enumerate(sa) if i >= len(sb) or sb[i] != n]
print("SEQ_ORDER", "OK" if not bad else f"MISMATCH at {bad[:5]}", "| extra:", sb[len(sa):])
