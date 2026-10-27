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
    c = Counter()
    box = defaultdict(lambda: [[1e9] * 3, [-1e9] * 3])
    while i < len(lines) and lines[i].strip() != "end":
        for k in range(1, 4):
            t = lines[i + k].split()
            links = [(names[int(t[10 + 2 * j])], float(t[11 + 2 * j])) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [(names[int(t[0])], 1.0)]
            dom = max(links, key=lambda x: x[1])[0]
            c[dom] += 1
            p = [float(x) for x in t[1:4]]
            bb = box[dom]
            for j in range(3):
                bb[0][j] = min(bb[0][j], p[j])
                bb[1][j] = max(bb[1][j], p[j])
        i += 4
    print("FILE", path)
    for n, k in c.most_common():
        bb = box[n]
        print(f"  {n:34s} {k:6d}  x[{bb[0][0]:6.2f},{bb[1][0]:6.2f}] y[{bb[0][1]:6.2f},{bb[1][1]:6.2f}] z[{bb[0][2]:6.2f},{bb[1][2]:6.2f}]")
