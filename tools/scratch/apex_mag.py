import glob
import math
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

for pat in ("ptpov_prowler_smg_reload_empty_01_dmx__7E41644.smd", "ptpov_prowler_smg_reload_01_dmx__4C976C7A.smd"):
    path = glob.glob(r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg\\" + pat)[0]
    n, f, _ = read_smd(path)
    print("APEX", path.split("\\")[-1], "frames", len(f))
    for fi in range(0, len(f), 4):
        g = by_name(n, globals_(n, f[fi]))
        c = g["jx_c_camera"].inverted()
        m = c @ g["def_c_magazine"].translation
        w = c @ g["def_l_wrist"].translation
        b = c @ g["def_c_base"].translation
        # angle off the view axis (camera +Z forward): horizontal / vertical degrees
        def ang(v):
            return (math.degrees(math.atan2(v.x, v.z)) if v.z > 0 else 999, math.degrees(math.atan2(v.y, v.z)) if v.z > 0 else 999)
        ma, wa = ang(m), ang(w)
        print(f"  f{fi:3d} mag cam({m.x:6.1f},{m.y:6.1f},{m.z:6.1f}) ang({ma[0]:5.0f},{ma[1]:5.0f}) | Lhand ({w.x:6.1f},{w.y:6.1f},{w.z:6.1f}) ang({wa[0]:5.0f},{wa[1]:5.0f}) | hand-mag {(g['def_l_wrist'].translation - g['def_c_magazine'].translation).length:5.1f} gun-mag {(g['def_c_base'].translation - g['def_c_magazine'].translation).length:5.1f}")
