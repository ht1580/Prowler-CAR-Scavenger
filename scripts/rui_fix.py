"""Re-seat the CAR body RUI on the Prowler (in place, same topology/byte layout).

car_smg_rui_lower (ui2 ammo counter)  -> onto the Prowler tank's "0000" counter window, facing the player
                                         (+x = rig left = toward the hip camera), rotated -90 deg about Y so the
                                         text reads rear->front unmirrored from that side.
car_smg_rui_upper (ui1 rail strip)    -> collapsed inside the receiver (CAR top-rail geometry; the user's
                                         crosshair mods disable ui1 anyway).
Usage: python -I rui_fix.py <conv.mdl>
"""
import json
import math
import struct
import sys
sys.path.insert(0, r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench")
import rui_editor

COUNTER_CENTER = (0.835, 48.75, 2.98)
COUNTER_SCALE = 1.25
HIDE_POINT = (0.0, 46.5, 5.0)

path = sys.argv[1]
sk = json.load(open(r"D:\TitanfallMods\35_ProwlerCAR\build\view\skeleton.json"))
doc = rui_editor.inspect_mdl(path)
data = bytearray(doc["bytes"])


def bone_origin(name):
    m = sk["rest_global"][name]
    rot_ok = all(abs(m[i][j] - (1.0 if i == j else 0.0)) < 1e-4 for i in range(3) for j in range(3))
    assert rot_ok, f"{name} rest has rotation; this script assumes axis-aligned parent"
    return (m[0][3], m[1][3], m[2][3])


report = {}
for mesh in doc["meshes"]:
    name = mesh["name"]
    if name.endswith("car_smg_rui_lower") or name.endswith("car_smg_rui_upper"):
        bone = mesh["parentNames"][0]
        o = bone_origin(bone)
        pts = [v["position"] for v in mesh["vertices"]]
        c = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
        out = []
        for p in pts:
            if name.endswith("lower"):
                dx, dy, dz = ((p[i] - c[i]) * COUNTER_SCALE for i in range(3))
                # Ry(-90): x' = -dz ; z' = dx
                mx, my, mz = -dz + COUNTER_CENTER[0], dy + COUNTER_CENTER[1], dx + COUNTER_CENTER[2]
            else:
                mx, my, mz = HIDE_POINT
            out.append((mx - o[0], my - o[1], mz - o[2]))
        for v, q in zip(mesh["vertices"], out):
            struct.pack_into("<3f", data, v["offset"] + 4, *q)
        report[name] = {"bone": bone, "vertices": len(out), "action": "counter" if name.endswith("lower") else "collapsed"}
    elif name.endswith("pro_screen_rui_upper"):
        # pro-screen mesh was scaled about def_c_proscreen in build_view; scale its bone-local RUI to match
        s = sk["report"].get("proscreen_scale", 1.0)
        for v in mesh["vertices"]:
            struct.pack_into("<3f", data, v["offset"] + 4, *(x * s for x in v["position"]))
        report[name] = {"bone": mesh["parentNames"][0], "scaled": s}
open(path, "wb").write(bytes(data))
check = rui_editor.inspect_mdl(path)
assert len(check["meshes"]) == len(doc["meshes"])
print("RUI_FIX_OK", json.dumps(report))
