"""Max +x (player-facing left side) body surface around given (y,z) points of the Prowler body SMD."""
import sys
body = r"D:\TitanfallMods\35_ProwlerCAR\build\view\prowler_body.smd"
pts = []
lines = open(body).read().splitlines()
i = lines.index("triangles") + 1
while lines[i] != "end":
    for k in range(1, 4):
        p = lines[i + k].split()
        pts.append((float(p[1]), float(p[2]), float(p[3])))
    i += 4
for (y, z, r) in [(46.8, 0.0, 0.5), (46.4, -0.4, 0.5), (47.2, 0.5, 0.5), (46.0, 0.6, 0.5)]:
    near = [p for p in pts if abs(p[1] - y) < r and abs(p[2] - z) < r]
    mx = max((p[0] for p in near), default=None)
    print(f"y={y} z={z} r={r}: n={len(near)} max_x={mx}")

