"""blender -b --factory-startup -P arms_axes_report.py -- <anim> <frame>
Bonemerge copies FULL world transforms by bone name, so the TF2 arms mesh is right only if every arms bone's
local frame (child offset direction + orientation) follows the TF2 rig convention. For every arms bone that
exists in the viewmodel: angle between the child's local offset in the animation and in the TF2 arms rest
(stock CAR vs ours) -> a bone whose axes follow a different convention (Apex) twists/stretches the mesh."""
import json
import math
import sys
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
a = sys.argv[sys.argv.index("--") + 1:]
anim, frame = a[0], int(a[1])
ab = json.load(open(ROOT + r"\stock\arms\arms_bones.json", encoding="utf-8"))["bones"]


def locals_(d):
    n, f, _ = read_smd(d + "\\" + anim + ".smd")
    fr = f[frame if frame >= 0 else len(f) + frame]
    return {n[i][0]: m for i, m in fr.items()}


S = locals_(ROOT + r"\stock\view\ptpov_car101_anims")
O = locals_(ROOT + r"\build\view\anims")
rows = []
for b in ab:
    nm = b["name"]
    if nm not in S or nm not in O or b["parent"] < 0:
        continue
    rest = Vector(b["pos"])
    if rest.length < 0.3:
        continue
    s, o = S[nm].translation, O[nm].translation
    ds = math.degrees(s.angle(rest)) if s.length > 1e-4 else 0
    do = math.degrees(o.angle(rest)) if o.length > 1e-4 else 0
    rows.append((do, nm, ab[b["parent"]]["name"], ds, rest, o))
rows.sort(reverse=True)
for do, nm, pn, ds, rest, o in rows:
    print(f"AXIS {nm:22s} in {pn:20s} offset dir vs TF2 arms rest: stock {ds:6.1f} deg  ours {do:6.1f} deg"
          f"   rest ({rest.x:5.2f},{rest.y:5.2f},{rest.z:5.2f}) ours ({o.x:5.2f},{o.y:5.2f},{o.z:5.2f})"
          + ("   <<<" if do > 20 else ""))
print("AXES_OK")
