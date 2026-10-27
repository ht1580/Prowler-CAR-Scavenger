"""blender -b --factory-startup -P skeleton_audit.py -- <dir with {model}_{anim}.json> model,model,... anim,anim,...
Skeleton audit of decoded final-MDL poses (decode_native_pose.ps1 -AllFrames), every frame:
  topology  arm/body bone parents identical to the stock CAR; exactly one left + one right arm chain;
            no gun bone hanging under an arm bone (except the ja_*_propHand prop points)
  stretch   every arm/finger segment length vs the TF2 pilot arms model (the mesh that gets bonemerged)
  twist     elbow = pure hinge about local Y; wrist twist about the forearm
and renders stick skeletons (camera view + side view) of selected frames, models side by side."""
import json
import math
import os
import sys
import bpy
from mathutils import Euler, Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]
D, MODELS, ANIMS = a[0], a[1].split(","), a[2].split(",")
ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
ARMS = json.load(open(ROOT + r"\stock\arms\arms_bones.json", encoding="utf-8"))["bones"]
ARM_NAMES = [b["name"] for b in ARMS]
ARM_LEN = {b["name"]: Vector(b["pos"]).length for b in ARMS}
ARM_PARENT = {b["name"]: (ARM_NAMES[b["parent"]] if b["parent"] >= 0 else None) for b in ARMS}
CAR_REF = json.load(open(os.path.join(D, "car_draw_seq.json"), encoding="utf-8"))["bones"]
CAR_PARENT = {b["name"]: (CAR_REF[b["parent"]]["name"] if b["parent"] >= 0 else None) for b in CAR_REF}


def load(model, anim):
    p = os.path.join(D, f"{model}_{anim}.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    if not d["poses"]:
        return None
    bones = d["bones"]
    names = [b["name"] for b in bones]
    par = [b["parent"] for b in bones]
    frames = []
    for pose in sorted(d["poses"], key=lambda x: x["frame"]):
        loc = {v["index"]: v for v in pose["locals"]}
        L, G = [], []
        for i, b in enumerate(bones):
            v = loc.get(i, b)
            m = Matrix.Translation(Vector(v["pos"])) @ Euler(v["rot"], "XYZ").to_matrix().to_4x4()
            L.append(m)
            G.append((G[par[i]] if par[i] >= 0 else Matrix.Identity(4)) @ m)
        frames.append(({n: L[i] for i, n in enumerate(names)}, {n: G[i] for i, n in enumerate(names)}))
    return names, {n: (names[p] if p >= 0 else None) for n, p in zip(names, par)}, frames


summary = {}
for model in MODELS:
    for anim in ANIMS:
        got = load(model, anim)
        if not got:
            continue
        names, parent, frames = got
        topo = []
        for n in names:
            if n.startswith(("def_l_", "def_r_", "def_c_hip", "def_c_spine", "def_c_neck", "def_c_head", "jx_", "ja_")) and "reactive" not in n:
                if n in CAR_PARENT and parent[n] != CAR_PARENT[n]:
                    topo.append(f"{n}: parent {parent[n]} (stock {CAR_PARENT[n]})")
        chains = {s: [n for n in names if n == f"def_{s}_wrist"] for s in "lr"}
        extra_arm = [n for n in names if (("wrist" in n or "elbow" in n or "shoulder" in n or "_fin" in n) and n not in ARM_NAMES)]
        under_arm = [n for n in names if parent[n] and parent[n].startswith(("def_l_", "def_r_")) and n not in ARM_NAMES]
        stretch, hinge, wtw = 0.0, 0.0, 0.0
        worst_seg = ""
        for L, G in frames:
            for n in ARM_NAMES:
                p = ARM_PARENT[n]
                if n in G and p in G and (n.startswith(("def_l_", "def_r_"))) and ARM_LEN[n] > 0.3:
                    seg = (G[n].translation - G[p].translation).length
                    r = abs(seg / ARM_LEN[n] - 1)
                    if r > stretch:
                        stretch, worst_seg = r, f"{n} {seg:.2f} vs arms {ARM_LEN[n]:.2f}"
            for s in "lr":
                if f"def_{s}_elbow" in L:
                    r3 = L[f"def_{s}_elbow"].to_3x3()
                    hinge = max(hinge, math.degrees(math.acos(max(-1, min(1, r3.col[1].normalized().y)))))
                if f"def_{s}_wrist" in L:
                    q = L[f"def_{s}_wrist"].to_quaternion()
                    t = abs(math.degrees(2 * math.atan2(q.x, q.w)))
                    wtw = max(wtw, min(t, 360 - t))
        summary[(model, anim)] = (len(frames), topo, {s: len(c) for s, c in chains.items()}, extra_arm, under_arm, stretch, worst_seg, hinge, wtw)
        print(f"AUDIT {model:6s} {anim:18s} frames {len(frames):3d} | parent changes vs stock {len(topo)} | wrists L{len(chains['l'])} R{len(chains['r'])} "
              f"| extra arm-like bones {extra_arm[:4]} | non-arm bones under arm bones {under_arm[:4]} "
              f"| max stretch {stretch * 100:5.1f}% ({worst_seg}) | elbow off-hinge {hinge:5.1f} deg | wrist twist {wtw:5.1f} deg")
        for t in topo[:5]:
            print("      TOPO", t)

# ---------------------------------------------------------------- stick renders
SHOTS = [("draw_seq", -1, "hip"), ("reload_empty_seq", 30, "reload30"), ("reload_empty_seq", 45, "reload45"), ("ads_in_anim", -1, "ads"), ("sprint_seq", 10, "sprint")]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"
sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 640, 360
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.12, 0.12, 0.14)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
COL = {"l": (0.2, 0.6, 1.0, 1), "r": (1.0, 0.3, 0.2, 1), "body": (0.6, 0.6, 0.6, 1), "gun": (0.2, 0.9, 0.3, 1), "drum": (1.0, 0.9, 0.1, 1)}
mats = {}
for k, c in COL.items():
    m = bpy.data.materials.new(k)
    m.diffuse_color = c
    mats[k] = m


