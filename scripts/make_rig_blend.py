"""blender -b -P make_rig_blend.py : HK560-style Blender project of the built viewmodel + first-person check.
(github.com/HK560/Titanfall2AnimationModTutorial: merged armature, meshes bound with Armature modifiers,
animations as actions, camera parented to jx_c_camera, "check the model follows the bones" in pose mode.)

Saves blend/prowler_car_view_rig.blend and renders previews/fp_*.png from the in-game camera bone:
textured gun + the hand/finger bones drawn as a stick skeleton (no arms mesh is extracted), for
hip / ADS / reload frames and the per-shot drum turn. Prints CHECK lines comparing the Blender pose with
the SMD data (the armature must reproduce the animation exactly)."""
import math
import sys
import bpy
import addon_utils
from mathutils import Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
VIEW = ROOT + r"\build\view"
ANIMS = ["draw_seq", "ads_in_anim", "reload_seq", "reload_empty_seq", "sprint_seq", "attack_anim", "idle_anim"]
HIDE = ("v_holo", "v_acgs", "v_cro", "v_proscreen", "sight_on", "glow")
SPIN = {"def_c_reactive_spinner_coils": 1.0, "def_c_reactive_spinner_1": -2.0, "def_c_reactive_spinner_2": 2.0}
FOV_X = math.radians(86.0)        # TF2 70 deg (4:3) horizontal -> 16:9

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_valvesource", default_set=False)
bpy.ops.import_scene.smd(filepath=VIEW + r"\ptpov_car101.qc", doAnim=False, createCollections=True)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
arm.name = "ptpov_car101_merged_armature"

img = bpy.data.images.load(ROOT + r"\repak\png\prowler_scavenger_col.png")
mat = bpy.data.materials.new("prowler_scavenger_col")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
mat.node_tree.links.new(tex.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
unbound = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    if not any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers):
        unbound.append(o.name)
    if any(h in o.name for h in HIDE):
        o.hide_render = True
        o.hide_set(True)
    elif "prowler" in o.name:
        o.data.materials.clear()
        o.data.materials.append(mat)
print("CHECK meshes bound to the armature:", [o.name for o in bpy.data.objects if o.type == "MESH"], "unbound:", unbound)

actions = {}
for name in ANIMS:
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if arm.animation_data:
        arm.animation_data.action = None          # BST writes into the current action otherwise
    bpy.ops.import_scene.smd(filepath=VIEW + rf"\anims\{name}.smd")
    act = arm.animation_data.action
    assert act not in actions.values(), f"{name} was imported into an existing action"
    act.name = name
    act.use_fake_user = True
    actions[name] = act
print("CHECK actions:", {k: (v.name, tuple(v.frame_range)) for k, v in actions.items()})
for o in bpy.data.objects:
    if o.name == "smd_bone_vis":
        o.hide_render = True

