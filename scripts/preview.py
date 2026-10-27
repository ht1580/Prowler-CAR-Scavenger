"""blender -b -P preview.py -- <anim.smd> <frame> <out.png> [bodygroups...]
First-person preview: skins built SMD meshes to a frame of a built animation, finger joints as spheres,
camera at jx_c_camera looking down +Z (rig y-up), 70 deg horizontal FOV."""
import bpy
import sys
import math
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
anim, frame, out = argv[0], int(argv[1]), argv[2]
parts = argv[3:] or ["prowler_body", "prowler_magazine", "prowler_sight_on", "prowler_glow"]
V = r"D:\TitanfallMods\35_ProwlerCAR\build\view"
COL = r"D:\Apex_猎兽进化皮_v21_scavenger\02_贴图_Textures\基础色_base\prowler_v21_react_scavenger_col.png"

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
n, f, _ = read_smd(anim)
fr = f[min(frame, len(f) - 1)] if frame >= 0 else f[-1]
pose = by_name(n, globals_(n, fr))
rn, rf, _ = read_smd(V + r"\ref.smd")
bind = by_name(rn, globals_(rn, rf[0]))
inv_bind = {k: m.inverted() for k, m in bind.items()}

mat_tex = bpy.data.materials.new("tex")
mat_tex.use_nodes = True
img = bpy.data.images.load(COL)
nt = mat_tex.node_tree
tn = nt.nodes.new("ShaderNodeTexImage")
tn.image = img
nt.links.new(tn.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
mat_glow = bpy.data.materials.new("glow")
mat_glow.diffuse_color = (1.0, 0.35, 0.05, 1)
mat_grey = bpy.data.materials.new("grey")
mat_grey.diffuse_color = (0.25, 0.25, 0.28, 1)
mat_hand = bpy.data.materials.new("hand")
mat_hand.diffuse_color = (0.1, 0.9, 0.2, 1)

for part in parts:
    pn, pf, tris = read_smd(V + "\\" + part + ".smd")
    names = {i: nm for i, (nm, p) in pn.items()}
    verts, faces, uvs = [], [], []
    for mat, vs in tris:
        base = len(verts)
        for p in vs:
            pos = Vector(map(float, p[1:4]))
            cnt = int(p[9])
            acc = Vector((0, 0, 0))
            tw = 0
            for k in range(cnt):
                b = names[int(p[10 + 2 * k])]
                w = float(p[11 + 2 * k])
                acc += (pose[b] @ inv_bind[b] @ pos) * w
                tw += w
            verts.append(acc / tw if tw else pos)
            uvs.append((float(p[7]), float(p[8])))
        faces.append((base, base + 1, base + 2))
    me = bpy.data.meshes.new(part)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new()
    for li, loop in enumerate(me.loops):
        uvl.data[li].uv = uvs[loop.vertex_index]
    ob = bpy.data.objects.new(part, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat_glow if "glow" in part else (mat_tex if part.startswith("prowler") else mat_grey))

for b, m in pose.items():
    if b.startswith(("def_r_fin", "def_l_fin", "def_r_wrist", "def_l_wrist")):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=m.translation, segments=8, ring_count=6)
        bpy.context.object.data.materials.append(mat_hand)

# RUI quads (local to parent bone) drawn as magenta panels: ammo counters on def_c_sight_on
import os as _os
if _os.environ.get("PREVIEW_RUI"):
    sys.path.insert(0, r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench")
    import rui_editor
    doc = rui_editor.inspect_mdl(_os.environ["PREVIEW_RUI"])
    mat_rui = bpy.data.materials.new("rui")
    mat_rui.diffuse_color = (1.0, 0.0, 1.0, 1)
    for m in doc["meshes"]:
        if "car_smg_rui" not in m["name"]:
            continue
        bone = m["parentNames"][0]
        pts = [pose[bone] @ Vector(v["position"]) for v in m["vertices"]]
        faces = [tuple(f["vertices"]) for f in m["faces"]]
        me = bpy.data.meshes.new(m["name"])
        me.from_pydata(pts, [], faces)
        ob = bpy.data.objects.new(m["name"], me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat_rui)

cam_m = pose["jx_c_camera"]
cd = bpy.data.cameras.new("cam")
cd.angle = math.radians(70)
cd.clip_start = 0.5
cam = bpy.data.objects.new("cam", cd)
bpy.context.scene.collection.objects.link(cam)
eye = cam_m.translation
r3 = cam_m.to_3x3()
fwd = (r3 @ Vector((0, 0, 1))).normalized()
# rig camera: +Z forward, +Y up, +X = left  ->  blender camera X=right, Y=up, Z=back
rot = Matrix(((r3 @ Vector((-1, 0, 0))).normalized(), (r3 @ Vector((0, 1, 0))).normalized(), -fwd)).transposed()
cam.matrix_world = Matrix.Translation(eye) @ rot.to_4x4()
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.light = "STUDIO"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PREVIEW_OK", out, "eye", tuple(round(x, 2) for x in eye), "fwd", tuple(round(x, 2) for x in fwd))
