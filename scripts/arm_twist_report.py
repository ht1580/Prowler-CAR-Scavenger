"""blender -b --factory-startup -P arm_twist_report.py -- <anims dir> [<anims dir> ...]
Twist of the wrist relative to the elbow about the forearm axis, and of the elbow relative to the shoulder
about the upper-arm axis, over every frame of every full-pose animation. The TF2 arms mesh skins the forearm
between elbow / def_*_forearm / wrist: a large twist there wrings the sleeve and glove ("stretched hand")."""
import math
import os
import sys
from mathutils import Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name


def twist(parent, child, axis_local):
    q = (parent.inverted() @ child).to_quaternion()
    v = Vector((q.x, q.y, q.z))
    p = axis_local.normalized() * v.dot(axis_local.normalized())
    t = math.degrees(2 * math.atan2(p.length, abs(q.w)))
    return t


for d in sys.argv[sys.argv.index("--") + 1:]:
    worst = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".smd") or fn in ("ref.smd",) or fn.startswith("prowler_spin"):
            continue
        n, frames, _ = read_smd(os.path.join(d, fn))
        names = {nm for nm, _ in n.values()}
        if "def_l_wrist" not in names:
            continue
        mx = {"l_fore": 0, "r_fore": 0, "l_upper": 0, "r_upper": 0}
        for fr in frames:
            g = by_name(n, globals_(n, fr))
            for s in "lr":
                ax = Vector((1, 0, 0)) if s == "l" else Vector((-1, 0, 0))
                mx[f"{s}_fore"] = max(mx[f"{s}_fore"], twist(g[f"def_{s}_elbow"], g[f"def_{s}_wrist"], ax))
                mx[f"{s}_upper"] = max(mx[f"{s}_upper"], twist(g[f"def_{s}_shoulder"], g[f"def_{s}_elbow"], ax))
        worst.append((max(mx.values()), fn, mx))
    worst.sort(reverse=True)
    print(f"TWIST {d}")
    for w, fn, mx in worst[:12]:
        print(f"   {fn:40s} forearm L {mx['l_fore']:6.1f} R {mx['r_fore']:6.1f}  upper L {mx['l_upper']:6.1f} R {mx['r_upper']:6.1f}")
print("TWIST_OK")