sc = bpy.context.scene
cam = bpy.data.objects.new("fp_camera", bpy.data.cameras.new("fp_camera"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.sensor_fit = "HORIZONTAL"
cam.data.angle = FOV_X
cam.data.clip_start = 0.05
FLIP = Matrix.Rotation(math.pi, 4, "Y")       # camera bone: +Z forward, +Y up -> Blender camera looks down -Z


def smd_frame(name, frame):
    n, f, _ = read_smd(VIEW + rf"\anims\{name}.smd")
    frame = frame if frame >= 0 else len(f) + frame
    return by_name(n, globals_(n, f[frame])), frame


def pose(name, frame):
    act = actions[name]
    arm.animation_data.action = act
    if hasattr(arm.animation_data, "action_slot") and getattr(act, "slots", None):   # Blender 4.4+ slotted actions
        arm.animation_data.action_slot = act.slots[0]
    assert arm.animation_data.action == act, f"could not assign action {name}"
    sc.frame_set(int(act.frame_range[0]) + frame)
    bpy.context.view_layer.update()


# camera follows jx_c_camera (bone parent, as in the tutorial); placed from the SMD data at the draw end
g, fr = smd_frame("draw_seq", -1)
pose("draw_seq", fr)
cam.matrix_world = arm.matrix_world @ g["jx_c_camera"] @ FLIP
cam.parent = arm
cam.parent_type = "BONE"
cam.parent_bone = "jx_c_camera"
cam.matrix_world = arm.matrix_world @ g["jx_c_camera"] @ FLIP
bpy.context.view_layer.update()

# hand skeleton overlay
hand_mat = {s: bpy.data.materials.new("hand_" + s) for s in "lr"}
hand_mat["r"].diffuse_color = (1.0, 0.25, 0.1, 1)
hand_mat["l"].diffuse_color = (0.1, 0.6, 1.0, 1)
n0, _, _ = read_smd(VIEW + r"\anims\draw_seq.smd")
parent_of = {nm: (n0[p][0] if p >= 0 else None) for i, (nm, p) in n0.items()}
HAND = [nm for nm in parent_of if nm.startswith(("def_r_fin", "def_l_fin", "def_r_wrist", "def_l_wrist")) and "helper" not in nm]


def draw_hands(g):
    for o in [o for o in bpy.data.objects if o.name.startswith("hand_")]:
        bpy.data.objects.remove(o)
    for side in "lr":
        cu = bpy.data.curves.new("hand_" + side, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.12
        for nm in HAND:
            if nm[4] != side or parent_of[nm] not in g:
                continue
            sp = cu.splines.new("POLY")
            sp.points.add(1)
            for k, b in enumerate((parent_of[nm], nm)):
                sp.points[k].co = (*(arm.matrix_world @ g[b].translation), 1)
        ob = bpy.data.objects.new("hand_" + side, cu)
        ob.data.materials.append(hand_mat[side])
        ob.show_in_front = True
        sc.collection.objects.link(ob)


def spin_drum(g, turn):
    """the per-shot fire delta: each drum bone rotates about its local Z (gun forward) by turn * its rate"""
    for b, rate in SPIN.items():
        pb = arm.pose.bones[b]
        axis = g[b].to_3x3().col[2].normalized()
        piv = g[b].translation
        R = Matrix.Translation(piv) @ Matrix.Rotation(turn * rate * 2 * math.pi, 4, axis) @ Matrix.Translation(-piv)
        pb.matrix = R @ pb.matrix
    bpy.context.view_layer.update()


def check(g, tag):
    dist = {b: ((arm.matrix_world @ arm.pose.bones[b].head) - (arm.matrix_world @ g[b].translation)).length
            for b in ("jx_c_delta", "def_c_base", "def_r_wrist", "def_l_wrist", "jx_c_camera", "def_c_magazine",
                      "def_c_reactive_spinner_coils") if b in g and b in arm.pose.bones}
    worst = max(dist, key=dist.get)
    print(f"CHECK {tag}: action {arm.animation_data.action.name} frame {sc.frame_current} "
          f"Blender pose vs SMD max bone distance {dist[worst]:.4f} ({worst})")


sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.32, 0.34, 0.38)
shots = [("draw_seq", -1, "hip"), ("ads_in_anim", -1, "ads"), ("reload_seq", 20, "reload_f20"),
         ("reload_seq", 40, "reload_f40"), ("sprint_seq", 0, "sprint")]
side = bpy.data.objects.new("side_camera", bpy.data.cameras.new("side_camera"))
sc.collection.objects.link(side)
side.data.type = "ORTHO"
side.data.ortho_scale = 30


def render_side(g, tag):
    """same pose seen from the gun's right side (def_c_base -X), gun forward = image right"""
    b = arm.matrix_world @ g["def_c_base"]
    fwd, up = b.to_3x3().col[2].normalized(), b.to_3x3().col[1].normalized()
    right = fwd                                      # image right = gun forward
    back = right.cross(up).normalized()              # camera +Z
    side.matrix_world = Matrix.Translation(b.translation + back * 60 + fwd * -2.5 + up * 1.5) @ \
        Matrix((right, up, back)).transposed().to_4x4()
    sc.camera = side
    sc.render.filepath = ROOT + rf"\previews\fp_{tag}_side.png"
    bpy.ops.render.render(write_still=True)
    sc.camera = cam
    print("RENDER_OK", sc.render.filepath)


for name, frame, tag in shots:
    g, fr = smd_frame(name, frame)
    pose(name, fr)
    check(g, tag)
    draw_hands(g)
    sc.render.filepath = ROOT + rf"\previews\fp_{tag}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", sc.render.filepath)
    render_side(g, tag)
# per-shot drum turn on the hip pose (attack delta frames 0..3 = 0/120/240/360 deg), plus in-between angles
g, fr = smd_frame("draw_seq", -1)
for k, turn in enumerate((0.0, 1 / 6, 1 / 3, 1 / 2, 2 / 3)):
    pose("draw_seq", fr)
    spin_drum(g, turn)
    draw_hands(g)
    sc.render.filepath = ROOT + rf"\previews\fp_drum_{k}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", sc.render.filepath, "turn", turn)
pose("draw_seq", fr)
for o in [o for o in bpy.data.objects if o.name.startswith("hand_")]:
    bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=ROOT + r"\blend\prowler_car_view_rig.blend")
print("RIG_BLEND_OK")
