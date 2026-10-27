"""Measure generated world SMDs, independent of the world model builder."""
import math
import re
from pathlib import Path

import numpy as np


def snapshot(folder):
    result = {"meshes": {}, "bones": {}}
    for path in sorted(Path(folder).glob("*.smd")):
        lines = path.read_text(encoding="ascii").splitlines()
        if "triangles" not in lines:
            continue
        positions = []
        for line in lines[lines.index("triangles") + 1:]:
            fields = line.split()
            if len(fields) >= 9 and fields[0].isdigit():
                positions.append([float(v) for v in fields[1:4]])
        points = np.array(positions, dtype=np.float64)
        if not len(points):
            raise ValueError(f"No vertices in {path}")
        result["meshes"][path.name] = {
            "count": len(points), "min": points.min(axis=0).tolist(),
            "max": points.max(axis=0).tolist(), "mean": points.mean(axis=0).tolist(),
        }
        if result["bones"]:
            continue
        names, parents = {}, {}
        for line in lines[lines.index("nodes") + 1:lines.index("skeleton") - 1]:
            match = re.fullmatch(r'(\d+) "([^"]+)" (-?\d+)', line.strip())
            if match:
                index, name, parent = match.groups()
                names[int(index)], parents[int(index)] = name, int(parent)
        transforms = {}
        for line in lines[lines.index("time 0") + 1:]:
            if line.strip() == "end":
                break
            fields = line.split()
            if len(fields) != 7:
                continue
            index = int(fields[0])
            x, y, z, rx, ry, rz = map(float, fields[1:])
            cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
            rotation_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
            rotation_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            rotation_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
            local = np.eye(4)
            local[:3, :3] = rotation_z @ rotation_y @ rotation_x
            local[:3, 3] = [x, y, z]
            parent = parents[index]
            transforms[index] = transforms[parent] @ local if parent >= 0 else local
            result["bones"][names[index]] = transforms[index].tolist()
    return result
