"""Measure the pistol-grip axis (side view, z forward / y up) of the CAR vs the Prowler from mesh vertices,
in def_c_base space, and draw a zoomed side view of the grip/trigger area of both.

Grip region = vertices below the base point (the hand) inside a window around it; the axis is the principal
component of those vertices in the y-z plane, reported as rake angle from vertical (positive = bottom tilts back).
Usage: python -I grip_axis.py <out.png>"""
import math
import struct
import sys
from PIL import Image, ImageDraw

CAR_V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\v_car101.smd"
PRW_V = r"D:\TitanfallMods\35_ProwlerCAR\build\view\prowler_body.smd"
BASE = (0.0, 43.307, 9.8425)


def smd_points(p):
    lines = open(p, errors="replace").read().splitlines()
    i = lines.index("triangles") + 1
    pts = []
    while i < len(lines) and lines[i] != "end":
        for k in range(1, 4):
            q = lines[i + k].split()
            pts.append((float(q[1]) - BASE[0], float(q[2]) - BASE[1], float(q[3]) - BASE[2]))
        i += 4
    return pts


def axis(pts, zlo, zhi, ylo, yhi):
    sel = [(y, z) for (x, y, z) in pts if zlo <= z <= zhi and ylo <= y <= yhi and abs(x) < 1.3]
    my = sum(y for y, _ in sel) / len(sel)
    mz = sum(z for _, z in sel) / len(sel)
    syy = sum((y - my) ** 2 for y, _ in sel)
    szz = sum((z - mz) ** 2 for _, z in sel)
    syz = sum((y - my) * (z - mz) for y, z in sel)
    ang = 0.5 * math.atan2(2 * syz, syy - szz)          # principal axis angle measured from the y axis
    dy, dz = math.cos(ang), math.sin(ang)
    if dy > 0:
        dy, dz = -dy, -dz                                 # point the axis downward
    rake = math.degrees(math.atan2(-dz, -dy))            # >0: bottom of grip sits behind the top (raked back)
    return len(sel), (my, mz), (dy, dz), rake


out = sys.argv[1]
res = {}
W, H, S = 1300, 650, 58
img = Image.new("RGB", (W, H), (28, 28, 32))
dr = ImageDraw.Draw(img)
for col, (label, path, win) in enumerate((("stock CAR", CAR_V, (-3.0, 1.5, -5.0, 0.2)),
                                          ("Prowler", PRW_V, (-3.0, 1.5, -5.0, 0.2)))):
    pts = smd_points(path)
    n, c, d, rake = axis(pts, *win)
    res[label] = rake
    OX, OY = 300 + col * 650, 300

    def P(y, z):
        return OX + z * S, OY - y * S

    for (x, y, z) in pts:
        if -5 <= z <= 5 and -6 <= y <= 4.5:
            px, py = P(y, z)
            dr.point((px, py), fill=(170, 170, 170) if col == 0 else (235, 150, 50))
    zlo, zhi, ylo, yhi = win
    dr.rectangle([P(yhi, zlo), P(ylo, zhi)], outline=(80, 80, 120))
    a, b = P(c[0] - 3 * d[0], c[1] - 3 * d[1]), P(c[0] + 3 * d[0], c[1] + 3 * d[1])
    dr.line([a, b], fill=(80, 200, 255), width=3)
    dr.line([P(0, -0.5), P(0, 0.5)], fill=(255, 60, 60), width=3)
    dr.line([P(-0.5, 0), P(0.5, 0)], fill=(255, 60, 60), width=3)
    dr.text((OX - 280, 15), f"{label}: grip axis rake {rake:+.1f} deg from vertical (n={n})  forward ->", fill=(230, 230, 230))
img.save(out)
print("GRIP_AXIS", {k: round(v, 1) for k, v in res.items()}, "difference", round(res["Prowler"] - res["stock CAR"], 1))
