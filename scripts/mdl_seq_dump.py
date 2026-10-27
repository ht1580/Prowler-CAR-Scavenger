"""Dump v53 sequence descs: label, activity, flags, fps-ish info, events (cycle/name/options). Usage: <mdl>"""
import struct
import sys

d = open(sys.argv[1], "rb").read()


def cstr(o):
    return d[o:d.index(b"\0", o)].decode("ascii", "replace")


n, idx = struct.unpack_from("<2i", d, 192)
for i in range(n):
    r = idx + i * 232
    lab, act = (cstr(r + struct.unpack_from("<i", d, r + o)[0]) for o in (4, 8))
    flags, activity, actweight, nev, evi = struct.unpack_from("<5i", d, r + 12)
    numblends, animindexindex = struct.unpack_from("<2i", d, r + 56)
    fin, fout = struct.unpack_from("<2f", d, r + 104)
    nmod, modi = struct.unpack_from("<2i", d, r + 188), None
    print(f"[{i}] {lab} act={act} w={actweight} flags=0x{flags:x} blends={numblends} fade={fin:.2f}/{fout:.2f} events={nev}")
    for e in range(nev):
        er = r + evi + e * 80
        cyc, ev, typ = struct.unpack_from("<f2i", d, er)
        opts = d[er + 12:er + 76].split(b"\0")[0].decode("ascii", "replace")
        nameoff = struct.unpack_from("<i", d, er + 76)[0]
        name = cstr(er + nameoff) if 0 < nameoff < 100000 else ""
        print(f"     cycle={cyc:.3f} event={ev} type={typ} name={name} options={opts!r}")
