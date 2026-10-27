"""Compare CAR delta idle frame vs absolute reload frame vs bind for a few arm bones (local values)."""
import re
V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view"


def frame0(path, idx_names):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    nodes = {}
    for s in lines[lines.index("nodes") + 1:]:
        if s.strip() == "end":
            break
        m = re.match(r'\s*(\d+)\s+"([^"]+)"', s)
        nodes[m[2]] = int(m[1])
    out = {}
    started = False
    for s in lines[lines.index("skeleton"):]:
        t = s.split()
        if not t:
            continue
        if t[0] == "time":
            if started:
                break
            started = True
            continue
        if started and t[0].isdigit():
            for nm in idx_names:
                if int(t[0]) == nodes.get(nm, -1):
                    out[nm] = [round(float(x), 3) for x in t[1:7]]
    return out


bones = ["def_l_shoulder", "def_l_elbow", "def_l_wrist", "def_r_shoulder", "def_r_elbow", "ja_c_propGun", "def_c_base"]
for lbl, f in [("bind", "v_car101.smd"), ("idle_anim(delta)", r"ptpov_car101_anims\idle_anim.smd"),
               ("reload f0(abs)", r"ptpov_car101_anims\reload_seq.smd"), ("draw f0(abs)", r"ptpov_car101_anims\draw_seq.smd"),
               ("ads_in(abs?)", r"ptpov_car101_anims\ads_in_anim.smd")]:
    d = frame0(V + "\\" + f, bones)
    print(f"== {lbl}")
    for b in bones:
        print(f"   {b:16s} {d.get(b)}")
