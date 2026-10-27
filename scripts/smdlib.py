"""Minimal SMD reader/writer + pose helpers (run inside Blender for mathutils)."""
import math
import re
from mathutils import Matrix, Vector, Euler


def read_smd(path):
    """Returns (nodes{idx:(name,parent)}, frames[list of {idx: Matrix local}], triangles list)."""
    lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    a = lines.index("nodes")
    b = lines.index("end", a)
    nodes = {}
    for s in lines[a + 1:b]:
        m = re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)', s)
        if m:
            nodes[int(m[1])] = (m[2], int(m[3]))
    a = lines.index("skeleton", b)
    b = lines.index("end", a)
    frames = []
    for row in lines[a + 1:b]:
        t = row.split()
        if not t:
            continue
        if t[0] == "time":
            frames.append({})
            continue
        v = list(map(float, t[1:7]))
        frames[-1][int(t[0])] = Matrix.Translation(Vector(v[:3])) @ Euler(v[3:], "XYZ").to_matrix().to_4x4()
    tris = []
    if "triangles" in lines[b:]:
        i = lines.index("triangles", b) + 1
        while i < len(lines) and lines[i].strip() != "end":
            mat = lines[i].strip()
            verts = []
            for k in range(1, 4):
                p = lines[i + k].split()
                verts.append(p)
            tris.append((mat, verts))
            i += 4
    return nodes, frames, tris


def globals_(nodes, local):
    out = {}

    def g(i):
        if i not in out:
            par = nodes[i][1]
            out[i] = (g(par) if par >= 0 else Matrix.Identity(4)) @ local.get(i, Matrix.Identity(4))
        return out[i]

    for i in nodes:
        g(i)
    return out


def by_name(nodes, mats):
    return {nodes[i][0]: m for i, m in mats.items()}


def tri_points(tris, mat_filter=None):
    pts = []
    for mat, verts in tris:
        if mat_filter and not mat_filter(mat):
            continue
        for p in verts:
            pts.append(Vector((float(p[1]), float(p[2]), float(p[3]))))
    return pts


def bbox(pts):
    if not pts:
        return None
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def fmt(v):
    return "(" + ", ".join(f"{x:.2f}" for x in v) + ")"
