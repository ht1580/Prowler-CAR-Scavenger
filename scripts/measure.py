"""blender -b -P measure.py : compare stock CAR vs Prowler layout in shared rig space."""
import sys
import json
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name, tri_points, bbox, fmt

V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view"
R = r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\mdl\Weapons\prowler_smg"
rep = {}

# --- CAR rest + meshes
n, f, tris = read_smd(V + r"\v_car101.smd")
rest = by_name(n, globals_(n, f[0]))
base = rest["def_c_base"]
print("CAR def_c_base", fmt(base.translation))
for name in ("v_car101.smd", "v_car101_magazine.smd", "v_car101_sight_on.smd", "v_holo.smd", "v_acgs.smd", "v_cro.smd"):
    _, _, t = read_smd(V + "\\" + name)
    bb = bbox(tri_points(t))
    print(f"CAR {name:24s} min{fmt(bb[0])} max{fmt(bb[1])}")
for bn in ("def_c_magazine", "ja_ads_attachment", "def_c_sight_on", "muzzle_flash", "def_c_trigger", "def_c_holo", "def_c_proscreen"):
    if bn in rest:
        print(f"CAR bone {bn:20s} {fmt(rest[bn].translation)}")

# --- CAR idle hands
n2, f2, _ = read_smd(V + r"\ptpov_car101_anims\idle_seq.smd") if False else (None, None, None)
import glob, os
na, fa, _ = read_smd(V + r"\ptpov_car101_anims\reload_seq.smd")
for fr in (0, 12, 19, 25, 35, 43):
    g = by_name(na, globals_(na, fa[fr]))
    inv = g["def_c_base"].inverted()
    row = []
    for bn in ("def_r_finIndexA", "def_l_finMidA", "def_c_magazine"):
        row.append(bn + fmt(base @ inv @ g[bn].translation))
    print(f"CAR reload f{fr:02d} " + "  ".join(row))

# --- Prowler (R5R base model) meshes
nP, fP, tP = read_smd(R + r"\ptpov_prowler_smg_body_0_lod0.smd")
restP = by_name(nP, globals_(nP, fP[0]))
print("PRW def_c_base", fmt(restP["def_c_base"].translation))
for name in ("ptpov_prowler_smg_body_0_lod0.smd", "ptpov_prowler_smg_clip_0_lod0.smd", "ptpov_prowler_smg_sight_rear_1_lod0.smd"):
    _, _, t = read_smd(R + "\\" + name)
    bb = bbox(tri_points(t))
    print(f"PRW {name:40s} min{fmt(bb[0])} max{fmt(bb[1])}")
for bn in ("def_c_magazine", "ja_ads_attachment", "muzzle_flash", "def_c_trigger", "def_c_holo", "def_c_bolt"):
    if bn in restP:
        print(f"PRW bone {bn:20s} {fmt(restP[bn].translation)}")
