"""blender -b --factory-startup -P end_pose_report.py -- <anims dir> [<anims dir>]
idle_seq / attack_seq are delta + noanimation: whatever full-pose sequence played last keeps holding its
final frame underneath them. So every sequence the weapon can go idle from must END in the hip pose
(draw_seq end). Prints, per full-pose animation, how far its first/last frame gun (def_c_base, camera space)
and left wrist are from the hip pose."""
import math
import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name


def pose(path, fi):
    n, f, _ = read_smd(path)
    g = by_name(n, globals_(n, f[fi if fi >= 0 else len(f) + fi]))
    c = g["jx_c_camera"].inverted()
    return c @ g["def_c_base"], c @ g["def_l_wrist"], c @ g["def_r_wrist"], len(f)


for d in sys.argv[sys.argv.index("--") + 1:]:
    hip = pose(os.path.join(d, "draw_seq.smd"), -1)
    print("END", d)
    rows = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".smd") or fn.startswith("prowler_spin") or fn == "ref.smd":
            continue
        try:
            first, last = pose(os.path.join(d, fn), 0), pose(os.path.join(d, fn), -1)
        except (KeyError, ValueError):
            continue
        def dist(p):
            return ((p[0].translation - hip[0].translation).length,
                    math.degrees(p[0].to_quaternion().rotation_difference(hip[0].to_quaternion()).angle),
                    (p[1].translation - hip[1].translation).length)
        a, b = dist(first), dist(last)
        rows.append((b[0] + b[1] / 10, fn, last[3], a, b))
    rows.sort(reverse=True)
    for _, fn, nf, a, b in rows:
        flag = "  <<< ends off the hip pose" if b[0] > 0.5 or b[1] > 3 else ""
        print(f"   {fn:40s} frames {nf:4d}  start gun {a[0]:5.2f}u {a[1]:5.1f}deg  END gun {b[0]:5.2f}u {b[1]:5.1f}deg  L-wrist {b[2]:5.2f}u{flag}")
print("END_OK")
