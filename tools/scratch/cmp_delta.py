"""Compare decoded per-bone local values of delta animations: ours vs stock CAR (shared bone names)."""
import json
import math
import sys
from mathutils import Euler, Quaternion

sys.argv = sys.argv[sys.argv.index("--"):]
ours = json.load(open(sys.argv[1], encoding="utf-8"))
stock = json.load(open(sys.argv[2], encoding="utf-8"))


def table(d):
    names = [b["name"] for b in d["bones"]]
    out = {}
    for p in d["poses"]:
        out[(p["name"], p["frame"])] = (p["flags"], {names[l["index"]]: l for l in p["locals"]})
    return names, out


on, op = table(ours)
sn, sp = table(stock)


def ang(rot):
    return math.degrees(Euler(rot, "XYZ").to_quaternion().angle)


def mag(v):
    return math.sqrt(sum(x * x for x in v))


rows = []
for key, (flags, ob) in op.items():
    if key not in sp:
        continue
    sflags, sb = sp[key]
    delta = bool(flags & 4)
    for nm in ob:
        if nm not in sb:
            continue
        o, s = ob[nm], sb[nm]
        if delta:
            da = abs(ang(o["rot"]) - ang(s["rot"]))
            dp = abs(mag(o["pos"]) - mag(s["pos"]))
            rows.append((da + dp, key, nm, ang(o["rot"]), ang(s["rot"]), mag(o["pos"]), mag(s["pos"]), "delta"))
filt = sys.argv[3] if len(sys.argv) > 3 else ""
rows.sort(key=lambda r: -r[0])
print("delta anims compared:", len({r[1][0] for r in rows}))
for r in rows[:60]:
    if filt and filt not in r[1][0]:
        continue
    print(f"{r[1][0]:34s} f{r[1][1]:<3d} {r[2]:28s} rot ours {r[3]:7.2f} stock {r[4]:7.2f}  pos ours {r[5]:7.3f} stock {r[6]:7.3f}")
