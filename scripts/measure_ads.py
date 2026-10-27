"""blender -b -P measure_ads.py : camera-relative sight/base positions at end of ADS-in for CAR and Prowler."""
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name, fmt

V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims"
P = r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg"
cases = [("CAR ads_in last", V + r"\ads_in_anim.smd", -1), ("CAR ads_in first", V + r"\ads_in_anim.smd", 0),
         ("CAR reload f0", V + r"\reload_seq.smd", 0),
         ("PRW ads_in last", P + r"\ptpov_prowler_smg_ads_in_dmx__1C9BD1BA.smd", -1),
         ("PRW ads_in first", P + r"\ptpov_prowler_smg_ads_in_dmx__1C9BD1BA.smd", 0),
         ("PRW reload f0", P + r"\ptpov_prowler_smg_reload_01_dmx__4C976C7A.smd", 0)]
for label, path, fr in cases:
    n, f, _ = read_smd(path)
    g = by_name(n, globals_(n, f[fr]))
    cam = g["jx_c_camera"]
    ci = cam.inverted()
    row = [f"n={len(f)}", "delta" + fmt(g["jx_c_delta"].translation), "cam" + fmt(cam.translation),
           "camRot" + fmt(cam.to_euler()) ]
    for bn in ("def_c_base", "ja_ads_attachment", "def_c_sight_on", "def_r_finIndexA", "def_l_finMidA"):
        if bn in g:
            row.append(bn + "@cam" + fmt(ci @ g[bn].translation))
    print(f"{label:18s} " + " ".join(row))
