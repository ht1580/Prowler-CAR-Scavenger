"""blender -b --factory-startup -P spinner_pivot.py : for every bone that spins in the fire delta, the
vertices skinned to it expressed in that bone's space: centroid off the spin axis (local Z) and radius.
A pivot that is off the part's centre makes the part orbit ("fly") when it turns."""
import math
import sys
from mathutils import Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
SPIN = ("def_c_reactive_spinner_coils", "def_c_reactive_spinner_1", "def_c_reactive_spinner_2")
for path in (ROOT + r"\build\view\prowler_body.smd", ROOT + r"\build\view\prowler_glow.smd"):
    n, f, _ = read_smd(path)
    bind = by_name(n, globals_(n, f[0]))
    idn = {i: nm for i, (nm, _) in n.items()}
    lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    i = lines.index("triangles") + 1
    pts = {b: [] for b in SPIN}
    mixed = {b: 0 for b in SPIN}
    while i < len(lines) and lines[i].strip() != "end":
        for k in range(1, 4):
            t = lines[i + k].split()
            p = Vector((float(t[1]), float(t[2]), float(t[3])))
            links = [(idn[int(t[10 + 2 * j])], float(t[11 + 2 * j])) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [(idn[int(t[0])], 1.0)]
            for nm, w in links:
                if nm in SPIN:
                    if w < 0.999:
                        mixed[nm] += 1
                    pts[nm].append(bind[nm].inverted() @ p)
        i += 4
    for b in SPIN:
        if not pts[b]:
            continue
        c = sum(pts[b], Vector()) / len(pts[b])
        rmax = max(math.hypot(p.x, p.y) for p in pts[b])
        zr = (min(p.z for p in pts[b]), max(p.z for p in pts[b]))
        print(f"PIVOT {path.split(chr(92))[-1]:18s} {b:30s} verts {len(pts[b]):5d} partial-weight {mixed[b]:4d} "
              f"centroid off-axis {math.hypot(c.x, c.y):6.3f} (x {c.x:6.3f} y {c.y:6.3f}) radius {rmax:6.2f} z [{zr[0]:6.2f},{zr[1]:6.2f}]")
print("PIVOT_OK")