def group(n):
    if n == "def_c_bolt":
        return "drum"
    if n.startswith("def_l_") and "reactive" not in n or n == "ja_l_propHand":
        return "l"
    if n.startswith("def_r_") and "reactive" not in n or n == "ja_r_propHand":
        return "r"
    if n.startswith(("def_c_hip", "def_c_spine", "def_c_neck", "def_c_head", "jx_c_neckB", "jx_c_start")):
        return "body"
    if n.startswith(("jx_c_delta", "jx_c_pov", "jx_c_camera")):
        return None
    return "gun"


out = []
for model in MODELS:
    for anim, fi, tag in SHOTS:
        got = load(model, anim)
        if not got:
            continue
        names, parent, frames = got
        L, G = frames[fi if fi >= 0 else len(frames) + fi] if abs(fi) < len(frames) or fi < 0 else frames[-1]
        for o in [o for o in sc.collection.objects if o.type == "CURVE"]:
            bpy.data.objects.remove(o)
        curves, objs = {}, {}
        for n in names:
            p = parent[n]
            g = group(n)
            if not p or g is None or group(p) is None:
                continue
            if g not in curves:
                cu = bpy.data.curves.new(g, "CURVE")
                cu.dimensions = "3D"
                cu.bevel_depth = 0.07
                ob = bpy.data.objects.new(g, cu)
                ob.data.materials.append(mats[g])
                sc.collection.objects.link(ob)
                curves[g], objs[g] = cu, ob
            sp = curves[g].splines.new("POLY")
            sp.points.add(1)
            sp.points[0].co = (*G[p].translation, 1)
            sp.points[1].co = (*G[n].translation, 1)
        C = G["jx_c_camera"]
        for view in ("eye", "side"):
            if "body" in objs:        # the spine/neck run right past the eye and fill the camera view
                objs["body"].hide_render = (view == "eye")
            if view == "eye":
                cam.data.type = "PERSP"
                cam.data.sensor_fit = "HORIZONTAL"
                cam.data.angle = math.radians(100)
                cam.matrix_world = C @ Matrix.Rotation(math.pi, 4, "Y")
            else:
                cam.data.type = "ORTHO"
                cam.data.ortho_scale = 55
                fwd, up = C.to_3x3().col[2].normalized(), C.to_3x3().col[1].normalized()
                back = fwd.cross(up).normalized()
                cam.matrix_world = Matrix.Translation(C.translation + fwd * 10 - up * 10 + back * 80) @ Matrix((fwd, up, back)).transposed().to_4x4()
            path = os.path.join(D, f"stick_{model}_{tag}_{view}.png")
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            out.append(path)
print("SKELETON_AUDIT_OK", len(out), "renders")
