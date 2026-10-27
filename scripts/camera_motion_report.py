"""blender -b --factory-startup -P camera_motion_report.py -- <anims dir> [<anims dir>]
How far the animated camera bone (jx_c_camera) moves away from the model origin (= where the engine puts the
eye) in every full-pose animation: max translation and max rotation over all frames. Renders taken from
jx_c_camera hide this; if the game does not follow the camera bone, an Apex pose authored around a moving
camera lands somewhere else on screen."""
import math
import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

for d in sys.argv[sys.argv.index("--") + 1:]:
    rows = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".smd") or fn.startswith("prowler_spin") or fn == "ref.smd":
            continue
        n, frames, _ = read_smd(os.path.join(d, fn))
        if "jx_c_camera" not in {nm for nm, _ in n.values()}:
            continue
        mt = mr = 0.0
        g0 = None
        for fr in frames:
            g = by_name(n, globals_(n, fr))
            rel = g["jx_c_pov"].inverted() @ g["jx_c_camera"]
            mt = max(mt, rel.translation.length)
            mr = max(mr, math.degrees(rel.to_quaternion().angle))
        rows.append((mr, mt, fn, len(frames)))
    rows.sort(reverse=True)
    print(f"CAM {d}")
    for mr, mt, fn, nf in rows[:14]:
        print(f"   {fn:40s} frames {nf:4d} camera max rot {mr:6.1f} deg  max move {mt:6.2f}")
print("CAM_OK")
