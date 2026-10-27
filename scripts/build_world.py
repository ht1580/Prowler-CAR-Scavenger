"""blender -b -P build_world.py : Prowler reactive world model on the TF2 CAR world skeleton (QC + SMDs)."""
import bpy
import addon_utils
import json
import math
import os
import re
import sys
import struct
from mathutils import Matrix, Vector, Euler

sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
TPL = r"D:\CodexStorage\Projects\2026-09-08\w-3\work\car_outlands\source\world"
SKIN = r"D:\Apex_鐚庡吔杩涘寲鐨甠v21_scavenger\01_妯″瀷_Models"
OUT = ROOT + r"\build\world"
BODY_MAT = r"models\Weapons_R2\prowler_car\prowler_scavenger"
view = json.load(open(ROOT + r"\build\view\skeleton.json"))["report"]
DELTA = Vector(view["DELTA"])                       # same eye-line shift as the viewmodel
SHELL = Vector(view["shell_rel"])
os.makedirs(OUT, exist_ok=True)

qc_tpl = open(TPL + r"\w_car_richmahogany.qc", encoding="utf-8", errors="replace").read()
bones = []                                           # (name, parent, Matrix local)
for m in re.finditer(r'\$definebone "([^"]+)" "([^"]*)" ([-\d.e]+) ([-\d.e]+) ([-\d.e]+) ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)', qc_tpl):
    n, p = m.group(1), m.group(2) or None
    t = Vector(map(float, m.group(3, 4, 5)))
    ry, rz, rx = (math.radians(float(v)) for v in m.group(6, 7, 8))   # QC = (eulerY, eulerZ, eulerX)
    bones.append([n, p, Matrix.Translation(t) @ Euler((rx, ry, rz), "XYZ").to_matrix().to_4x4()])
names = [b[0] for b in bones]
parent = {b[0]: b[1] for b in bones}
glob = {}
for n, p, loc in bones:
    glob[n] = (glob[p] if p else Matrix.Identity(4)) @ loc
car_g = {n: m.copy() for n, m in glob.items()}


def place(n, pos):
    m = glob[n].copy()
    m.translation = pos
    glob[n] = m


# CAR -> Prowler placements (def_c_base is the grip at the origin in both models)
place("def_c_proscreen", Vector((0.75, 3.29, -10.04)))    # same rear-stock spot as the viewmodel, base-relative
for n in ("ja_ads_attachment", "def_c_sight_on"):
    place(n, car_g[n].translation + DELTA)
for n in ("def_c_holo", "def_c_acgs", "def_c_cro"):
    if n in glob:
        place(n, car_g[n].translation + DELTA)
place("muzzle_flash", Vector((-0.008, 4.006, 5.36)))
for n in ("shell", "shell_fp"):
    if n in glob:
        place(n, SHELL)
ps_shift = glob["def_c_proscreen"].translation - car_g["def_c_proscreen"].translation
# Third-person grip (grip_delta.py, from both guns' own first-person idle poses):
#   the 3P hand holds weapon_bone exactly like the CAR, so the whole Prowler (mesh + child bones) gets
#   T = H_car(right hand) @ inv(H_prw(right hand)) -> it sits in the hand at the Apex grip angle.
#   IK anchors: l_hand_ik pairs with the right (grip) hand -> stays stock; r_hand_ik pairs with the left
#   (support) hand -> retargeted onto the Prowler's front tube with the left-hand relation (pos + rot).
gd = json.load(open(ROOT + r"\build\grip_delta.json"))
T = Matrix(gd["T"])
L_car, L_prw = Matrix(gd["car"]["ja_l_propHand"]), Matrix(gd["prw"]["ja_l_propHand"])
ROOTS = ("ja_c_propGun", "weapon_bone", "def_c_base")
for n in names:
    if n not in ROOTS and n not in ("l_hand_ik", "r_hand_ik"):
        glob[n] = T @ glob[n]
glob["l_hand_ik"] = car_g["l_hand_ik"].copy()
glob["r_hand_ik"] = T @ L_prw @ L_car.inverted() @ car_g["r_hand_ik"]
T3 = T.to_3x3()
# Rigid only: the mesh is never stretched or squashed. The grip hand keeps the stock l_hand_ik (the CAR's
# grip == the Prowler's pipe grip after T) and the support hand IK (r_hand_ik, used in game: stock guns
# carry per-gun values, e.g. Alternator z 2.4 / CAR 8.4 / Hemlok 9.3) sits on the taped front grip.
local = {}
for n in names:
    p = parent[n]
    local[n] = (glob[p].inverted() @ glob[n]) if p else glob[n].copy()
