import json
import math
import sys
from mathutils import Euler, Vector

d = json.load(open(r"D:\TitanfallMods\35_ProwlerCAR\build\native-all-at_draw_seq.json", encoding="utf-8"))
bones = d["bones"]
names = [b["name"] for b in bones]
bp = max(d["poses"], key=lambda p: p["frame"])
loc = {v["index"]: v for v in bp["locals"]}
for nm in ("def_c_reactive_spinner_coils", "def_c_reactive_spinner_1", "def_c_reactive_spinner_2", "def_c_reactive_spring_2", "def_c_bolt", "def_c_magazine"):
    if nm not in names:
        continue
    i = names.index(nm)
    v = loc.get(i, bones[i])
    R = Euler(v["rot"], "XYZ").to_matrix()
    zl = R.col[2]
    ang = math.degrees(zl.angle(Vector((0, 0, 1))))
    print(f"{nm:32s} parent {names[bones[i]['parent']]:28s} local rot deg {[round(math.degrees(x), 1) for x in v['rot']]}  "
          f"rest rot deg {[round(math.degrees(x), 1) for x in bones[i]['rot']]}  local Z vs parent Z {ang:6.1f} deg  pos {[round(x, 2) for x in v['pos']]}")
