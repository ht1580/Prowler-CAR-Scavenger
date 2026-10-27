import sys, bpy, addon_utils
from mathutils import Matrix
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name
VIEW = r"D:\TitanfallMods\35_ProwlerCAR\build\view"
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_valvesource", default_set=False)
bpy.ops.import_scene.smd(filepath=VIEW + r"\ptpov_car101.qc", doAnim=False)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
print("DBG arm matrix", [list(map(lambda x: round(x, 3), r)) for r in arm.matrix_world])
n, f, _ = read_smd(VIEW + r"\prowler_body.smd")
g = by_name(n, globals_(n, f[0]))
for b in ("jx_c_delta", "def_c_base", "jx_c_camera", "def_r_wrist"):
    print("DBG rest", b, "blender", tuple(round(x, 2) for x in arm.matrix_world @ arm.data.bones[b].head_local), "smd", tuple(round(x, 2) for x in g[b].translation))
bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True); bpy.context.view_layer.objects.active = arm
bpy.ops.import_scene.smd(filepath=VIEW + r"\anims\draw_seq.smd")
act = arm.animation_data.action
print("DBG action", act.name, act.frame_range, bpy.context.scene.frame_start, bpy.context.scene.frame_end)
n, f, _ = read_smd(VIEW + r"\anims\draw_seq.smd")
print("DBG smd frames", len(f))
for fr in (0, len(f) - 1):
    g = by_name(n, globals_(n, f[fr]))
    for off in (0, 1):
        bpy.context.scene.frame_set(fr + off)
        bpy.context.view_layer.update()
        d = {b: round(((arm.matrix_world @ arm.pose.bones[b].head) - g[b].translation).length, 3) for b in ("jx_c_delta", "def_c_base", "jx_c_camera")}
        print("DBG frame", fr, "+", off, d, "blender jx_c_delta", tuple(round(x, 2) for x in arm.matrix_world @ arm.pose.bones["jx_c_delta"].head), "smd", tuple(round(x, 2) for x in g["jx_c_delta"].translation))
