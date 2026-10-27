"""blender -b -P make_blend.py : import the generated QCs with Blender Source Tools (meshes only) and save
.blend work files (doc step: keep an importable baseline .blend). doAnim=False, createCollections=True."""
import bpy
import addon_utils
import os

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
OUT = ROOT + r"\blend"
os.makedirs(OUT, exist_ok=True)
addon_utils.enable("io_scene_valvesource", default_set=False)
for tag, qc in (("view", ROOT + r"\build\view\ptpov_car101.qc"), ("world", ROOT + r"\build\world\w_car101.qc")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("io_scene_valvesource", default_set=False)
    res = bpy.ops.import_scene.smd(filepath=qc, doAnim=False, createCollections=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    path = OUT + rf"\prowler_car_{tag}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("BLEND_OK", tag, res, "meshes", len(meshes), [o.name for o in meshes][:8],
          "bones", len(arms[0].data.bones) if arms else 0, path)
