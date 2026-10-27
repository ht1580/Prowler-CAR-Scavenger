"""blender -b --factory-startup -P preview_world.py -- out.png : side view of world-model SMDs at rest."""
import bpy
import sys
import math
from mathutils import Vector, Matrix
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd

W = r"D:\TitanfallMods\35_ProwlerCAR\build\world"
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
cols = {"prowler_w_body_lod0": (0.75, 0.62, 0.42, 1), "prowler_w_sight_on": (0.2, 0.2, 0.2, 1),
        "stock_w_holo": (0.3, 0.5, 0.9, 1), "stock_w_proscreen": (0.9, 0.2, 0.9, 1)}
for part, c in cols.items():
    n, f, tris = read_smd(W + "\\" + part + ".smd")
    verts, faces = [], []
    for mat, vs in tris:
        b = len(verts)
        verts += [Vector(map(float, p[1:4])) for p in vs]
        faces.append((b, b + 1, b + 2))
    me = bpy.data.meshes.new(part)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(part, me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new(part)
    m.diffuse_color = c
    ob.data.materials.append(m)
cd = bpy.data.cameras.new("c")
cd.type = "ORTHO"
cd.ortho_scale = 24
cam = bpy.data.objects.new("c", cd)
bpy.context.scene.collection.objects.link(cam)
# look from +x (gun's left side) toward -x, y up
cam.matrix_world = Matrix.Translation((30, 4, -2)) @ Matrix.Rotation(math.radians(90), 4, "Y")
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1200, 600
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PREVIEW_WORLD_OK")
