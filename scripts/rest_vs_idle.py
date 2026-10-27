"""blender -b --factory-startup -P rest_vs_idle.py
idle_seq / attack_seq are delta + noanimation: in game they are layered on the model's REST pose
($definebone = ref), not on the last frame of draw_seq. For stock and ours: rest pose vs draw_seq end
(world positions relative to the camera) for the arm chain and the gun."""
import re
import sys
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
BONES = ("def_l_shoulder", "def_r_shoulder", "def_l_elbow", "def_l_wrist", "def_r_wrist", "def_c_base", "def_c_reactive_spinner_coils", "jx_c_camera")


def definebones(qc):
    nodes, local = {}, {}
    names = []
    for m in re.finditer(r'^\$definebone "([^"]+)" "([^"]*)" ([-\d.e ]+)$', open(qc, encoding="utf-8", errors="replace").read(), re.M):
        v = [float(x) for x in m[3].split()]
        names.append((m[1], m[2]))
    idx = {n: i for i, (n, _) in enumerate(names)}
    for m in re.finditer(r'^\$definebone "([^"]+)" "([^"]*)" ([-\d.e ]+)$', open(qc, encoding="utf-8", errors="replace").read(), re.M):
        v = [float(x) for x in m[3].split()]
        i = idx[m[1]]
        nodes[i] = (m[1], idx.get(m[2], -1))
        import math
        local[i] = Matrix.Translation(Vector(v[:3])) @ Euler([math.radians(a) for a in v[3:6]], "XYZ").to_matrix().to_4x4()
    return by_name(nodes, globals_(nodes, local))


def last(path, fi=-1):
    n, f, _ = read_smd(path)
    return by_name(n, globals_(n, f[fi]))


sets = {
    "stock definebone": definebones(ROOT + r"\stock\view\ptpov_car101.qc"),
    "stock ref.smd": last(ROOT + r"\stock\view\ptpov_car101_anims\ref.smd", 0),
    "stock draw end": last(ROOT + r"\stock\view\ptpov_car101_anims\draw_seq.smd"),
    "ours definebone": definebones(ROOT + r"\build\view\ptpov_car101.qc"),
    "ours ref.smd": last(ROOT + r"\build\view\anims\ref.smd", 0),
    "ours draw end": last(ROOT + r"\build\view\anims\draw_seq.smd"),
}
for b in BONES:
    row = []
    for k, g in sets.items():
        if b in g and "jx_c_camera" in g:
            v = g["jx_c_camera"].inverted() @ g[b].translation
            row.append(f"{k}: ({v.x:6.1f},{v.y:6.1f},{v.z:6.1f})")
        else:
            row.append(f"{k}: -")
    print(f"REST {b:30s} " + " | ".join(row))
print("REST_OK")
