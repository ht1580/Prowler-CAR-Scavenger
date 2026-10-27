"""blender -b --factory-startup -P screen_scan.py -- <anims dir> [h_limit v_limit]
For every frame of every full-pose animation: view angles (horizontal, vertical; camera +Z forward, +X = screen
left, +Y = up) of both wrists, the magazine and the gun base. Lists frames where a hand or the magazine sits
in the band Apex keeps off screen but a wider TF2 viewmodel view shows (|h| or |v| between the limits), and
any hand in the upper half of the view."""
import math
import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

a = sys.argv[sys.argv.index("--") + 1:]
d = a[0]
lo, hi = (float(a[1]), float(a[2])) if len(a) > 2 else (35.0, 62.0)


def ang(v):
    if v.z <= 0.05:
        return None
    return math.degrees(math.atan2(v.x, v.z)), math.degrees(math.atan2(v.y, v.z))


hits = []
upper = []
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".smd") or fn.startswith("prowler_spin") or fn == "ref.smd":
        continue
    n, frames, _ = read_smd(os.path.join(d, fn))
    names = {nm for nm, _ in n.values()}
    if not {"def_l_wrist", "def_c_magazine", "jx_c_camera"} <= names:
        continue
    for fi, fr in enumerate(frames):
        g = by_name(n, globals_(n, fr))
        c = g["jx_c_camera"].inverted()
        for b in ("def_l_wrist", "def_r_wrist", "def_c_magazine"):
            v = ang(c @ g[b].translation)
            if v is None:
                continue
            m = max(abs(v[0]), abs(v[1]) * 1.6)          # 16:9: vertical edge is closer
            if lo <= m <= hi:
                hits.append((fn, fi, b, v))
            if b != "def_c_magazine" and v[1] > 8:
                upper.append((fn, fi, b, v))
print(f"SCAN band {lo}-{hi}: {len(hits)} element-frames")
by = {}
for fn, fi, b, v in hits:
    by.setdefault((fn, b), []).append((fi, v))
for (fn, b), lst in sorted(by.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"   {fn:38s} {b:16s} frames {lst[0][0]}-{lst[-1][0]} ({len(lst)})  e.g. h {lst[len(lst)//2][1][0]:5.0f} v {lst[len(lst)//2][1][1]:5.0f}")
print(f"UPPER hands above the centre line: {len(upper)}")
for fn, fi, b, v in upper[:20]:
    print(f"   {fn:38s} f{fi:3d} {b:12s} h {v[0]:5.0f} v {v[1]:5.0f}")
print("SCAN_OK")
