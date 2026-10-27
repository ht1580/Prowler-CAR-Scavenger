"""Make every stock-indexed seqdesc carry the stock CAR's flags and bbox (in place).
SFM studiomdl + MDLShit turn Crowbar's "noanimation" (stock v53 flag 0x80000 on the idle seqs) into
0x100000, add 0x80000 to optic_layer, and recompute per-sequence bboxes; the game sees the stock CAR's
values for these sequences, so copy them verbatim. Appended (Prowler-only) sequences keep only the
classic low flag bits and get the stock idle_seq bbox.
Usage: python -I seq_fix.py <stock.mdl> <built.mdl>"""
import struct
import sys

SEQ_COUNT, SEQ_STRIDE, FLAGS, BBOX = 192, 232, 12, 32


def seqs(d):
    n, idx = struct.unpack_from("<2i", d, SEQ_COUNT)
    out = []
    for k in range(n):
        r = idx + k * SEQ_STRIDE
        name = d[r + struct.unpack_from("<i", d, r + 4)[0]:].split(b"\0")[0].decode()
        out.append((r, name))
    return out


stock = open(sys.argv[1], "rb").read()
built = bytearray(open(sys.argv[2], "rb").read())
s, b = seqs(stock), seqs(built)
assert len(b) >= len(s), "built model has fewer sequences than stock"
idle_bb = None
changed = 0
for (rs, ns), (rb, nb) in zip(s, b):
    assert ns == nb, f"sequence order differs from stock: {ns} vs {nb}"
    want = stock[rs + FLAGS:rs + FLAGS + 4] + b""
    bb = stock[rs + BBOX:rs + BBOX + 24]
    if ns == "idle_seq":
        idle_bb = bb
    if built[rb + FLAGS:rb + FLAGS + 4] != want or built[rb + BBOX:rb + BBOX + 24] != bb:
        changed += 1
    built[rb + FLAGS:rb + FLAGS + 4] = want
    built[rb + BBOX:rb + BBOX + 24] = bb
for rb, nb in b[len(s):]:
    fl = struct.unpack_from("<i", built, rb + FLAGS)[0]
    struct.pack_into("<i", built, rb + FLAGS, fl & 0xFFFF)
    if idle_bb:
        built[rb + BBOX:rb + BBOX + 24] = idle_bb
    print(f"appended {nb}: flags {fl:#x} -> {fl & 0xFFFF:#x}")
open(sys.argv[2], "wb").write(built)

# verify
s2, b2 = seqs(stock), seqs(bytes(built))
bad = [nb for (rs, _), (rb, nb) in zip(s2, b2)
       if stock[rs + FLAGS:rs + FLAGS + 4] != built[rb + FLAGS:rb + FLAGS + 4]
       or stock[rs + BBOX:rs + BBOX + 24] != built[rb + BBOX:rb + BBOX + 24]]
print(f"patched {changed} of {len(s)} stock sequences; mismatches after patch: {bad}")
print("SEQ_FIX_OK" if not bad else "SEQ_FIX_FAIL")
sys.exit(1 if bad else 0)
