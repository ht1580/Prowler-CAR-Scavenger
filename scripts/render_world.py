"""blender -b -P render_world.py -- <out.png> : textured side view of the generated third-person mesh
(build/world, root space = the pilot's hand, +z forward) with red = grip-hand IK (l_hand_ik), blue =
support-hand IK (r_hand_ik), white = root (hand prop)."""
import sys
import bpy
import addon_utils
from mathutils import Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTP = argv[0] if argv else ROOT + r"\previews\world_side.png"
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_valvesource", default_set=False)
img = bpy.data.images.load(ROOT + r"\repak\png\prowler_scavenger_col.png")
mat = bpy.data.materials.new("col")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
mat.node_tree.links.new(tex.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
for m in ("prowler_w_body_lod0", "prowler_w_sight_on"):
    bpy.ops.import_scene.smd(filepath=ROOT + rf"\build\world\{m}.smd", doAnim=False)
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(mat)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    elif o.type == "ARMATURE":
        o.hide_render = True
n, f, _ = read_smd(ROOT + r"\build\world\prowler_w_body_lod0.smd")
g = by_name(n, globals_(n, f[0]))


def marker(p, color, r=0.4):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p)
    s = bpy.context.object
    m = bpy.data.materials.new("m")
    m.diffuse_color = color
    s.data.materials.append(m)


for b, col in (("ja_c_propGun", (1, 1, 1, 1)), ("l_hand_ik", (1, 0, 0, 1)), ("r_hand_ik", (0, .3, 1, 1))):
    p = g[b].translation
    marker(p, col)
    print(f"MARK {b:14s} ({p.x:6.2f},{p.y:6.2f},{p.z:6.2f})")
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x, sc.render.resolution_y = 1600, 800
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 26
right, up = Vector((0, 0, 1)), Vector((0, 1, 0))
cam.matrix_world = Matrix.Translation(Vector((-40, 2.5, -2.5))) @ Matrix((right, up, right.cross(up))).transposed().to_4x4()
sc.render.filepath = OUTP
bpy.ops.render.render(write_still=True)
print("RENDER_OK", OUTP)
