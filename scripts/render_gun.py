"""blender -b -P render_gun.py -- <out.png> [anim.smd frame]
Textured orthographic side views of the Prowler view meshes (def_c_base space: +z forward, +y up),
with markers: red = right hand (ja_r_propHand), orange = right index finger tip, blue = left hand
(ja_l_propHand), green = reactive spinner bones. Hands come from one frame of a first-person anim."""
import sys
import bpy
import addon_utils
from mathutils import Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTP = argv[0] if argv else ROOT + r"\previews\gun_side.png"
ANIM = argv[1] if len(argv) > 1 else ROOT + r"\build\view\anims\draw_seq.smd"
FRAME = int(argv[2]) if len(argv) > 2 else -1

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("io_scene_valvesource", default_set=False)
img = bpy.data.images.load(ROOT + r"\repak\png\prowler_scavenger_col.png")
mat = bpy.data.materials.new("col")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
bsdf = mat.node_tree.nodes["Principled BSDF"]
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

for m in ("prowler_body", "prowler_magazine", "prowler_sight_on"):
    bpy.ops.import_scene.smd(filepath=ROOT + rf"\build\view\{m}.smd", doAnim=False)
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.parent = None
    elif o.type == "ARMATURE":
        o.hide_render = True

# mesh space -> def_c_base space
n, f, _ = read_smd(ROOT + r"\build\view\prowler_body.smd")
rest = by_name(n, globals_(n, f[0]))
base_rest = rest["def_c_base"]
for o in bpy.data.objects:
    if o.type == "MESH":
        o.matrix_world = base_rest.inverted() @ o.matrix_world

an, af, _ = read_smd(ANIM)
g = by_name(an, globals_(an, af[FRAME if FRAME >= 0 else len(af) + FRAME]))
bi = g["def_c_base"].inverted()


def marker(p, color, r=0.35):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p)
    s = bpy.context.object
    m = bpy.data.materials.new("m")
    m.diffuse_color = color
    m.use_nodes = False
    s.data.materials.append(m)
    s.show_in_front = True


pts = {}
for b, col in (("ja_r_propHand", (1, 0, 0, 1)), ("def_r_finIndexC", (1, .5, 0, 1)), ("def_r_finIndexA", (1, .8, 0, 1)),
               ("ja_l_propHand", (0, .3, 1, 1)), ("def_l_finMidA", (0, .8, 1, 1))):
    if b in g:
        pts[b] = bi @ g[b].translation
        marker(pts[b], col)
for b in rest:
    if "spinner" in b or "coil" in b:
        p = base_rest.inverted() @ rest[b].translation
        pts[b] = p
        marker(p, (0, 1, 0, 1), 0.25)
for b, p in pts.items():
    print(f"MARK {b:24s} ({p.x:7.2f},{p.y:7.2f},{p.z:7.2f})")

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x, sc.render.resolution_y = 1600, 800
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.12, 0.12, 0.14)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 26
# view from -X (gun's right side): camera right = +Z (forward), up = +Y, looking along +X
for tag, sx in (("right", -1), ("left", 1)):
    right, up = Vector((0, 0, -sx)), Vector((0, 1, 0))
    back = right.cross(up)                      # camera +Z (points away from view direction)
    R = Matrix((right, up, back)).transposed()
    cam.matrix_world = Matrix.Translation(Vector((sx * 40, 2.5, -2.5))) @ R.to_4x4()
    sc.render.filepath = OUTP.replace(".png", f"_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK", sc.render.filepath)
