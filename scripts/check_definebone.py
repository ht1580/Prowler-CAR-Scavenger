"""blender -b -P : compare QC $definebone rotation values with SMD bind euler for a few bones."""
import sys, re, math
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd
V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view"
n, f, _ = read_smd(V + r"\v_car101.smd")
qc = open(V + r"\ptpov_car101.qc").read()
for name in ("def_l_clav", "def_l_shoulder", "def_r_elbow", "muzzle_flash", "def_l_wrist"):
    i = [k for k, (nm, p) in n.items() if nm == name][0]
    m = f[0][i]
    e = [math.degrees(a) for a in m.to_euler("XYZ")]
    t = list(m.to_translation())
    q = re.search(r'\$definebone "' + name + r'" "[^"]*" ([-\d. e]+)', qc).group(1).split()
    print(name, "smd t", [round(x, 3) for x in t], "smd eulerXYZ deg", [round(x, 3) for x in e], "| qc", q[:6])
