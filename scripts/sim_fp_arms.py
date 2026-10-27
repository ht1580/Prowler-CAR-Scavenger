"""blender -b --factory-startup -P sim_fp_arms.py -- <tag> <viewmodel anims dir> <mesh smd>[,<mesh smd>...] <anim> <frame> [out.png]

First-person simulation with the REAL pilot arms: the game bonemerges the arms model
(models/weapons/arms/pov_pilot_*.mdl) onto the viewmodel by bone name, so every arms bone that exists in the
viewmodel takes the viewmodel bone's world transform; the rest follow their arms-model parent at arms rest.
Arms vertices (embedded VVD, LOD0) are skinned with that pose and drawn as small blobs; the gun meshes (SMD
triangles) are skinned with the same animation frame. Camera = jx_c_camera, as make_rig_blend.py."""
import json
import math
import struct
import sys
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
ARMS = ROOT + r"\stock\arms\pov_pilot_medium_stalker_m.mdl"
ARMS_BONES = ROOT + r"\stock\arms\arms_bones.json"
a = sys.argv[sys.argv.index("--") + 1:]
tag, anim_dir, meshes, anim, frame = a[0], a[1], a[2].split(","), a[3], int(a[4])
out_png = a[5] if len(a) > 5 else ROOT + rf"\previews\sim_{tag}_{anim}_f{frame}.png"
HIDE = ("v_holo", "v_acgs", "v_cro", "v_proscreen", "sight_on", "glow")

# --- viewmodel pose
n, f, _ = read_smd(anim_dir + "\\" + anim + ".smd")
frame = frame if frame >= 0 else len(f) + frame
vm = by_name(n, globals_(n, f[frame]))

# --- arms skeleton (rest) + bonemerged pose
ab = json.load(open(ARMS_BONES, encoding="utf-8"))["bones"]
rest_local = [Matrix.Translation(Vector(b["pos"])) @ Euler(b["rot"], "XYZ").to_matrix().to_4x4() for b in ab]
rest_g, pose_g = [], []
merged = []
for k, b in enumerate(ab):
    p = b["parent"]
    rest_g.append((rest_g[p] if p >= 0 else Matrix.Identity(4)) @ rest_local[k])
    if b["name"] in vm:
        pose_g.append(vm[b["name"]].copy())
        merged.append(b["name"])
    else:
        pose_g.append((pose_g[p] if p >= 0 else Matrix.Identity(4)) @ rest_local[k])
skin = [np.array(pose_g[k] @ rest_g[k].inverted()) for k in range(len(ab))]
print("SIM merged arms bones:", len(merged), "/", len(ab), "unmerged:", [b["name"] for b in ab if b["name"] not in vm])

# --- arms vertices from the embedded VVD (48-byte vertices: 3 weights, 3 bone ids, count, pos, normal, uv)
d = open(ARMS, "rb").read()
v = d.find(b"IDSV")
nverts = struct.unpack_from("<i", d, v + 16)[0]
vstart = struct.unpack_from("<i", d, v + 56)[0]
GROUPS = (("hand", ("fin", "wrist", "propHand"), (0.9, 0.15, 0.1, 1)),
          ("forearm", ("forearm", "elbow"), (0.95, 0.75, 0.1, 1)),
          ("upper", ("shoulder", "clav"), (0.15, 0.45, 0.95, 1)),
          ("body", ("",), (0.6, 0.6, 0.6, 1)))
