"""blender -b --factory-startup -P joint_report.py
Joint (jx_) vs deform (def_) vs attachment (ja_) bones in: the stock CAR viewmodel, the Apex Prowler viewmodel
rig, and the reactive-skin rig; which of them the reactive cast mesh is actually weighted to (vertex counts per
vertex group), and how each joint moves in the Apex animations (relative to its parent)."""
import os
import sys
from collections import Counter
import bpy
import addon_utils
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
CAR = ROOT + r"\stock\view\v_car101.smd"
PRW = ROOT + r"\r5r_anims\mdl\Weapons\prowler_smg\ptpov_prowler_smg_body_0_lod0.smd"
REA = ROOT + r"\apex_react\animrig\techart\mshop\weapons\class\smg\prowler\prowler_react_v21_scavenger_v_animRig.smd"
SKIN = os.path.dirname(os.path.dirname(open(ROOT + r"\scripts\build_view.py", encoding="utf-8").read().split('SKIN = r"')[1].split('"')[0] + "\\x"))


def tree(path, label):
    n, f, _ = read_smd(path)
    names = {i: nm for i, (nm, p) in n.items()}
    groups = Counter(nm.split("_")[0] for nm in names.values())
    print(f"TREE {label}: {len(names)} bones, prefixes {dict(groups)}")
    for i, (nm, p) in sorted(n.items()):
        if not nm.startswith(("def_l_", "def_r_", "def_c_hip", "def_c_spine", "def_c_neck", "def_c_head", "jx_c_neckB")) or nm.startswith("def_l_reactive") or nm.startswith("def_r_reactive"):
            if nm.startswith(("jx_", "ja_")) or "reactive" in nm or "spinner" in nm or "bolt" in nm or "mag" in nm or "c_base" in nm:
                print(f"   {nm:34s} <- {names.get(p, '-')}")
    return n


tree(CAR, "stock CAR viewmodel")
tree(PRW, "Apex Prowler viewmodel rig")
tree(REA, "reactive skin rig")

# which groups the reactive cast mesh vertices are weighted to
SKIN_DIR = r"D:\Apex_鐚庡吔杩涘寲鐨甠v21_scavenger"
cast_path = None
for root, _, files in os.walk(SKIN_DIR):
    for fn in files:
        if fn.endswith("LOD0.cast") and "scavenger_v" in fn:
            cast_path = os.path.join(root, fn)
addon_utils.enable("io_scene_cast", default_set=False)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.cast(filepath=cast_path)
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    c = Counter()
    gn = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight)
            c[gn[g.group]] += 1
    print(f"MESH {o.name}: {len(o.data.vertices)} verts, dominant groups:")
    for name, k in c.most_common():
        print(f"   {name:34s} {k:6d}")
print("JOINT_REPORT_OK")
