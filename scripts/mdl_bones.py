"""Dump v53 bone rest data (parent, pos, quat, euler) from an MDL. Layout follows mstudiobone_t:
sznameindex@0 parent@4 bonecontroller[6]@8 pos@32 quat@44 rot(RadianEuler)@60. Stride 244 (calibrated).
Usage: python -I mdl_bones.py <mdl> [bone names...]"""
import math
import struct
import sys

d = open(sys.argv[1], "rb").read()
n, idx = struct.unpack_from("<2i", d, 160)
want = set(sys.argv[2:])
names = []
for k in range(n):
    r = idx + k * 244
    names.append(d[r + struct.unpack_from("<i", d, r)[0]:].split(b"\0")[0].decode())
for k in range(n):
    r = idx + k * 244
    parent = struct.unpack_from("<i", d, r + 4)[0]
    pos = struct.unpack_from("<3f", d, r + 32)
    quat = struct.unpack_from("<4f", d, r + 44)
    rot = struct.unpack_from("<3f", d, r + 60)
    if not want or names[k] in want:
        print(f"{k:3d} {names[k]:24s} parent={names[parent] if parent >= 0 else '-':18s} "
              f"pos=({pos[0]:8.3f},{pos[1]:8.3f},{pos[2]:8.3f}) rotdeg=({', '.join(f'{math.degrees(a):8.2f}' for a in rot)}) "
              f"quat=({', '.join(f'{q:6.3f}' for q in quat)})")
