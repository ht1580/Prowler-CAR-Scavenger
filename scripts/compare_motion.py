"""blender -b --factory-startup -P compare_motion.py -- <stock.json> <port.json>
Decoded native poses (decode_native_pose.ps1 -AllFrames): per frame, how far the port's wrists / gun base /
magazine / camera are from the stock model's (camera space). ~0 = the port kept the TF2 animation."""
import json
import sys
from mathutils import Euler, Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]


def poses(path):
    d = json.load(open(path, encoding="utf-8"))
    bones = d["bones"]
    names = [b["name"] for b in bones]
    out = {}
    for p in d["poses"]:
        loc = {v["index"]: v for v in p["locals"]}
        g = []
        for i, b in enumerate(bones):
            v = loc.get(i, b)
            m = Matrix.Translation(Vector(v["pos"])) @ Euler(v["rot"], "XYZ").to_matrix().to_4x4()
            g.append((g[b["parent"]] if b["parent"] >= 0 else Matrix.Identity(4)) @ m)
        out[p["frame"]] = {n: g[i] for i, n in enumerate(names)}
    return out


S, Pp = poses(a[0]), poses(a[1])
worst = {}
for f in sorted(S):
    if f not in Pp:
        continue
    cs, cp = S[f]["jx_c_camera"].inverted(), Pp[f]["jx_c_camera"].inverted()
    for b in ("def_l_wrist", "def_r_wrist", "def_c_base", "def_c_magazine", "def_l_elbow"):
        if b in S[f] and b in Pp[f]:
            dd = ((cs @ S[f][b].translation) - (cp @ Pp[f][b].translation)).length
            worst[b] = max(worst.get(b, 0), dd)
print("MOTION max difference port vs stock (camera space): " + ", ".join(f"{k} {v:.2f}" for k, v in worst.items()))
