import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

for d, tag in ((r"D:\TitanfallMods\35_ProwlerCAR\build\view\anims", "ours"),):
    for fn in ("reload_empty_seq.smd", "reload_seq.smd"):
        n, f, _ = read_smd(os.path.join(d, fn))
        row = []
        for fi in range(0, len(f), 5):
            g = by_name(n, globals_(n, f[fi]))
            c = g["jx_c_camera"].inverted()
            w = c @ g["def_l_wrist"].translation
            m = c @ g["def_c_magazine"].translation
            row.append(f"f{fi}: hand-mag {(g['def_l_wrist'].translation - g['def_c_magazine'].translation).length:5.1f} handZ {w.z:5.1f}")
        print(tag, fn)
        print("   " + " | ".join(row))
