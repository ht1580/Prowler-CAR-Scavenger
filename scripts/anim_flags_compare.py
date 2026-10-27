"""python -I anim_flags_compare.py <stock.mdl> <ours.mdl> : anim-desc flags + frame count, and seqdesc flags,
stock vs ours, every difference listed (delta 0x4, noanimation 0x20, looping 0x1, autoplay 0x8 ...)."""
import struct
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from mdl_lib import Mdl

s, o = Mdl(sys.argv[1]), Mdl(sys.argv[2])


def anims(m):
    out = {}
    for row, name in m.table(184, 92, 4):
        out[name] = {"fps": struct.unpack_from("<f", m.d, row + 8)[0], "flags": m.i(row + 12), "frames": m.i(row + 16)}
    return out


def seqs(m):
    return {name: m.i(row + 12) for row, name in m.table(192, 232, 4)}


sa, oa = anims(s), anims(o)
diff = 0
for name, v in sa.items():
    w = oa.get(name)
    if w is None:
        print(f"ANIM missing in ours: {name}")
        diff += 1
    elif v["flags"] != w["flags"] or abs(v["fps"] - w["fps"]) > 1e-3:
        print(f"ANIM {name:36s} stock flags {v['flags']:#07x} fps {v['fps']:.1f} frames {v['frames']:4d} | ours flags {w['flags']:#07x} fps {w['fps']:.1f} frames {w['frames']:4d}")
        diff += 1
for name in oa:
    if name not in sa:
        print(f"ANIM extra in ours: {name} flags {oa[name]['flags']:#07x}")
ss, os_ = seqs(s), seqs(o)
for name, f in ss.items():
    if os_.get(name) != f:
        print(f"SEQ {name:36s} stock {f:#07x} ours {os_.get(name)}")
        diff += 1
print(f"FLAGS_COMPARE_DONE differences {diff}")
for name in ("idle_anim", "@idle_seq", "attack_anim", "@draw_seq", "@ref", "idle_anim_autoplay"):
    if name in sa:
        print(f"  stock {name:22s} flags {sa[name]['flags']:#07x} frames {sa[name]['frames']}")
