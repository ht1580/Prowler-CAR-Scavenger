"""blender -b --factory-startup -P sim_fire.py -- <base.json> <delta.json> [frames]
Fire simulation from the FINAL MDL: decoded base pose (draw_seq end = what idle keeps) with the decoded
attack delta layered the way Source applies a delta layer (pos = base + delta, rot = base * delta, local).
Prints, per frame, every bone that moves relative to def_c_base (origin shift / turn) and renders the gun
from its right side so a part that leaves the gun is visible."""
import math
import json
import sys
import bpy
from mathutils import Euler, Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
a = sys.argv[sys.argv.index("--") + 1:]
base_doc, delta_doc = (json.load(open(p, encoding="utf-8")) for p in a[:2])
frames = [int(x) for x in a[2].split(",")] if len(a) > 2 else list(range(8))
bones = base_doc["bones"]
names = [b["name"] for b in bones]
par = [b["parent"] for b in bones]


def lm(v):
    return Matrix.Translation(Vector(v["pos"])) @ Euler(v["rot"], "XYZ").to_matrix().to_4x4()


rest = {i: {"pos": b["pos"], "rot": b["rot"]} for i, b in enumerate(bones)}
bp = max(base_doc["poses"], key=lambda p: p["frame"])
base = dict(rest)
base.update({v["index"]: v for v in bp["locals"]})
deltas = {p["frame"]: {v["index"]: v for v in p["locals"]} for p in delta_doc["poses"]}


def pose(frame):
    out = {}
    for i in range(len(bones)):
        b = base[i]
        q = Euler(b["rot"], "XYZ").to_quaternion()
        p = Vector(b["pos"])
        d = deltas[frame].get(i) if frame is not None else None
        if d is not None:
            q = q @ Euler(d["rot"], "XYZ").to_quaternion()
            p = p + Vector(d["pos"])
        out[i] = Matrix.Translation(p) @ q.to_matrix().to_4x4()
    g = {}
    for i in range(len(bones)):
        g[i] = (g[par[i]] if par[i] >= 0 else Matrix.Identity(4)) @ out[i]
    return {names[i]: m for i, m in g.items()}


G0 = pose(None)
B0 = G0["def_c_base"].inverted()
for f in frames:
    G = pose(f)
    Bf = G["def_c_base"].inverted()
    movers = []
    for nm in names:
        if nm.startswith(("def_c_", "jx_c_bolt")) and nm != "def_c_base":
            r0, r1 = B0 @ G0[nm], Bf @ G[nm]
            shift = (r1.translation - r0.translation).length
            turn = math.degrees(r0.to_quaternion().rotation_difference(r1.to_quaternion()).angle)
            if shift > 0.05 or turn > 1:
                movers.append(f"{nm}(shift {shift:.2f}, turn {turn:.0f})")
    print(f"FIRE f{f}: " + ("; ".join(movers) if movers else "nothing moves"))

# render: gun meshes skinned with the frame pose, seen from the right side
mesh_paths = [ROOT + r"\build\view\prowler_body.smd", ROOT + r"\build\view\prowler_magazine.smd"]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 34
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.render.resolution_x, sc.render.resolution_y = 800, 450
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.32, 0.34, 0.38)
meshes = []
for path in mesh_paths:
    mn, mf, _ = read_smd(path)
    bind = by_name(mn, globals_(mn, mf[0]))
    idn = {i: nm for i, (nm, _) in mn.items()}
    lines = open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    i = lines.index("triangles") + 1
    tris = []
    while i < len(lines) and lines[i].strip() != "end":
        vs = []
        for k in range(1, 4):
            t = lines[i + k].split()
            p = Vector((float(t[1]), float(t[2]), float(t[3])))
            links = [(idn[int(t[10 + 2 * j])], float(t[11 + 2 * j])) for j in range(int(t[9]))] if len(t) > 10 and int(t[9]) > 0 else [(idn[int(t[0])], 1.0)]
            vs.append((p, links))
        tris.append((lines[i].strip(), vs))
        i += 4
    meshes.append((bind, tris))
for f in [None] + frames:
    G = pose(f)
    for o in list(sc.collection.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o)
    for bind, tris in meshes:
        verts, faces = [], []
        for mat, vs in tris:
            if "glow" in mat:
                continue
            face = []
            for p, links in vs:
                acc = Vector()
                for nm, w in links:
                    acc += w * ((G[nm] @ bind[nm].inverted()) @ p if nm in G else p)
                face.append(len(verts))
                verts.append(tuple(acc))
            faces.append(face)
        me = bpy.data.meshes.new("gun")
        me.from_pydata(verts, [], faces)
        sc.collection.objects.link(bpy.data.objects.new("gun", me))
    b = G["def_c_base"]
    fwd, up = b.to_3x3().col[2].normalized(), b.to_3x3().col[1].normalized()
    back = fwd.cross(up).normalized()
    cam.matrix_world = Matrix.Translation(b.translation + fwd * 4 + up * 2 + back * 60) @ Matrix((fwd, up, back)).transposed().to_4x4()
    sc.render.filepath = ROOT + rf"\previews\fire_{'base' if f is None else f'f{f:02d}'}.png"
    bpy.ops.render.render(write_still=True)
print("SIM_FIRE_OK")
