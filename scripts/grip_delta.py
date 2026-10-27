"""blender -b --factory-startup -P grip_delta.py
How the hand holds each gun, from their own first-person idle poses (both rigs share Respawn bone names):
  H_car = inv(def_c_base) @ ja_r_propHand   (CAR held by CAR anim)
  H_prw = inv(def_c_base) @ ja_r_propHand   (Prowler held by Apex anim)
The third-person hand holds weapon_bone like the CAR, so to reproduce the Apex grip the world mesh needs
  T = H_car @ inv(H_prw)  (applied in def_c_base space).  Prints T as translation + euler, and the
left-hand (support) props for both, to re-target the support-hand IK attachment."""
import sys
import math
import json
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

CAR = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims\reload_seq.smd"
PRW = r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg\ptpov_prowler_smg_reload_01_dmx__4C976C7A.smd"


def hands(path):
    n, f, _ = read_smd(path)
    g = by_name(n, globals_(n, f[0]))
    ib = g["def_c_base"].inverted()
    return {k: ib @ g[k] for k in ("ja_r_propHand", "ja_l_propHand", "def_r_wrist", "def_l_wrist") if k in g}


c, p = hands(CAR), hands(PRW)
for name in c:
    tc, tp = c[name].to_translation(), p[name].to_translation()
    ec = [round(math.degrees(a), 1) for a in c[name].to_euler("XYZ")]
    ep = [round(math.degrees(a), 1) for a in p[name].to_euler("XYZ")]
    print(f"{name:14s} CAR pos({tc.x:6.2f},{tc.y:6.2f},{tc.z:6.2f}) rot{ec}   PRW pos({tp.x:6.2f},{tp.y:6.2f},{tp.z:6.2f}) rot{ep}")
T = c["ja_r_propHand"] @ p["ja_r_propHand"].inverted()
t = T.to_translation()
e = [math.degrees(a) for a in T.to_euler("XYZ")]
print(f"T (apply to Prowler world mesh in def_c_base space): move ({t.x:.3f},{t.y:.3f},{t.z:.3f}) rotXYZ ({e[0]:.2f},{e[1]:.2f},{e[2]:.2f}) deg")
json.dump({"T": [list(r) for r in T], "car": {k: [list(r) for r in m] for k, m in c.items()},
           "prw": {k: [list(r) for r in m] for k, m in p.items()}},
          open(r"D:\TitanfallMods\35_ProwlerCAR\build\grip_delta.json", "w"), indent=1)
print("GRIP_OK")