idx = {n: i for i, n in enumerate(names)}
nodes = [(n, idx[parent[n]] if parent[n] else -1) for n in names]


def write_smd(path, frames, tris=None):
    out = ["version 1", "nodes"] + [f'{i} "{n}" {p}' for i, (n, p) in enumerate(nodes)] + ["end", "skeleton"]
    for f, fr in enumerate(frames):
        out.append(f"time {f}")
        for i, n in enumerate(names):
            m = fr[n]
            t, e = m.to_translation(), m.to_euler("XYZ")
            out.append(f"{i} {t.x:.6f} {t.y:.6f} {t.z:.6f} {e.x:.6f} {e.y:.6f} {e.z:.6f}")
    out.append("end")
    if tris is not None:
        out.append("triangles")
        for mat, vs in tris:
            out.append(mat)
            for (p, nrm, uv, links) in vs:
                p, nrm = T @ Vector(p), (T3 @ Vector(nrm)).normalized()     # grip alignment (see above)
                out.append(f"{links[0][0]} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {nrm[0]:.6f} {nrm[1]:.6f} {nrm[2]:.6f} "
                           f"{uv[0]:.6f} {uv[1]:.6f} {len(links)} " + " ".join(f"{b} {w:.6f}" for b, w in links))
        out.append("end")
    open(path, "w", encoding="ascii", newline="\n").write("\n".join(out) + "\n")


def obj_tris(obj, bone):
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    cn = me.corner_normals
    mw = obj.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    tris = []
    for lt in me.loop_triangles:
        vs = []
        for li, vi in zip(lt.loops, lt.vertices):
            p = mw @ me.vertices[vi].co
            n = (nm @ cn[li].vector).normalized()
            vs.append(((p.x, p.y, p.z), (n.x, n.y, n.z), tuple(uv[li].uv), [(idx[bone], 1.0)]))
        tris.append((BODY_MAT, vs))
    return tris


addon_utils.enable("io_scene_cast", default_set=False)
report = {}
for lod in range(4):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.import_scene.cast(filepath=SKIN + rf"\prowler_react_v21_scavenger_w_LOD{lod}.cast")
    meshes = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    body = [o for n, o in meshes.items() if n.startswith("body_0")][0]
    write_smd(OUT + rf"\prowler_w_body_lod{lod}.smd", [local], obj_tris(body, "def_c_base"))
    report[f"lod{lod}"] = len(body.data.polygons)
    if lod == 0:
        rear = [o for n, o in meshes.items() if n.startswith("sight_rear_1")]
        if rear:
            write_smd(OUT + r"\prowler_w_sight_on.smd", [local], obj_tris(rear[0], "def_c_base"))


def restock(src, dst, shift, scale=1.0, pivot=None):
    n, f, tris = read_smd(TPL + "\\" + src)
    nm = {i: x for i, (x, p) in n.items()}
    out = []
    for mat, verts in tris:
        vv = []
        for p in verts:
            pos = Vector(map(float, p[1:4]))
            pos = (pivot + (pos - pivot) * scale + shift) if pivot is not None else pos + shift
            cnt = int(p[9]) if len(p) > 9 else 0
            links = [(idx[nm[int(p[10 + 2 * k])]], float(p[11 + 2 * k])) for k in range(cnt)] or [(idx[nm[int(p[0])]], 1.0)]
            vv.append(((pos.x, pos.y, pos.z), tuple(map(float, p[4:7])), (float(p[7]), float(p[8])), links))
        out.append((mat, vv))
    write_smd(OUT + "\\" + dst, [local], out)


