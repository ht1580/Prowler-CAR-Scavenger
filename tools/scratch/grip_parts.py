"""Which bones the gun-mesh vertices nearest to each hand (hip pose) are skinned to."""
import re
import sys
from collections import Counter
from mathutils import Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR\build\view"
n, f, _ = read_smd(ROOT + r"\anims\draw_seq.smd")
g = by_name(n, globals_(n, f[-1]))
mn, mf, _ = read_smd(ROOT + r"\prowler_body.smd")
bind = by_name(mn, globals_(mn, mf[0]))
idn = {i: nm for i, (nm, _) in mn.items()}
lines = open(ROOT + r"\prowler_body.smd", encoding="utf-8-sig").read().splitlines()
i = lines.index("triangles") + 1
verts = []
while i < len(lines) and lines[i].strip() != "end":
    for k in range(1, 4):
        t = lines[i + k].split()
        p = Vector((float(t[1]), float(t[2]), float(t[3])))
        links = [(idn[int(t[10 + 2 * j])], float(t[11 + 2 * j])) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [(idn[int(t[0])], 1.0)]
        dom = max(links, key=lambda x: x[1])[0]
        world = sum(((g[b] @ bind[b].inverted() @ p) * w for b, w in links if b in g), Vector())
        verts.append((world, dom))
    i += 4
for hand in ("def_l_finMidA", "def_r_finMidA", "def_l_wrist", "def_r_wrist"):
    h = g[hand].translation
    near = sorted(verts, key=lambda v: (v[0] - h).length)[:400]
    print(hand, Counter(d for _, d in near).most_common(5), f"nearest {(near[0][0] - h).length:.2f}")
