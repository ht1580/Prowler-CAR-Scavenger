"""blender -b -P measure_bind.py : hand positions in CAR vs Prowler bind poses, and delta anim sanity."""
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name, fmt

V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view"
R = r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims"
pairs = [("CAR bind", V + r"\v_car101.smd"),
         ("PRW bind", R + r"\mdl\Weapons\prowler_smg\ptpov_prowler_smg_body_0_lod0.smd"),
         ("PRW ref", R + r"\mdl\Weapons\prowler_smg\anims_ptpov_prowler_smg\ref.smd"),
         ("PRW idle33", R + r"\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg\ptpov_prowler_smg_idle_dmx__33_DCFF7D84.smd"),
         ("PRW reload0", R + r"\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg\ptpov_prowler_smg_reload_01_dmx__4C976C7A.smd")]
for label, p in pairs:
    n, f, _ = read_smd(p)
    g = by_name(n, globals_(n, f[0]))
    b = g.get("def_c_base")
    inv = b.inverted()
    row = [f"frames={len(f)}"]
    for bn in ("def_r_finIndexA", "def_l_finMidA", "def_c_magazine", "jx_c_camera"):
        if bn in g:
            row.append(bn + fmt(inv @ g[bn].translation))
    print(f"{label:12s} base{fmt(b.translation)} " + " ".join(row))