# ps_shift was measured before the grip/fit transforms, which write_smd applies once.
restock("stock_w_holo.smd", "stock_w_holo.smd", DELTA)
restock("stock_w_acgs.smd", "stock_w_acgs.smd", DELTA)
restock("stock_w_cro.smd", "stock_w_cro.smd", DELTA)
restock("stock_w_proscreen.smd", "stock_w_proscreen.smd", ps_shift, 0.65, car_g["def_c_proscreen"].translation)
# World-model sequences: the native original CAR idle (24 frames) keeps the ROOT bone
# ja_c_propGun rotated +90 deg about X in every frame; the third-person hold depends on it. A rest-pose
# (identity root) animation leaves the gun 90 deg off, muzzle up (0.1.8/0.1.9 lobby bug).
STOCK_IDLE = ROOT + r"\stock\world\world_idle.smd"
root_line = next(l for l in open(STOCK_IDLE).read().splitlines() if l.startswith("0 ") and '"' not in l)
rv = list(map(float, root_line.split()[1:7]))
ROOT_POSE = Matrix.Translation(Vector(rv[:3])) @ Euler(rv[3:], "XYZ").to_matrix().to_4x4()
assert abs(rv[3] - math.pi / 2) < 1e-4 and abs(rv[4]) < 1e-6 and abs(rv[5]) < 1e-6, rv
anim_frame = dict(local)
anim_frame["ja_c_propGun"] = ROOT_POSE
stock_idle_nodes, stock_idle_frames, _ = read_smd(STOCK_IDLE)
write_smd(OUT + r"\world_idle.smd", [anim_frame] * len(stock_idle_frames))
report["world_anim_root_euler"] = rv[3:]

# QC: template definebones/attachments with new values, Prowler bodygroups + LODs
qc = qc_tpl
for n in names:
    m = local[n]
    t = m.to_translation()
    e = [math.degrees(a) for a in m.to_euler("XYZ")]
    qc = re.sub(r'\$definebone "' + re.escape(n) + r'" ("[^"]*") [^\n]*',
                lambda mm: f'$definebone "{n}" {mm.group(1)} {t.x:.6f} {t.y:.6f} {t.z:.6f} {e[1]:.6f} {e[2]:.6f} {e[0]:.6f}', qc)
qc = qc.replace("car_lgnd_v21_retromodern_w_body_0_lod0.smd", "prowler_w_body_lod0.smd")
qc = qc.replace("car_lgnd_v21_retromodern_w_body_0_lod1.smd", "prowler_w_body_lod1.smd")
qc = qc.replace("car_lgnd_v21_retromodern_w_body_0_lod2.smd", "prowler_w_body_lod2.smd")
qc = qc.replace("car_lgnd_v21_retromodern_w_body_0_lod3.smd", "prowler_w_body_lod3.smd")
qc = qc.replace("stock_w_car101_sight_on.smd", "prowler_w_sight_on.smd")
# stock w_car101 sequence table (read from the stock MDL with mdl_seq_dump.py): same names, order,
# activities and events, so server-networked sequence indices and the 3P muzzle flash / shell eject work
attack = ('\tactivity "ACT_RANGE_ATTACK_SMG1" 1\n'
          '\t{ event AE_CL_VSCRIPT_CALLBACK 0 "muzzle_flash" }\n'
          '\t{ event AE_CL_VSCRIPT_CALLBACK 0 "shell_eject" }\n'
          '\t{ event 3002 0 "" }\n\tfadein 0.2\n\tfadeout 0.2\n\tfps 30\n')
seqs = ('$sequence "idle_seq" {\n\t"world_idle.smd"\n\tactivity "ACT_VM_IDLE" 1\n\tfadein 0.2\n\tfadeout 0.2\n\tfps 30\n\tloop\n}\n'
        + "".join(f'$sequence "{n}" {{\n\t"world_idle.smd"\n{attack}}}\n' for n in ("attack_seq", "attack_seq_alt1", "attack_seq_alt2")))
qc, nsub = re.subn(r'\$sequence "idle" \{[^}]*\}\n?', lambda m: seqs, qc)
assert nsub == 1, "world idle sequence block not found in template"
qc = re.sub(r'models\\Weapons_R2\\codex_car_outlands\\car_outlands', BODY_MAT.replace("\\", "\\\\"), qc)
# stock w_car101 muzzle_flash attachment has no offset (Codex template had +0.65 y)
qc = qc.replace('$attachment "muzzle_flash" "muzzle_flash" 0.0 0.65 0.0', '$attachment "muzzle_flash" "muzzle_flash" 0.0 0.0 0.0')
assert '"muzzle_flash" "muzzle_flash" 0.0 0.0 0.0' in qc
open(OUT + r"\w_car101.qc", "w", encoding="ascii", newline="\n").write(qc)
report["proscreen_shift"] = list(ps_shift)
report["world_frames"] = len(stock_idle_frames)
report["grip_T_translation"] = list(T.to_translation())
report["grip_T_euler_deg"] = [math.degrees(a) for a in T.to_euler("XYZ")]
report["r_hand_ik"] = list(glob["r_hand_ik"].to_translation())
json.dump(report, open(OUT + r"\build_report.json", "w"), indent=1)
print("BUILD_WORLD_OK", report)

