import math
import sys
from mathutils import Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

for fn, fi in (("draw_seq", -1), ("reload_seq", 30), ("sprint_seq", 5), ("ads_in_anim", -1)):
    n, f, _ = read_smd(rf"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims\{fn}.smd")
    L = {n[i][0]: m for i, m in f[fi].items()}
    g = by_name(n, globals_(n, f[fi]))
    for s in "l":
        print(fn, fi)
        for child, parent in (("shoulderTwist", "shoulder"), ("shoulderMid", "shoulder"), ("elbowB", "shoulder"), ("elbow", "shoulderMid"),
                              ("forearm", "elbow"), ("wrist", "elbow")):
            m = g[f"def_{s}_{parent}"].inverted() @ g[f"def_{s}_{child}"]
            q = m.to_quaternion()
            ax, ang = q.axis, math.degrees(q.angle)
            print(f"   {child:14s} in {parent:12s} rot {ang:6.1f} deg about ({ax.x:5.2f},{ax.y:5.2f},{ax.z:5.2f})  pos {tuple(round(x, 2) for x in m.translation)}")
        # twist split: forearm vs wrist about x
        def tw(a, b):
            q = (g[a].inverted() @ g[b]).to_quaternion()
            return math.degrees(2 * math.atan2(q.x, q.w))
        print(f"   twist about x: forearm/elbow {tw(f'def_{s}_elbow', f'def_{s}_forearm'):6.1f}  wrist/elbow {tw(f'def_{s}_elbow', f'def_{s}_wrist'):6.1f}  "
              f"shoulderTwist/shoulder {tw(f'def_{s}_shoulder', f'def_{s}_shoulderTwist'):6.1f}  shoulder/clav {tw(f'def_{s}_clav', f'def_{s}_shoulder'):6.1f}")
