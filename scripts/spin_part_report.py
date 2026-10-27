"""blender -b --factory-startup -P spin_part_report.py -- <decoded.json> bone[,bone...]
For each animation that moves the given spinning-part bones: anim flags (delta?), frame count, and the
bone's local rotation angle / axis and translation at the decoded frames (first / mid / last)."""
import json
import math
import sys
from mathutils import Euler, Vector

a = sys.argv[sys.argv.index("--") + 1:]
d = json.load(open(a[0], encoding="utf-8"))
want = a[1].split(",")
names = [b["name"] for b in d["bones"]]
rest = {b["name"]: b for b in d["bones"]}
by_anim = {}
for p in d["poses"]:
    by_anim.setdefault(p["name"], []).append(p)
for an, poses in by_anim.items():
    rows = []
    for p in sorted(poses, key=lambda x: x["frame"]):
        loc = {names[v["index"]]: v for v in p["locals"]}
        for b in want:
            v = loc.get(b)
            if v is None:
                continue
            q = Euler(v["rot"], "XYZ").to_quaternion()
            delta = bool(p["flags"] & 4)
            if not delta:
                q = Euler(rest[b]["rot"], "XYZ").to_quaternion().inverted() @ q     # vs bind
                t = (Vector(v["pos"]) - Vector(rest[b]["pos"])).length
            else:
                t = Vector(v["pos"]).length
            ang = math.degrees(q.angle)
            if ang > 0.5 or t > 0.01:
                ax = q.axis
                rows.append(f"f{p['frame']}/{p['frames']} {b} {ang:6.1f}deg axis({ax.x:4.1f},{ax.y:4.1f},{ax.z:4.1f}) move {t:.2f}")
    if rows:
        print(f"SPIN {an:34s} flags {poses[0]['flags']:#06x} :: " + " | ".join(rows))
print("SPIN_REPORT_OK")
