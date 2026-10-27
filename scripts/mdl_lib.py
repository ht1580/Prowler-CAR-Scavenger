"""Minimal Titanfall MDL v53 reader (offsets calibrated on the stock CAR with mdl_probe.py)."""
import struct
from pathlib import Path


class Mdl:
    def __init__(self, path):
        self.d = Path(path).read_bytes()
        assert self.d[:4] == b"IDST" and struct.unpack_from("<i", self.d, 4)[0] == 53, path

    def i(self, o, n=1):
        v = struct.unpack_from(f"<{n}i", self.d, o)
        return v if n > 1 else v[0]

    def s(self, o):
        return self.d[o:self.d.index(b"\0", o)].decode("ascii", "replace")

    def table(self, off, stride, rel=0):
        n, idx = self.i(off, 2)
        return [(idx + k * stride, self.s(idx + k * stride + self.i(idx + k * stride + rel))) for k in range(n)]

    def bones(self):
        return [n for _, n in self.table(160, 244)]

    def anims(self):
        return [n for _, n in self.table(184, 92, 4)]

    def sequences(self):
        an = self.anims()
        out = []
        for r, name in self.table(192, 232, 4):
            g0, g1 = self.i(r + 68, 2)
            ai = self.i(r + 60)
            raw = [struct.unpack_from("<h", self.d, r + ai + 2 * k)[0] for k in range(g0 * g1)]
            flags = self.i(r + 12)
            out.append({"name": name, "activity": self.s(r + self.i(r + 8)), "blend": [g0, g1], "raw": raw,
                        "anims": [an[x] if 0 <= x < len(an) else f"#INVALID({x})" for x in raw],
                        "looping": bool(flags & 1), "delta": bool(flags & 4), "autoplay": bool(flags & 8)})
        return out

    def textures(self):
        return [n for _, n in self.table(208, 44)]

    def skins(self):
        nref, nfam, idx = self.i(224, 3)
        tex = self.textures()
        return [[tex[struct.unpack_from("<h", self.d, idx + 2 * (f * nref + k))[0]] for k in range(nref)] for f in range(nfam)]

    def bodyparts(self):
        return [{"name": name, "options": self.i(r + 4), "base": self.i(r + 8)} for r, name in self.table(236, 16)]

    def attachments(self):
        bones = self.bones()
        return [{"name": name, "bone": bones[self.i(r + 8)]} for r, name in self.table(244, 92)]

    def poseparams(self):
        return [n for _, n in self.table(304, 20)]
