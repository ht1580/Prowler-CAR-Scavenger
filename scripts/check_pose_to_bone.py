"""blender -b --factory-startup -P check_pose_to_bone.py -- <engine dump json> [<mdl>]
The renderer skins a vertex as  BoneToWorld(anim) * poseToBone * v_bind. poseToBone must be the inverse of
the bone's bind (rest) world matrix; a mismatch offsets everything skinned to that bone even when the
animation is right (nothing in the animation decode shows it). Also checks, with the embedded VVD, that
each spinning part's vertices sit centred on its bone axis in that bone's poseToBone space."""
import json
import math
import struct
import sys
from mathutils import Matrix, Quaternion, Vector

a = sys.argv[sys.argv.index("--") + 1:]
doc = json.load(open(a[0], encoding="utf-8"))
bones = doc["bones"]
G = []
for b in bones:
    q = Quaternion((b["quat"][3], b["quat"][0], b["quat"][1], b["quat"][2]))
    L = Matrix.Translation(Vector(b["pos"])) @ q.to_matrix().to_4x4()
    G.append((G[b["parent"]] if b["parent"] >= 0 else Matrix.Identity(4)) @ L)
worst = []
P2B = []
for i, b in enumerate(bones):
    c = b["p2b"]
    M = Matrix(((c[0][0], c[1][0], c[2][0], c[3][0]),
                (c[0][1], c[1][1], c[2][1], c[3][1]),
                (c[0][2], c[1][2], c[2][2], c[3][2]),
                (0, 0, 0, 1)))
    P2B.append(M)
    E = M @ G[i]                                   # identity when poseToBone == inverse(bind world)
    err_t = E.translation.length
    err_r = math.degrees(E.to_quaternion().angle)
    worst.append((err_t + err_r / 10, b["name"], err_t, err_r))
worst.sort(reverse=True)
print("P2B worst bones (poseToBone @ restWorld should be identity):")
for _, n, t, r in worst[:12]:
    print(f"P2B {n:34s} translation err {t:8.3f}  rotation err {r:7.2f} deg")
bad = [w for w in worst if w[2] > 0.01 or w[3] > 0.1]
print(f"P2B_SUMMARY {len(bad)} of {len(bones)} bones mismatch")

if len(a) > 1:
    d = open(a[1], "rb").read()
    v = d.find(b"IDSV")
    n = struct.unpack_from("<i", d, v + 16)[0]
    vs = struct.unpack_from("<i", d, v + 56)[0]
    names = [b["name"] for b in bones]
    acc = {}
    for k in range(n):
        o = v + vs + k * 48
        w = struct.unpack_from("<3f", d, o)
        bid = struct.unpack_from("<3B", d, o + 12)
        nb = d[o + 15]
        p = Vector(struct.unpack_from("<3f", d, o + 16))
        for j in range(nb):
            if w[j] > 0.5 and "spinner" in names[bid[j]]:
                acc.setdefault(names[bid[j]], []).append(P2B[bid[j]] @ p)
    for nm, pts in acc.items():
        c = sum(pts, Vector()) / len(pts)
        print(f"VVD {nm:32s} verts {len(pts):5d} centroid in bone space ({c.x:6.3f},{c.y:6.3f},{c.z:6.3f}) off-axis {math.hypot(c.x, c.y):.3f}")
print("P2B_OK")
