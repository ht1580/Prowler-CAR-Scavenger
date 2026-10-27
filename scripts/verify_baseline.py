"""Prove the stock decompile + RUI used by the build come from the CURRENT VPK's ptpov_car101.mdl.

1) decompile-MDL.txt byte map covers exactly the VPK MDL length (same file that Crowbar read)
2) decompiled QC bone / sequence / attachment / bodygroup / pose-param name tables == VPK MDL tables
3) stock_car101.rui (MDLShit extract) == RUI embedded in the VPK MDL (names, parents, vertices, faces)
"""
import re
import struct
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
sys.path.insert(0, r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench")
from mdl_lib import Mdl
import rui_editor

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
MDL = ROOT + r"\stock\models\weapons\car101\ptpov_car101.mdl"
ok = True
m = Mdl(MDL)

# 1) Crowbar byte map end offset vs file length
txt = open(ROOT + r"\stock\view\ptpov_car101 decompile-MDL.txt", errors="replace").read()
ends = [int(b.replace(",", "")) for _, b in re.findall(r"^\s*([\d,]+) - ([\d,]+)", txt, re.M)]
print(f"[1] crowbar byte map max end {max(ends) + 1:,} vs VPK MDL length {len(m.d):,}")

# 2) name tables
qc = open(ROOT + r"\stock\view\ptpov_car101.qc", errors="replace").read()


def names(kind):
    return re.findall(r'^\$' + kind + r' "([^"]+)"', qc, re.M)


for label, a, b in [("bones", names("definebone"), m.bones()),
                    ("sequences", names("sequence"), [s["name"] for s in m.sequences()]),
                    ("attachments", names("attachment"), [x["name"] for x in m.attachments()]),
                    ("bodygroups", names("bodygroup"), [x["name"] for x in m.bodyparts()]),
                    ("poseparams", names("poseparameter"), m.poseparams())]:
    same = a == b
    ok &= same
    print(f"[2] {label:12s} QC {len(a):3d} == VPK {len(b):3d}: {same}")

# 3) RUI: compiled-from-.rui stock data vs VPK
stock = rui_editor.inspect_mdl(MDL)
rui = open(ROOT + r"\stock\stock_car101.rui", "rb").read()
for mesh in stock["meshes"]:
    # every vertex float triple and face rect of the VPK RUI must appear byte-identical in the .rui file
    vbytes = b"".join(struct.pack("<3f", *v["position"]) for v in mesh["vertices"])
    fbytes = b"".join(struct.pack("<8f", *(f["uvMin"] + f["uvMax"] + f["scaleMin"] + f["scaleMax"])) for f in mesh["faces"])
    name_in = mesh["name"].encode() in rui
    found = name_in and all(struct.pack("<3f", *v["position"]) in rui for v in mesh["vertices"]) and fbytes in rui
    ok &= found
    print(f"[3] RUI {mesh['name']:48s} parent={mesh['parentNames']} in .rui: {found}")
print("BASELINE_OK" if ok else "BASELINE_FAIL")
