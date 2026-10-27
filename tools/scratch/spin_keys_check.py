import json
import math
from mathutils import Euler, Vector

d = json.load(open(r"D:\TitanfallMods\35_ProwlerCAR\build\native-view-all.json", encoding="utf-8"))
names = [b["name"] for b in d["bones"]]
want = ("def_c_reactive_spinner_coils", "def_c_reactive_spinner_1", "def_c_reactive_spinner_2")
for p in d["poses"]:
    if "spin" not in p["name"] or p["frame"] != 0:
        continue
    loc = {names[v["index"]]: v for v in p["locals"]}
    out = []
    for b in want:
        v = loc.get(b)
        if v is None:
            out.append(f"{b[-5:]}: none")
            continue
        q = Euler(v["rot"], "XYZ").to_quaternion()
        ang = math.degrees(2 * math.atan2(Vector((q.x, q.y, q.z)).dot(Vector((0, 0, 1))), q.w))
        off = math.degrees(Vector((q.x, q.y)).length * 2)
        out.append(f"{b[-5:]}: z {ang:7.1f} off-axis {off:4.2f} pos {max(map(abs, v['pos'])):.4f}")
    others = [n for n, v in loc.items() if n not in want and (max(map(abs, v["pos"])) > 1e-4 or max(map(abs, v["rot"])) > 1e-4)]
    print(f"{p['name']:28s} " + " | ".join(out) + f" | other bones moved: {others[:4]}")
