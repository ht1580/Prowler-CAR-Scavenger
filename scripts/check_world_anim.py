"""Gate: the built world animation must carry the stock root pose (ja_c_propGun) and frame count.
Compares against the native-decoded original CAR baseline (24 frames).
Usage: python -I check_world_anim.py"""
import sys

STOCK = r"D:\TitanfallMods\35_ProwlerCAR\stock\world\world_idle.smd"
BUILT = r"D:\TitanfallMods\35_ProwlerCAR\build\world\world_idle.smd"


def scan(p):
    lines = open(p).read().splitlines()
    nodes = {}
    i = lines.index("nodes") + 1
    while lines[i].strip() != "end":
        k, name = lines[i].split()[:2]
        nodes[int(k)] = name.strip('"')
        i += 1
    frames, cur = [], None
    for l in lines[lines.index("skeleton") + 1:]:
        t = l.split()
        if not t or t[0] == "end":
            continue
        if t[0] == "time":
            cur = {}
            frames.append(cur)
        else:
            cur[nodes[int(t[0])]] = list(map(float, t[1:7]))
    return frames


s, b = scan(STOCK), scan(BUILT)
ok = len(s) == len(b)
for name in ("ja_c_propGun", "weapon_bone", "def_c_base"):
    bad = [f for f in range(min(len(s), len(b))) if max(abs(x - y) for x, y in zip(s[f][name], b[f][name])) > 1e-4]
    ok &= not bad
    print(f"{name:14s} stock {s[0][name]}  built {b[0][name]}  frames differing: {len(bad)}")
print(f"frames stock {len(s)} built {len(b)}")
print("WORLD_ANIM_OK" if ok else "WORLD_ANIM_FAIL")
sys.exit(0 if ok else 1)
