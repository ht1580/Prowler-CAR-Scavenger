"""Side views (z right = forward, y up) of world-model vertex clouds in weapon_bone space, one panel per model,
same scale. Red cross = weapon_bone (the third-person hand), blue rings = IK attachments of that model.
Usage: python -I overlay_world.py <out.png> <label=mdl> [<label=mdl> ...]"""
import struct
import sys
from PIL import Image, ImageDraw


def load(p):
    d = open(p, "rb").read()
    v = d.find(b"IDSV")
    n = struct.unpack_from("<i", d, v + 16)[0]
    s = struct.unpack_from("<i", d, v + 56)[0]
    pts = [struct.unpack_from("<3f", d, v + s + k * 48 + 16) for k in range(n)]
    nb, idx = struct.unpack_from("<2i", d, 160)
    bones = {}
    for k in range(nb):
        r = idx + k * 244
        bones[d[r + struct.unpack_from("<i", d, r)[0]:].split(b"\0")[0].decode()] = struct.unpack_from("<3f", d, r + 32)
    return pts, bones


out = sys.argv[1]
models = [a.split("=", 1) for a in sys.argv[2:]]
S, PW, PH = 34, 1300, 420
img = Image.new("RGB", (PW, PH * len(models)), (28, 28, 32))
dr = ImageDraw.Draw(img)
for row, (label, path) in enumerate(models):
    pts, bones = load(path)
    oy0 = row * PH
    OX, OY = 480, oy0 + 270

    def P(y, z):
        return OX + z * S, OY - y * S

    for z in range(-14, 24, 2):
        dr.line([P(-6, z), P(10, z)], fill=(48, 48, 54))
        dr.text(P(-6.6, z), f"{z}", fill=(90, 90, 100))
    for y in range(-6, 11, 2):
        dr.line([P(y, -14), P(y, 23)], fill=(40, 40, 46))
    for (x, y, z) in pts:
        px, py = P(y, z)
        dr.ellipse((px - 1.2, py - 1.2, px + 1.2, py + 1.2), fill=(235, 150, 50) if row else (170, 170, 170))
    for name in ("l_hand_ik", "r_hand_ik", "muzzle_flash"):
        if name in bones:
            x, y, z = bones[name]
            px, py = P(y, z)
            dr.ellipse((px - 6, py - 6, px + 6, py + 6), outline=(80, 170, 255), width=2)
            dr.text((px + 8, py - 6), name, fill=(80, 170, 255))
    dr.line([P(0, -1.2), P(0, 1.2)], fill=(255, 60, 60), width=3)
    dr.line([P(-1.2, 0), P(1.2, 0)], fill=(255, 60, 60), width=3)
    dr.text((10, oy0 + 8), f"{label}   (red cross = weapon_bone / hand, grid 2 in, z forward)", fill=(230, 230, 230))
img.save(out)
print("OVERLAY_OK", out)
