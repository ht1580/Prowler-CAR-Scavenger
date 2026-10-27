"""blender -b --factory-startup -P check_hand_on_gun.py : right hand / trigger finger in def_c_base space,
stock CAR vs ours, for the hip-hold frames (draw end, ads_in start). Compare against the mesh extents
(mdl_vvd_bbox) to see where along the gun the hand grips."""
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

STOCK = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims"
OURS = r"D:\TitanfallMods\35_ProwlerCAR\build\view\anims"
for fn, fi in (("draw_seq.smd", -1), ("ads_in_anim.smd", 0), ("ads_in_anim.smd", -1), ("sprint_seq.smd", 0)):
    for label, d in (("stock", STOCK), ("ours ", OURS)):
        n, f, _ = read_smd(d + "\\" + fn)
        g = by_name(n, globals_(n, f[fi if fi >= 0 else len(f) + fi]))
        bi = g["def_c_base"].inverted()
        out = []
        for b in ("ja_r_propHand", "def_r_finIndexA", "def_r_wrist", "def_l_wrist", "ja_l_propHand"):
            if b in g:
                v = bi @ g[b].translation
                out.append(f"{b}=({v.x:6.2f},{v.y:6.2f},{v.z:6.2f})")
        print(f"HAND {fn:16s} f{fi:+d} {label} " + "  ".join(out))
print("HAND_OK")
