"""blender -b --factory-startup -P check_ref.py : where is the gun relative to the camera in the ref sequence?"""
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

for label, p in (("stock ref.smd", r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims\ref.smd"),
                 ("0.1.10 ref.smd (ours)", r"D:\TitanfallMods\35_ProwlerCAR\build\view\anims\ref.smd"),
                 ("CAR ads_in f0 (hip hold)", r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims\ads_in_anim.smd")):
    n, f, _ = read_smd(p)
    g = by_name(n, globals_(n, f[0]))
    ci = g["jx_c_camera"].inverted()
    b = ci @ g["def_c_base"].translation
    r = ci @ g["def_r_finIndexA"].translation if "def_r_finIndexA" in g else None
    print(f"REF {label:28s} def_c_base@cam=({b.x:6.2f},{b.y:6.2f},{b.z:6.2f})  r_index@cam={tuple(round(x, 2) for x in r) if r else None}")
