"""Does every decoded animation keep each reactive drum part seated on the gun?
For each pose: rel = inv(G[def_c_base]) @ G[part], compared with the bone-table rest rel. A seated part
may only rotate about its own spin axis (local Z); any translation or tilt is "misalignment".
Delta layers are checked as layers: their part delta must be a pure local-Z rotation (or identity).
Usage: python -I check_drum_seat.py <decoded.json from decode_native_pose.ps1>"""
import json
import math
import sys

import numpy as np

PARTS = ("def_c_reactive_spinner_coils", "def_c_reactive_spinner_1", "def_c_reactive_spinner_2")


def mat(pos, rot):
    rx, ry, rz = rot
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    m = np.eye(4)
    m[:3, :3] = (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
                 @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))
    m[:3, 3] = pos
    return m


doc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
bones = doc["bones"]
names = [b["name"] for b in bones]
parent_chain = {}
for p in PARTS:
    chain, i = [], names.index(p)
    while i >= 0:
        chain.append(names[i])
        i = bones[i]["parent"]
    parent_chain[p] = chain
    print("CHAIN", p, " <- ".join(chain))


def globals_(locals_):
    g = []
    for i, b in enumerate(bones):
        v = locals_.get(i, b)
        m = mat(v["pos"], v["rot"])
        g.append(g[b["parent"]] @ m if b["parent"] >= 0 else m)
    return g


rest = globals_({})
base = names.index("def_c_base")
rest_rel = {p: np.linalg.inv(rest[base]) @ rest[names.index(p)] for p in PARTS}
bad = 0
for pose in doc["poses"]:
    delta = bool(pose["flags"] & 4)
    loc = {v["index"]: v for v in pose["locals"]}
    for p in PARTS:
        i = names.index(p)
        if delta:
            if i not in loc:
                continue
            d = mat(loc[i]["pos"], loc[i]["rot"])
        else:
            g = globals_(loc)
            d = np.linalg.inv(rest_rel[p]) @ (np.linalg.inv(g[base]) @ g[i])
        shift = float(np.linalg.norm(d[:3, 3]))
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, d[2, 2]))))     # local Z axis must stay put
        if shift > 0.01 or tilt > 0.5:
            bad += 1
            print(f"MISALIGNED {pose['name']:40s} f{pose['frame']:3d} {'delta' if delta else 'abs  '} {p:30s} shift {shift:6.3f} tilt {tilt:6.2f}")
print(f"poses {len(doc['poses'])}  misaligned part-poses {bad}")
print("DRUM_SEAT_OK" if bad == 0 else "DRUM_SEAT_FAIL")
