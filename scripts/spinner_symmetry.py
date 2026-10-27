"""blender -b --factory-startup -P spinner_symmetry.py : for each reactive spinner bone, the vertices it
drives and their rotational symmetry about the gun's forward axis through the bone. A per-shot turn of
360/k (k = symmetry order) restarts every shot without a visible snap."""
import math
import sys
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

P = r"D:\TitanfallMods\35_ProwlerCAR\build\view\prowler_body.smd"
n, f, tris = read_smd(P)
rest = by_name(n, globals_(n, f[0]))
ids = {nm: i for i, (nm, p) in n.items()}
lines = open(P).read().splitlines()
pts = {}
for line in lines[lines.index("triangles") + 1:]:
    t = line.split()
    if len(t) < 10 or not t[0].lstrip("-").isdigit():
        continue
    links = int(t[9])
    pairs = [(int(t[10 + 2 * k]), float(t[11 + 2 * k])) for k in range(links)] if links else [(int(t[0]), 1.0)]
    b, w = max(pairs, key=lambda x: x[1])
    pts.setdefault(b, set()).add(tuple(round(float(v), 4) for v in t[1:4]))
for name in ("def_c_reactive_spinner_coils", "def_c_reactive_spinner_1", "def_c_reactive_spinner_2"):
    if name not in ids or ids[name] not in pts:
        print("SYM", name, "no vertices")
        continue
    g = rest[name]
    axis = Vector((0, 0, 1))                              # gun forward (build_view SPIN_BONES axis)
    c = g.translation
    v = [Vector(p) for p in pts[ids[name]]]
    zs = [p.z for p in v]
    r = [((p - c) - axis * (p - c).dot(axis)).length for p in v]
    kd = KDTree(len(v))
    for i, p in enumerate(v):
        kd.insert(p, i)
    kd.balance()
    scores = {}
    for k in range(2, 17):
        R = Matrix.Translation(c) @ Matrix.Rotation(2 * math.pi / k, 4, axis) @ Matrix.Translation(-c)
        d = [kd.find(R @ p)[2] for p in v[:: max(1, len(v) // 1500)]]
        scores[k] = sum(d) / len(d)
    best = sorted(scores.items(), key=lambda x: x[1])[:5]
    print(f"SYM {name:30s} verts={len(v):6d} pivot=({c.x:.2f},{c.y:.2f},{c.z:.2f}) z[{min(zs):.2f},{max(zs):.2f}] "
          f"radius max {max(r):.2f}  best k: " + ", ".join(f"{k}:{s:.3f}" for k, s in best))
print("SYM_OK")
