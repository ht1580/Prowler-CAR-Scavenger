"""python -I mesh_bone_usage.py <smd>... : per material, how many triangle vertices are skinned to which bone
group. A weapon mesh must only use gun bones (def_c_* / weapon parts); vertices on arm/hand/body bones mean
a stray hand/arm mesh inside the gun model."""
import re
import sys
from collections import Counter, defaultdict

for path in sys.argv[1:]:
    lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    a = lines.index("nodes")
    names = {}
    for s in lines[a + 1:lines.index("end", a)]:
        m = re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)', s)
        if m:
            names[int(m[1])] = m[2]
    i = lines.index("triangles") + 1
    per = defaultdict(Counter)
    while i < len(lines) and lines[i].strip() != "end":
        mat = lines[i].strip()
        for k in range(1, 4):
            t = lines[i + k].split()
            links = [int(t[10 + 2 * j]) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [int(t[0])]
            for b in links:
                nm = names[b]
                grp = "ARM/HAND/BODY" if re.match(r"def_[lr]_|def_c_(hip|spine|neck|head)|ja_[lr]_", nm) else nm
                per[mat][grp] += 1
        i += 4
    print("FILE", path)
    for mat, c in per.items():
        bad = c.get("ARM/HAND/BODY", 0)
        print(f"  {mat:50s} {sum(c.values()):7d} vertex-links  arm/hand/body {bad:6d}  top {c.most_common(4)}")
