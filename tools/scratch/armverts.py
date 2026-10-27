import re
import sys
from collections import Counter

path = r"D:\TitanfallMods\35_ProwlerCAR\build\view\prowler_body.smd"
lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
a = lines.index("nodes")
names = {}
for s in lines[a + 1:lines.index("end", a)]:
    m = re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)', s)
    if m:
        names[int(m[1])] = m[2]
i = lines.index("triangles") + 1
c = Counter()
combos = Counter()
pts = {}
while i < len(lines) and lines[i].strip() != "end":
    for k in range(1, 4):
        t = lines[i + k].split()
        links = [(names[int(t[10 + 2 * j])], float(t[11 + 2 * j])) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [(names[int(t[0])], 1.0)]
        bad = [(n, w) for n, w in links if re.match(r"def_[lr]_|def_c_(hip|spine|neck|head)|ja_[lr]_", n)]
        if bad:
            for n, w in bad:
                c[n] += 1
                pts.setdefault(n, []).append(tuple(float(x) for x in t[1:4]))
            combos[" + ".join(f"{n}:{w:.2f}" for n, w in sorted(links))[:120]] += 1
    i += 4
for n, k in c.most_common():
    p = pts[n]
    mn = [min(q[j] for q in p) for j in range(3)]
    mx = [max(q[j] for q in p) for j in range(3)]
    print(f"{n:24s} {k:5d} links  bbox x[{mn[0]:6.2f},{mx[0]:6.2f}] y[{mn[1]:6.2f},{mx[1]:6.2f}] z[{mn[2]:6.2f},{mx[2]:6.2f}]")
print("--- weight combos")
for s, k in combos.most_common(12):
    print(k, s)
