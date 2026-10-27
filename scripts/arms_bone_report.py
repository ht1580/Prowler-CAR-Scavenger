"""blender -b --factory-startup -P arms_bone_report.py -- <anim> <frame>
Arms bones (pilot arms model) in camera space for stock vs ours at one frame, plus the bone lengths
(parent->child distance) each animation implies vs the arms model's rest. Bonemerge copies world transforms
by name, so a viewmodel skeleton with different bone lengths stretches/tears the arms mesh."""
import json
import sys
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
a = sys.argv[sys.argv.index("--") + 1:]
anim, frame = a[0], int(a[1])
ab = json.load(open(ROOT + r"\stock\arms\arms_bones.json", encoding="utf-8"))["bones"]
names = [b["name"] for b in ab]


def pose(d):
    n, f, _ = read_smd(d + "\\" + anim + ".smd")
    return by_name(n, globals_(n, f[frame if frame >= 0 else len(f) + frame]))


S = pose(ROOT + r"\stock\view\ptpov_car101_anims")
O = pose(ROOT + r"\build\view\anims")
for b in ab:
    nm = b["name"]
    if nm not in S or nm not in O:
        continue
    p = b["parent"]
    rest_len = Vector(b["pos"]).length
    pn = names[p] if p >= 0 else None
    sl = (S[nm].translation - S[pn].translation).length if pn in S else 0
    ol = (O[nm].translation - O[pn].translation).length if pn in O else 0
    sc = S["jx_c_camera"].inverted() @ S[nm].translation
    oc = O["jx_c_camera"].inverted() @ O[nm].translation
    flag = "  <<< length" if abs(ol - rest_len) > 0.5 else ""
    print(f"BONE {nm:24s} parent {str(pn):22s} len arms {rest_len:6.2f} stock {sl:6.2f} ours {ol:6.2f}   "
          f"cam stock ({sc.x:6.1f},{sc.y:6.1f},{sc.z:6.1f}) ours ({oc.x:6.1f},{oc.y:6.1f},{oc.z:6.1f}){flag}")
print("ARMS_REPORT_OK")
