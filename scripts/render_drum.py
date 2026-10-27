"""blender -b blend/prowler_car_view_rig.blend -P render_drum.py : close-ups of the coil drum on the
first-person hip pose while it turns (same rotation the fire delta applies), seen along its axis and from
the side. If the bone pivot/axis or the skinning were off the drum would orbit / leave its frame."""
import math
import sys
import bpy
from mathutils import Matrix
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
arm = bpy.data.objects["ptpov_car101_merged_armature"]
sc = bpy.context.scene
act = bpy.data.actions["draw_seq"]
arm.animation_data.action = act
if hasattr(arm.animation_data, "action_slot") and act.slots:
    arm.animation_data.action_slot = act.slots[0]
n, f, _ = read_smd(ROOT + r"\build\view\anims\draw_seq.smd")
g = by_name(n, globals_(n, f[-1]))
SPIN = {"def_c_reactive_spinner_coils": 1.0, "def_c_reactive_spinner_1": -2.0, "def_c_reactive_spinner_2": 2.0}
coil = g["def_c_reactive_spinner_coils"]
axis = coil.to_3x3().col[2].normalized()
up = g["def_c_base"].to_3x3().col[1].normalized()
cam = bpy.data.objects.new("drum_cam", bpy.data.cameras.new("drum_cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.clip_start = 0.01
sc.render.resolution_x, sc.render.resolution_y = 640, 640
views = {
    # looking backwards along the drum axis from in front of it (muzzle side)
    "axis": (coil.translation + axis * 12, -axis, up, 4.0),
    # from the gun's right side
    "side": (coil.translation + axis.cross(up).normalized() * -12 + axis * -0.5, axis.cross(up).normalized(), up, 7.0),
}
for k, turn in enumerate((0.0, 1 / 6, 1 / 3, 1 / 2)):
    sc.frame_set(int(act.frame_range[1]))
    for b, rate in SPIN.items():
        pb = arm.pose.bones[b]
        piv, ax = g[b].translation, g[b].to_3x3().col[2].normalized()
        pb.matrix = Matrix.Translation(piv) @ Matrix.Rotation(turn * rate * 2 * math.pi, 4, ax) @ Matrix.Translation(-piv) @ pb.matrix
    bpy.context.view_layer.update()
    for tag, (pos, look, upv, scale) in views.items():
        back = -look
        right = upv.cross(back).normalized()
        upo = back.cross(right).normalized()
        cam.matrix_world = Matrix.Translation(pos) @ Matrix((right, upo, back)).transposed().to_4x4()
        cam.data.ortho_scale = scale
        sc.render.filepath = ROOT + rf"\previews\drum_{tag}_{k}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDER_OK turn", turn)
print("DRUM_RENDER_OK")
