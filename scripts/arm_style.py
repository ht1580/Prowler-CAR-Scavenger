"""blender -b --factory-startup -P arm_style.py -- name=json ... : how a viewmodel's animation treats the arm chain,
over every decoded frame: shoulders in camera space (max forward), elbow hinge (local twist about the upper
arm), bone lengths shoulder->elbow / elbow->wrist, spine height, gun-to-camera distance."""
import json
import math
import sys
from mathutils import Euler, Matrix, Vector

for arg in sys.argv[sys.argv.index("--") + 1:]:
    name, path = arg.split("=", 1)
    d = json.load(open(path, encoding="utf-8"))
    bones = d["bones"]
    names = [b["name"] for b in bones]
    ix = {n: i for i, n in enumerate(names)}
    st = {"sh_fwd": -99, "upper_twist": 0, "len_ue": set(), "len_ew": set(), "hip": set(), "gun_dist": []}
    for p in d["poses"]:
        loc = {v["index"]: v for v in p["locals"]}
        L, G = [], []
        for i, b in enumerate(bones):
            v = loc.get(i, b)
            m = Matrix.Translation(Vector(v["pos"])) @ Euler(v["rot"], "XYZ").to_matrix().to_4x4()
            L.append(m)
            G.append((G[b["parent"]] if b["parent"] >= 0 else Matrix.Identity(4)) @ m)
        c = G[ix["jx_c_camera"]].inverted()
        for s in "lr":
            sh = c @ G[ix[f"def_{s}_shoulder"]].translation
            st["sh_fwd"] = max(st["sh_fwd"], sh.z)
            q = L[ix[f"def_{s}_elbow"]].to_quaternion()
            tw = abs(math.degrees(2 * math.atan2(q.x, q.w)))
            st["upper_twist"] = max(st["upper_twist"], min(tw, 360 - tw))
            st["len_ue"].add(round((G[ix[f"def_{s}_elbow"]].translation - G[ix[f"def_{s}_shoulder"]].translation).length, 2))
            st["len_ew"].add(round((G[ix[f"def_{s}_wrist"]].translation - G[ix[f"def_{s}_elbow"]].translation).length, 2))
        st["hip"].add(round(L[ix["def_c_hip"]].translation.length, 2))
        st["gun_dist"].append((c @ G[ix["def_c_base"]].translation).length)
    print(f"ARMS {name:22s} frames {len(d['poses']):3d}  shoulder max forward {st['sh_fwd']:5.2f}  elbow twist max {st['upper_twist']:5.1f}"
          f"  upper len {sorted(st['len_ue'])[:3]}  fore len {sorted(st['len_ew'])[:3]}  hip {sorted(st['hip'])[:2]}"
          f"  gun dist {min(st['gun_dist']):5.1f}-{max(st['gun_dist']):5.1f}")
