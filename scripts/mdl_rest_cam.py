"""Where do the gun bones sit relative to jx_c_camera in the MDL bone-table rest pose?
Delta viewmodel sequences (idle/attack/walk) are added on top of this rest pose in game, so it must be
the hip pose. Usage: python -I mdl_rest_cam.py <mdl> [<mdl> ...]"""
import struct
import sys


def qmat(x, y, z, w):
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def mul(a, b):  # rigid transforms as (R, t)
    R = [[sum(a[0][i][k] * b[0][k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    t = [sum(a[0][i][k] * b[1][k] for k in range(3)) + a[1][i] for i in range(3)]
    return R, t


def inv(a):
    Rt = [[a[0][j][i] for j in range(3)] for i in range(3)]
    return Rt, [-sum(Rt[i][k] * a[1][k] for k in range(3)) for i in range(3)]


def rest(path):
    d = open(path, "rb").read()
    n, idx = struct.unpack_from("<2i", d, 160)
    names, g = [], []
    for k in range(n):
        r = idx + k * 244
        names.append(d[r + struct.unpack_from("<i", d, r)[0]:].split(b"\0")[0].decode())
        parent = struct.unpack_from("<i", d, r + 4)[0]
        m = (qmat(*struct.unpack_from("<4f", d, r + 44)), list(struct.unpack_from("<3f", d, r + 32)))
        g.append(mul(g[parent], m) if parent >= 0 else m)
    return dict(zip(names, g))


for p in sys.argv[1:]:
    g = rest(p)
    ci = inv(g["jx_c_camera"])
    print(p)
    for b in ("def_c_base", "def_c_barrel", "def_r_finIndexA", "ja_r_propHand", "def_c_holo"):
        if b in g:
            v = mul(ci, g[b])[1]
            print(f"   {b:18s} @cam = ({v[0]:8.2f},{v[1]:8.2f},{v[2]:8.2f})")
