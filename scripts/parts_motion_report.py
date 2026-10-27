"""blender -b --factory-startup -P parts_motion_report.py -- <anims dir>
Every frame of every full-pose animation: how far each Prowler part bone (def_c_* except def_c_base and the
arms/body) moves away from its rest place relative to def_c_base. Parts that are glued to the gun should
stay put (rotating in place is fine for spinners); a part that wanders off is a "flying part"."""
import math
import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

d = sys.argv[sys.argv.index("--") + 1]
rn, rf, _ = read_smd(os.path.join(d, "ref.smd"))
R = by_name(rn, globals_(rn, rf[0]))
Rb = R["def_c_base"].inverted()
worst = {}
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".smd") or fn.startswith("prowler_spin") or fn == "ref.smd":
        continue
    n, frames, _ = read_smd(os.path.join(d, fn))
    names = [nm for nm, _ in n.values()]
    if "def_c_base" not in names:
        continue
    parts = [nm for nm in names if nm.startswith("def_c_") and nm != "def_c_base" and "spine" not in nm and "neck" not in nm
             and "head" not in nm and "hip" not in nm]
    for fi, fr in enumerate(frames):
        g = by_name(n, globals_(n, fr))
        gb = g["def_c_base"].inverted()
        for p in parts:
            if p not in R:
                continue
            a, b = Rb @ R[p], gb @ g[p]
            shift = (a.translation - b.translation).length
            key = (fn, p)
            if shift > worst.get(key, (0,))[0]:
                worst[key] = (shift, fi, len(frames))
rows = sorted(((v[0], k[0], k[1], v[1], v[2]) for k, v in worst.items()), reverse=True)
for s, fn, p, fi, nf in rows[:30]:
    print(f"PART {p:34s} in {fn:36s} moves {s:6.2f} at frame {fi}/{nf}")
print("PARTS_OK")
