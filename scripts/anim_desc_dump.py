"""python -I anim_desc_dump.py name=path.mdl ... : raw v53 anim descriptors for key animations
(flags, frames, fps, animblock, animindex, sectionindex/frames) + header animblock info, to see where a
model's animation data lives (embedded vs external blocks) and whether frame counts match stock."""
import struct
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from mdl_lib import Mdl

KEYS = ("@draw_seq", "@reload_seq", "@reload_empty_seq", "@sprint_seq", "attack_anim", "idle_anim_autoplay", "ads_in_anim", "@ref")
for a in sys.argv[1:]:
    name, path = a.split("=", 1)
    m = Mdl(path)
    print(f"== {name}  size {len(m.d)}  declared length {m.i(80)}")
    for row, n in m.table(184, 92, 4):
        if n in KEYS:
            ints = struct.unpack_from("<23i", m.d, row)
            fps = struct.unpack_from("<f", m.d, row + 8)[0]
            print(f"   {n:20s} flags {ints[3]:#06x} frames {ints[4]:4d} fps {fps:5.1f}  raw {ints[5:23]}")
