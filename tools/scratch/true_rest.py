import json
import sys
from mathutils import Euler, Matrix, Quaternion, Vector


def rest(path):
    d = json.load(open(path, encoding="utf-8"))
    G = []
    for b in d["bones"]:
        q = Quaternion((b["quat"][3], b["quat"][0], b["quat"][1], b["quat"][2]))
        L = Matrix.Translation(Vector(b["pos"])) @ q.to_matrix().to_4x4()
        G.append((G[b["parent"]] if b["parent"] >= 0 else Matrix.Identity(4)) @ L)
    return {b["name"]: G[i] for i, b in enumerate(d["bones"])}


def last_pose(path):
    d = json.load(open(path, encoding="utf-8"))
    bones = d["bones"]
    p = max(d["poses"], key=lambda x: x["frame"])
    loc = {v["index"]: v for v in p["locals"]}
    G = []
    for i, b in enumerate(bones):
        v = loc.get(i, b)
        m = Matrix.Translation(Vector(v["pos"])) @ Euler(v["rot"], "XYZ").to_matrix().to_4x4()
        G.append((G[b["parent"]] if b["parent"] >= 0 else Matrix.Identity(4)) @ m)
    return {b["name"]: G[i] for i, b in enumerate(bones)}


S = r"%USERPROFILE%\AppData\Local\Temp\claude\E--\3c9f35e5-ab0e-4d54-bffb-1ee98c095406\scratchpad"
for tag, eng, draw in (("stock", r"D:\TitanfallMods\35_ProwlerCAR\build\engine-stock.json", S + r"\ref_stock_car_draw_seq.json"),
                       ("ours", r"D:\TitanfallMods\35_ProwlerCAR\build\engine-ours.json", S + r"\ref_ours_draw_seq.json")):
    R, D = rest(eng), last_pose(draw)
    rc, dc = R["jx_c_camera"].inverted(), D["jx_c_camera"].inverted()
    for b in ("def_c_base", "def_l_wrist", "def_r_wrist", "def_l_shoulder"):
        r, dd = rc @ R[b].translation, dc @ D[b].translation
        print(f"{tag:5s} {b:16s} MDL rest (cam) ({r.x:6.1f},{r.y:6.1f},{r.z:6.1f})   draw end ({dd.x:6.1f},{dd.y:6.1f},{dd.z:6.1f})   diff {(r - dd).length:5.2f}")