pts = {g[0]: [] for g in GROUPS}
for k in range(nverts):
    o = v + vstart + k * 48
    w = struct.unpack_from("<3f", d, o)
    bid = struct.unpack_from("<3B", d, o + 12)
    nb = d[o + 15]
    p = np.array((*struct.unpack_from("<3f", d, o + 16), 1.0))
    q = sum(w[i] * (skin[bid[i]] @ p) for i in range(nb))
    dom = ab[bid[max(range(nb), key=lambda i: w[i])]]["name"]
    grp = next(g[0] for g in GROUPS if any(s in dom for s in g[1]))
    pts[grp].append(Vector(q[:3]))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def blob_mesh(name, points, r, color):
    verts, faces = [], []
    for c in points:
        base = len(verts)
        verts += [c + Vector((r, 0, 0)), c + Vector((-r, r, 0)), c + Vector((-r, -r, 0)), c + Vector((0, 0, r * 1.5)), c + Vector((0, 0, -r * 1.5))]
        faces += [(base, base + 1, base + 3), (base + 1, base + 2, base + 3), (base + 2, base, base + 3),
                  (base, base + 1, base + 4), (base + 1, base + 2, base + 4), (base + 2, base, base + 4)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in verts], [], faces)
    ob = bpy.data.objects.new(name, me)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    me.materials.append(mat)
    sc.collection.objects.link(ob)
    return ob


for g in GROUPS:
    blob_mesh("arms_" + g[0], pts[g[0]], 0.08, g[2])

# --- gun meshes: SMD triangles skinned from their own reference skeleton to the animation frame
for path in meshes:
    if any(h in path for h in HIDE):
        continue
    mn, mf, _ = read_smd(path)
    bind = by_name(mn, globals_(mn, mf[0]))
    names = {i: nm for i, (nm, _) in mn.items()}
    lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    i = lines.index("triangles") + 1
    verts, faces = [], []
    while i < len(lines) and lines[i].strip() != "end":
        mat = lines[i].strip()
        tri = []
        for k in range(1, 4):
            t = lines[i + k].split()
            p = Vector((float(t[1]), float(t[2]), float(t[3])))
            links = [(int(t[0]), 1.0)]
            if len(t) > 10 and int(t[9]) > 0:
                links = [(int(t[10 + 2 * j]), float(t[11 + 2 * j])) for j in range(int(t[9]))]
            acc = Vector((0, 0, 0))
            for b, w in links:
                nm = names[b]
                M = vm[nm] @ bind[nm].inverted() if nm in vm else Matrix.Identity(4)
                acc += w * (M @ p)
            tri.append(len(verts))
            verts.append(tuple(acc))
        if not any(h in mat for h in HIDE):
            faces.append(tuple(tri))
        i += 4
    me = bpy.data.meshes.new(path.split("\\")[-1])
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(me.name, me)
    gm = bpy.data.materials.new("gun")
    gm.diffuse_color = (0.55, 0.6, 0.65, 1)
    me.materials.append(gm)
    sc.collection.objects.link(ob)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.sensor_fit = "HORIZONTAL"
cam.data.angle = math.radians(float(__import__("os").environ.get("SIM_FOV", "86")))
cam.data.clip_start = 0.05
cam.matrix_world = vm["jx_c_camera"] @ Matrix.Rotation(math.pi, 4, "Y")
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.32, 0.34, 0.38)
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
# side view (from the player's right, camera forward = image right) to see what sits in front of the eye
side = bpy.data.objects.new("side", bpy.data.cameras.new("side"))
sc.collection.objects.link(side)
side.data.type = "ORTHO"
side.data.ortho_scale = 60
C = vm["jx_c_camera"]
fwd, up = C.to_3x3().col[2].normalized(), C.to_3x3().col[1].normalized()
back = fwd.cross(up).normalized()
side.matrix_world = Matrix.Translation(C.translation + fwd * 12 - up * 8 + back * 80) @ Matrix((fwd, up, back)).transposed().to_4x4()
eye = bpy.data.objects.new("eye", bpy.data.meshes.new("eye"))
sc.collection.objects.link(eye)
blob_mesh("eye_marker", [C.translation], 0.8, (0.1, 0.9, 0.2, 1))
sc.camera = side
sc.render.filepath = out_png.replace(".png", "_side.png")
bpy.ops.render.render(write_still=True)
wl = vm["def_l_wrist"].translation if "def_l_wrist" in vm else None
print("SIM_OK", out_png, "verts", nverts, "l_wrist", tuple(round(x, 2) for x in wl) if wl else None)
