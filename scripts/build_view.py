"""Build the Prowler->CAR first-person model sources (SMD + QC) in Blender background mode.

blender -b -P build_view.py

Inputs
  stock/view                      stock CAR decompile (QC, ref meshes, 124 anims)
  r5r_anims/...ptpov_prowler_smg  R5R Prowler rig rest + 97 viewmodel animations
  apex_react/...animRig.smd       reactive skin rig rest (spinner/spring/wheel bones)
  Apex_..._v21_scavenger          reactive skin cast mesh + textures
Outputs
  build/view/*.smd, ptpov_car101.qc, build/view/build_report.json
"""
import bpy
import addon_utils
import json
import math
import os
import re
import shutil
import sys
from mathutils import Matrix, Vector, Quaternion

sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
STOCK = ROOT + r"\stock\view"
CARA = STOCK + r"\ptpov_car101_anims"
PRWR = ROOT + r"\r5r_anims\mdl\Weapons\prowler_smg\ptpov_prowler_smg_body_0_lod0.smd"
PRWA = ROOT + r"\r5r_anims\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg"
REAR = ROOT + r"\apex_react\animrig\techart\mshop\weapons\class\smg\prowler\prowler_react_v21_scavenger_v_animRig.smd"
SKIN = r"D:\Apex_鐚庡吔杩涘寲鐨甠v21_scavenger"
CAST = SKIN + r"\01_妯″瀷_Models\prowler_react_v21_scavenger_v_LOD0.cast"
ILM = SKIN + r"\02_璐村浘_Textures\鍩虹鑹瞋base\prowler_v21_react_scavenger_ilm.png"
OUT = ROOT + r"\build\view"
ANIMOUT = OUT + r"\anims"

BODY_MAT = r"models\Weapons_R2\prowler_car\prowler_scavenger"
GLOW_MAT = r"models\Weapons_R2\prowler_car\prowler_coil_glow"
SPIN_KEYS = 8
SPIN_BONES = {                     # bone -> (world axis = gun forward, turns per pose-parameter cycle)
    "def_c_reactive_spinner_coils": (Vector((0, 0, 1)), 1.0),
    "def_c_reactive_spinner_1": (Vector((0, 0, 1)), -1.0),
    "def_c_reactive_spinner_2": (Vector((0, 0, 1)), 1.0),
}
report = {}


# ---------------------------------------------------------------- helpers
def write_smd(path, nodes, frames, tris=None):
    """nodes: list of (name, parent_index); frames: list of list[Matrix local]."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = ["version 1", "nodes"]
    out += [f'{i} "{n}" {p}' for i, (n, p) in enumerate(nodes)]
    out += ["end", "skeleton"]
    for f, locs in enumerate(frames):
        out.append(f"time {f}")
        for i, m in enumerate(locs):
            t = m.to_translation()
            e = m.to_euler("XYZ")
            vals = (t.x, t.y, t.z, e.x, e.y, e.z)
            assert all(math.isfinite(v) and abs(v) < 1e5 for v in vals), (path, f, nodes[i][0])
            out.append(f"{i} " + " ".join(f"{v:.6f}" for v in vals))
    out.append("end")
    if tris is not None:
        out.append("triangles")
        for mat, verts in tris:
            out.append(mat)
            for (p, n, uv, links) in verts:
                ls = " ".join(f"{b} {w:.6f}" for b, w in links)
                out.append(f"{links[0][0]} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f} {n[0]:.6f} {n[1]:.6f} {n[2]:.6f} "
                           f"{uv[0]:.6f} {uv[1]:.6f} {len(links)} {ls}")
        out.append("end")
    open(path, "w", encoding="ascii", newline="\n").write("\n".join(out) + "\n")


def lerp_mat(a, b, t):
    ta, tb = a.to_translation(), b.to_translation()
    qa, qb = a.to_quaternion(), b.to_quaternion()
    return Matrix.Translation(ta.lerp(tb, t)) @ qa.slerp(qb, t).to_matrix().to_4x4()


def sample(frames, nodes, t):
    """Interpolated local pose dict at fractional frame t."""
    t = max(0.0, min(t, len(frames) - 1))
    lo = int(math.floor(t))
    hi = min(lo + 1, len(frames) - 1)
    mix = t - lo
    if mix < 1e-6:
        return dict(frames[lo])
    return {i: lerp_mat(frames[lo][i], frames[hi].get(i, frames[lo][i]), mix) for i in frames[lo]}


# ---------------------------------------------------------------- skeletons
car_n, car_f, _ = read_smd(STOCK + r"\v_car101.smd")
car_rest_g = by_name(car_n, globals_(car_n, car_f[0]))
prw_n, prw_f, _ = read_smd(PRWR)
prw_rest_g = by_name(prw_n, globals_(prw_n, prw_f[0]))
rea_n, rea_f, _ = read_smd(REAR)
rea_rest_g = by_name(rea_n, globals_(rea_n, rea_f[0]))
rea_parent = {n: (rea_n[p][0] if p >= 0 else None) for i, (n, p) in rea_n.items()}

car_order = [car_n[i][0] for i in sorted(car_n)]
car_parent = {car_n[i][0]: (car_n[car_n[i][1]][0] if car_n[i][1] >= 0 else None) for i in car_n}

# eye point (camera) in def_c_base space at full ADS, CAR vs Prowler
def ads_eye(path):
    n, f, _ = read_smd(path)
    g = by_name(n, globals_(n, f[-1]))
    return (g["def_c_base"].inverted() @ g["jx_c_camera"]).to_translation()


E_car = ads_eye(CARA + r"\ads_in_anim.smd")
E_prw = ads_eye(PRWA + r"\ptpov_prowler_smg_ads_in_dmx__1C9BD1BA.smd")
base_rest = prw_rest_g["def_c_base"]
DELTA = base_rest.to_3x3() @ (E_prw - E_car)          # optic shift in model space
report["eye_car_base"] = list(E_car)
report["eye_prw_base"] = list(E_prw)
report["optic_shift_model"] = list(DELTA)

# ---------------------------------------------------------------- reactive cast mesh
addon_utils.enable("io_scene_cast", default_set=False)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.cast(filepath=CAST)
cast_arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
cast_heads = {b.name: (cast_arm.matrix_world @ b.head_local) for b in cast_arm.data.bones}

# extra bones appended after the CAR skeleton (keeps CAR indices -> stock RUI parents stay valid)
extra = [n for n in [rea_n[i][0] for i in sorted(rea_n)] if n not in car_order and
         (n.startswith("def_c_reactive") or "reactive" in n or n in ("def_c_bolt_end",))]
final_order = car_order + extra
final_parent = dict(car_parent)
for n in extra:
    p = rea_parent[n]
    final_parent[n] = p if p in final_order else "def_c_base"
report["extra_bones"] = extra

# proscreen relocation: put the pro-screen on the tank counter ("0000") on the player-facing side
# (the counter window itself carries the ammo RUI, see rui_fix.py; pro screen goes on the tank's front half)
PS_TARGET = Vector((0.75, 46.60, -0.20))
PS_SCALE = 0.65
PS_SHIFT = PS_TARGET - car_rest_g["def_c_proscreen"].to_translation()
report["proscreen_shift"] = list(PS_SHIFT)

# TF2 optic bones keep the stock CAR placement + eye-line shift (stock attachments/RUI stay valid),
# even though the Prowler rig has same-named Apex optic bones.
OPTIC_BONES = ("def_c_holo", "def_c_acgs", "def_c_cro", "def_c_sight_on")
rest_g = {}
for n in final_order:
    if n in OPTIC_BONES:
        rest_g[n] = Matrix.Translation(DELTA) @ car_rest_g[n]
    elif n in prw_rest_g:
        rest_g[n] = prw_rest_g[n].copy()
    elif n in rea_rest_g:
        rest_g[n] = rea_rest_g[n].copy()
    elif n == "def_c_proscreen":
        rest_g[n] = Matrix.Translation(PS_SHIFT) @ car_rest_g[n]
    elif n == "muzzle_flash":
        m = car_rest_g[n].copy()
        m.translation = cast_heads["muzzle_flash"]
        rest_g[n] = m
    elif n == "def_c_magazine1":
        rest_g[n] = prw_rest_g["def_c_magazine"].copy()
    else:
        rest_g[n] = car_rest_g[n].copy()
CAR_ONLY = [n for n in final_order if (n not in prw_rest_g and n not in rea_rest_g) or n in OPTIC_BONES]
report["car_only_bones"] = CAR_ONLY
idx = {n: i for i, n in enumerate(final_order)}
nodes = [(n, idx[final_parent[n]] if final_parent[n] else -1) for n in final_order]


def to_locals(gmap):
    out = []
    for n in final_order:
        p = final_parent[n]
        out.append((gmap[p].inverted() @ gmap[n]) if p else gmap[n].copy())
    return out


rest_local = to_locals(rest_g)
rest_local_by = dict(zip(final_order, rest_local))


# ---------------------------------------------------------------- meshes
def mesh_tris(obj, matname, bone_map, offset=Vector((0, 0, 0)), normal_push=0.0, face_filter=None):
    me = obj.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    cn = me.corner_normals if hasattr(me, "corner_normals") else None
    groups = {g.index: g.name for g in obj.vertex_groups}
    mw = obj.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    tris = []
    for lt in me.loop_triangles:
        if face_filter and not face_filter(me, lt):
            continue
        verts = []
        for li, vi in zip(lt.loops, lt.vertices):
            v = me.vertices[vi]
            n = (nm @ (cn[li].vector if cn else v.normal)).normalized()
            p = mw @ v.co + n * normal_push + offset
            links = []
            for g in v.groups:
                if g.weight > 0.001:
                    b = bone_map(groups[g.group])
                    links.append([idx[b], g.weight])
            if not links:
                links = [[idx["def_c_base"], 1.0]]
            merged = {}
            for b, w in links:
                merged[b] = merged.get(b, 0) + w
            tot = sum(merged.values())
            links = sorted(([b, w / tot] for b, w in merged.items()), key=lambda x: -x[1])[:3]
            tot = sum(w for _, w in links)
            links = [(b, w / tot) for b, w in links]
            u = uv[li].uv
            verts.append(((p.x, p.y, p.z), (n.x, n.y, n.z), (u.x, u.y), links))
        tris.append((matname, verts))
    return tris


def bone_map(name):
    while name not in idx:
        name = rea_parent.get(name) or "def_c_base"
    return name


objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
body = [o for n, o in objs.items() if n.startswith("body_0")][0]
clip = [o for n, o in objs.items() if n.startswith("clip_0")][0]
irons = [o for n, o in objs.items() if n.startswith("sight_front_1")][0]

# iron sight mesh is skinned to ja_ads_attachment in Apex; bind it to def_c_sight_on? no - keep ja_ads (Prowler-driven)
write_smd(OUT + r"\prowler_body.smd", nodes, [rest_local], mesh_tris(body, BODY_MAT, bone_map))
write_smd(OUT + r"\prowler_magazine.smd", nodes, [rest_local], mesh_tris(clip, BODY_MAT, lambda n: "def_c_magazine"))
write_smd(OUT + r"\prowler_sight_on.smd", nodes, [rest_local], mesh_tris(irons, BODY_MAT, lambda n: "ja_ads_attachment"))

# glow overlay: body faces whose UVs land on lit ILM texels (hot coil wire)
img = bpy.data.images.load(ILM)
W, H = img.size
px = list(img.pixels)


def ilm_at(u, v):
    x = min(W - 1, max(0, int(u % 1.0 * W)))
    y = min(H - 1, max(0, int(v % 1.0 * H)))
    k = (y * W + x) * 4
    return max(px[k], px[k + 1], px[k + 2])


def glow_filter(me, lt):
    uv = me.uv_layers.active.data
    pts = [uv[li].uv for li in lt.loops]
    c = (sum(p.x for p in pts) / 3, sum(p.y for p in pts) / 3)
    return max([ilm_at(c[0], c[1])] + [ilm_at(p.x, p.y) for p in pts]) > 0.20


glow = mesh_tris(body, GLOW_MAT, bone_map, normal_push=0.004, face_filter=glow_filter)
write_smd(OUT + r"\prowler_glow.smd", nodes, [rest_local], glow)
report["glow_tris"] = len(glow)
report["glow_bones"] = sorted({final_order[l[0]] for _, vs in glow for (_, _, _, ls) in vs for l in ls})


# stock TF2 optics / proscreen, re-skinned onto the new skeleton and shifted
def restock(src, dst, shift, scale=1.0, pivot=None):
    n, f, tris = read_smd(STOCK + "\\" + src)
    names = {i: nm for i, (nm, p) in n.items()}
    out = []
    for mat, verts in tris:
        vv = []
        for p in verts:
            pos = Vector(map(float, p[1:4]))
            pos = (pivot + (pos - pivot) * scale + shift) if pivot is not None else pos + shift
            nrm = tuple(map(float, p[4:7]))
            uv = (float(p[7]), float(p[8]))
            cnt = int(p[9]) if len(p) > 9 else 0
            links = [(idx[names[int(p[10 + 2 * k])]], float(p[11 + 2 * k])) for k in range(cnt)] or [(idx[names[int(p[0])]], 1.0)]
            vv.append(((pos.x, pos.y, pos.z), nrm, uv, links))
        out.append((mat, vv))
    write_smd(OUT + "\\" + dst, nodes, [rest_local], out)


restock("v_holo.smd", "v_holo.smd", DELTA)
restock("v_acgs.smd", "v_acgs.smd", DELTA)
restock("v_cro.smd", "v_cro.smd", DELTA)
restock("v_proscreen.smd", "v_proscreen.smd", PS_SHIFT, PS_SCALE, car_rest_g["def_c_proscreen"].to_translation())
report["proscreen_scale"] = PS_SCALE
write_smd(OUT + r"\ref.smd", nodes, [rest_local])
# sequence 0 "ref" must be THIS skeleton's bind pose (the stock anims\ref.smd holds the CAR rest:
# e.g. def_c_magazine 13" forward of the Prowler's magazine well)
write_smd(ANIMOUT + r"\ref.smd", nodes, [rest_local])

# ---------------------------------------------------------------- spin / fire layers (delta anims)
def delta_pose(changes):
    """changes: {bone: Matrix delta-local}; zero elsewhere -> list of local deltas (identity)."""
    return [changes.get(n, Matrix.Identity(4)) for n in final_order]


def spin_delta(bone, axis_world, angle):
    r = rest_g[bone].to_3x3()
    axis_local = (r.inverted() @ axis_world).normalized()
    return Quaternion(axis_local, angle).to_matrix().to_4x4()


# Drum spin = script-driven looping pose parameter "prowler_spin" (0..1 = one turn) blending these keys in an
# autoplay delta layer. Not in the fire deltas: a delta can't accumulate rotation over shots, so 0.1.14-0.1.16
# had to spin whole turns per shot (14 turns/s coils, 28 rings) -> strobing, "flying" drum in game.
# 8 keys over 0..360 deg (key 7 == key 0, seamless wrap; MDLShit corrupted the 9th index of a 9-key blend).
spin_files = []
for k in range(SPIN_KEYS):
    frac = k / (SPIN_KEYS - 1)
    ch = {b: spin_delta(b, ax, turns * 2 * math.pi * frac) for b, (ax, turns) in SPIN_BONES.items() if b in idx}
    fn = f"prowler_spin_{k}.smd"
    write_smd(ANIMOUT + "\\" + fn, nodes, [delta_pose(ch)])
    spin_files.append(fn)
report["spin_keys"] = spin_files


def fire_kick(nframes):
    """Per-shot spring compression + bolt kick, as delta frames (returns to zero)."""
    springs = [n for n in final_order if n.startswith("def_c_reactive_spring_")]
    frames = []
    for f in range(nframes):
        a = 1.0 if f == 1 else (0.6 if f == 2 else (0.25 if f == 3 else 0.0))
        ch = {}
        for s in springs[1:]:
            ch[s] = Matrix.Translation(-0.35 * a * rest_local_by[s].to_translation())
        if "def_c_bolt" in idx:
            back = rest_g["def_c_base"].to_3x3().inverted() @ Vector((0, 0, -0.45 * a))
            ch["def_c_bolt"] = Matrix.Translation(back)
        frames.append(delta_pose(ch))
    return frames


report["DELTA"] = list(DELTA)
report["shell_rel"] = list(rest_g["def_c_base"].inverted() @ cast_heads["shell"])
json.dump({"final_order": final_order, "final_parent": final_parent, "car_only": CAR_ONLY,
           "rest_local": {n: [list(r) for r in m] for n, m in rest_local_by.items()},
           "rest_global": {n: [list(r) for r in m] for n, m in rest_g.items()}, "report": report},
          open(OUT + r"\skeleton.json", "w"), indent=1)

# ---------------------------------------------------------------- animation retarget
# CAR absolute animation -> Prowler source (R5R). None = generated from Prowler idle frames.
P = {
    "ads_in": "ptpov_prowler_smg_ads_in_dmx__1C9BD1BA", "ads_out": "ptpov_prowler_smg_ads_out_dmx__80BB161B",
    "ads_in_slide": "ptpov_prowler_smg_ads_in_slide_dmx__5A0B27B", "ads_out_slide": "ptpov_prowler_smg_ads_out_slide_dmx__DB8A79B7",
    "oh_ads_in": "ptpov_prowler_smg_onehanded_ads_in_dmx__83E9248E", "oh_ads_out": "ptpov_prowler_smg_onehanded_ads_out_dmx__5CC0CFE",
    "pullout": "ptpov_prowler_smg_pullout_dmx__D2F7243", "pullout_crouch": "ptpov_prowler_smg_pullout_crouch_dmx__521EA5E3",
    "first_pullout": "ptpov_prowler_smg_first_pullout_dmx__3382FD23", "first_pullout_crouch": "ptpov_prowler_smg_first_pullout_crouch_dmx__BB857983",
    "oh_pullout": "ptpov_prowler_smg_onehanded_pullout_dmx__EA0BAC9F", "oh_first_pullout": "ptpov_prowler_smg_onehanded_first_pullout_dmx__2E7D861D",
    "putaway": "ptpov_prowler_smg_putaway_dmx__B23CFF6", "oh_putaway": "ptpov_prowler_smg_onehanded_putaway_dmx__F5412C20",
    "raise": "ptpov_prowler_smg_raise_dmx__F30C0F05", "raise_crouch": "ptpov_prowler_smg_raise_crouch_dmx__429BD4CB",
    "oh_raise": "ptpov_prowler_smg_onehanded_raise_dmx__C45C15C5",
    "lower": "ptpov_prowler_smg_lower_dmx__32F15E2", "oh_lower": "ptpov_prowler_smg_onehanded_lower_dmx__36E1F895",
    "reload": "ptpov_prowler_smg_reload_01_dmx__4C976C7A", "reload_crouch": "ptpov_prowler_smg_reload_crouch_02_dmx__AA991656",
    "reload_empty": "ptpov_prowler_smg_reload_empty_01_dmx__7E41644", "reload_empty_crouch": "ptpov_prowler_smg_reload_empty_crouch_02_dmx__970E6523",
    "oh_reload": "ptpov_prowler_smg_onehanded_reload_01_dmx__F5E3964F", "oh_reload_empty": "ptpov_prowler_smg_onehanded_reload_empty_01_dmx__DD71CA26",
    "sprint": "ptpov_prowler_smg_sprint_noroll_dmx__36_loop_508CF1DD", "oh_sprint": "ptpov_prowler_smg_onehanded_sprint_dmx__36_loop_A77FAD69",
    "sprint_raise": "ptpov_prowler_smg_sprint_raise_dmx__827EA878", "oh_sprint_raise": "ptpov_prowler_smg_onehanded_sprint_raise_dmx__E7132E18",
    "sprint_pullout": "ptpov_prowler_smg_sprint_pullout_dmx__A93C7D37", "sprint_putaway": "ptpov_prowler_smg_sprint_putaway_dmx__DDC59DB2",
    "to_oh": "ptpov_prowler_smg_switch_to_onehanded_dmx__5973A669", "to_th": "ptpov_prowler_smg_switch_to_twohanded_dmx__B1E502B9",
    "idle": "ptpov_prowler_smg_idle_dmx__33_DCFF7D84",
}
MAP = {
    "ads_in_anim": "ads_in", "ads_in_anim_alt1": "ads_in", "ads_in_anim_alt2": "ads_in", "ads_in_anim_alt3": "ads_in",
    "ads_out_anim": "ads_out", "ads_out_anim_alt1": "ads_out", "ads_out_anim_alt2": "ads_out", "ads_out_anim_alt3": "ads_out",
    "ads_in_slide_anim": "ads_in_slide", "ads_in_slide_aog_anim": "ads_in_slide", "ads_in_slide_hcog_anim": "ads_in_slide", "ads_in_slide_holo_anim": "ads_in_slide",
    "ads_out_slide_anim": "ads_out_slide", "ads_out_slide_aog_anim": "ads_out_slide", "ads_out_slide_hcog_anim": "ads_out_slide", "ads_out_slide_holo_anim": "ads_out_slide",
    "ads_in_onehanded_anim": "oh_ads_in", "ads_in_onehanded_anim_alt1": "oh_ads_in", "ads_in_onehanded_anim_alt2": "oh_ads_in", "ads_in_onehanded_anim_alt3": "oh_ads_in",
    "ads_out_onehanded_anim": "oh_ads_out", "ads_out_onehanded_anim_alt1": "oh_ads_out", "ads_out_onehanded_anim_alt2": "oh_ads_out", "ads_out_onehanded_anim_alt3": "oh_ads_out",
    "draw_seq": "pullout", "draw_crouch_seq": "pullout_crouch", "drawfirst_seq": "first_pullout", "drawfirst_crouch_seq": "first_pullout_crouch",
    "draw_onehanded_seq": "oh_pullout", "draw_onehanded_crouch_seq": "oh_pullout", "drawfirst_onehanded_seq": "oh_first_pullout",
    "holster_seq": "putaway", "holster_onehanded_seq": "oh_putaway",
    "raise_seq": "raise", "raise_frommelee_seq": "raise", "raise_frommelee_sliding_seq": "raise",
    "raise_crouch_seq": "raise_crouch", "raise_frommelee_crouch_seq": "raise_crouch",
    "raise_onehanded_seq": "oh_raise", "raise_onehanded_crouch_seq": "oh_raise",
    "lower_seq": "lower", "lower_onehanded_seq": "oh_lower",
    "reload_seq": "reload", "reload_crouch_seq": "reload_crouch",
    "reload_empty_seq": "reload_empty", "reload_empty_crouch_seq": "reload_empty_crouch",
    "reload_onehanded_seq": "oh_reload", "reload_onehanded_crouch_seq": "oh_reload",
    "reload_empty_onehanded_seq": "oh_reload_empty", "reload_empty_onehanded_crouch_seq": "oh_reload_empty",
    "sprint_seq": "sprint", "sprint_onehanded_seq": "oh_sprint",
    "sprintraise_seq": "sprint_raise", "sprintraise_seq_regrip": "sprint_raise", "sprintraise_seq_air": "sprint_raise",
    "sprintraise_onehanded_seq": "oh_sprint_raise", "sprintraise_onehanded_slide_anim": "oh_sprint_raise",
    "sprintdraw_seq": "sprint_pullout", "sprintdraw_onehanded_seq": "sprint_pullout",
    "sprintholster_seq": "sprint_putaway", "sprintholster_onehanded_seq": "sprint_putaway",
    "switch_to_onehanded_anim": "to_oh", "switch_to_twohanded_anim": "to_th",
    "idle_check_anim_nod": "idle", "iron_anim_nod": "idle",
}
# late reload segments: (car late anim, car full seq anim file, full-seq event name used to align)
LATE = {
    "reload_late1_anim": "reload_seq", "reload_late1_crouch_anim": "reload_crouch_seq",
    "reload_empty_late1_anim": "reload_empty_seq", "reload_empty_late2_anim": "reload_empty_seq",
    "reload_empty_late1_crouch_anim": "reload_empty_crouch_seq", "reload_empty_late2_crouch_anim": "reload_empty_crouch_seq",
    "reload_onehanded_late1_anim": "reload_onehanded_seq", "reload_onehanded_late1_crouch_anim": "reload_onehanded_crouch_seq",
    "reload_empty_onehanded_late1_anim": "reload_empty_onehanded_seq", "reload_empty_onehanded_late2_anim": "reload_empty_onehanded_seq",
    "reload_empty_onehanded_late1_crouch_anim": "reload_empty_onehanded_crouch_seq",
    "reload_empty_onehanded_late2_crouch_anim": "reload_empty_onehanded_crouch_seq",
}

qc_text = open(STOCK + r"\ptpov_car101.qc", encoding="utf-8", errors="replace").read()


def seq_events(seq):
    m = re.search(r'\$sequence\s+"' + re.escape(seq) + r'"\s*\{(.*?)\n\}', qc_text, re.S)
    return {e: int(fr) for e, fr in re.findall(r"event\s+(\w+)\s+(\d+)", m.group(1))} if m else {}


def mag_keys(nodes_p, frames_p):
    """(mag leaves seat, mag reseated) frames from def_c_magazine offset vs def_c_base."""
    nb = by_name
    out = []
    rest = None
    for i, fr in enumerate(frames_p):
        g = nb(nodes_p, globals_(nodes_p, fr))
        rel = (g["def_c_base"].inverted() @ g["def_c_magazine"]).to_translation()
        if rest is None:
            rest = rel
        out.append((rel - rest).length)
    moving = [i for i, d in enumerate(out) if d > 0.25]
    return (moving[0], moving[-1]) if moving else (None, None)


def warp_fn(keys_dst, keys_src):
    """piecewise-linear dst frame -> src frame through matching key pairs."""
    pairs = sorted(zip(keys_dst, keys_src))

    def f(x):
        for (d0, s0), (d1, s1) in zip(pairs, pairs[1:]):
            if d0 <= x <= d1:
                return s0 + (s1 - s0) * ((x - d0) / max(1e-6, d1 - d0))
        return pairs[-1][1] if x > pairs[-1][0] else pairs[0][1]
    return f


cache = {}


def load_prw(key):
    if key not in cache:
        n, f, _ = read_smd(PRWA + "\\" + P[key] + ".smd")
        cache[key] = (n, f, {nm: i for i, (nm, p) in n.items()})
    return cache[key]


def retarget(key, n_out, warp):
    n_p, f_p, ix_p = load_prw(key)
    frames = []
    for fo in range(n_out):
        loc = sample(f_p, n_p, warp(fo))
        g = by_name(n_p, globals_(n_p, loc))
        gm = {}
        for n in final_order:
            if n in g and n not in CAR_ONLY:
                gm[n] = g[n]
            else:
                p = final_parent[n]
                gm[n] = (gm[p] if p else Matrix.Identity(4)) @ rest_local_by[n]
            if n == "def_c_magazine1" and "def_c_magazine" in gm:
                gm[n] = gm["def_c_magazine"].copy()
        frames.append(to_locals(gm))
    return frames


anim_report = []
full_cache = {}
for car_anim, key in MAP.items():
    cn, cf, _ = read_smd(CARA + "\\" + car_anim + ".smd")
    n_out = len(cf)
    n_p, f_p, _ = load_prw(key)
    n_src = len(f_p)
    seqname = car_anim if car_anim.endswith("_seq") else None
    if key.endswith("reload") or "reload_empty" in key or key.endswith("reload_crouch"):
        ev = seq_events(car_anim)
        s_out, s_in = mag_keys(n_p, f_p)
        d_pull = ev.get("AE_WPN_RELOAD_MILESTONE_1", ev.get("AE_WPN_FILLAMMO", n_out // 3)) - 3
        d_insert = ev.get("AE_WPN_FILLAMMO", (2 * n_out) // 3) - 6
        if s_out is not None and 0 < d_pull < d_insert < n_out - 1:
            warp = warp_fn([0, d_pull, d_insert, n_out - 1], [0, s_out, s_in, n_src - 1])
            how = f"timewarp mag {s_out}->{d_pull}, {s_in}->{d_insert}"
        else:
            warp = warp_fn([0, n_out - 1], [0, n_src - 1])
            how = "linear"
    elif key in ("sprint", "oh_sprint", "idle"):
        warp = (lambda x, ns=n_src, no=n_out: x * (ns - 1) / max(1, no - 1)) if key != "idle" else (lambda x: x % n_src)
        how = "loop-stretch" if key != "idle" else "frames"
    else:
        warp = warp_fn([0, n_out - 1], [0, n_src - 1])
        how = "linear"
    fr = retarget(key, n_out, warp)
    full_cache[car_anim] = (fr, warp, n_src)
    write_smd(ANIMOUT + "\\" + car_anim + ".smd", nodes, fr)
    anim_report.append({"anim": car_anim, "src": P[key], "frames": n_out, "srcFrames": n_src, "warp": how})

# late segments: slice the converted full reload from the READYTOFIRE alignment (Codex merge_native_reload rule)
for late, full_seq in LATE.items():
    cn, cf, _ = read_smd(CARA + "\\" + late + ".smd")
    n_out = len(cf)
    full_frames = full_cache[full_seq][0]
    late_seq = late.replace("_anim", "_seq")
    late_seq = re.sub(r"_crouch_seq$", "_crouch_seq", late_seq)
    rf_full = seq_events(full_seq).get("AE_WPN_READYTOFIRE")
    rf_late = seq_events(late_seq).get("AE_WPN_READYTOFIRE")
    start = (rf_full - rf_late) if (rf_full is not None and rf_late is not None) else len(full_frames) - n_out
    start = max(0, min(start, len(full_frames) - 1))
    fr = [full_frames[min(start + k, len(full_frames) - 1)] for k in range(n_out)]
    write_smd(ANIMOUT + "\\" + late + ".smd", nodes, fr)
    anim_report.append({"anim": late, "slicedFrom": full_seq, "start": start, "frames": n_out})

# fire deltas: copy CAR deltas onto the new skeleton, add spring/bolt kick (the drum is the spin layer's)
for att in ("attack_anim", "attack_ads_anim", "attack_slide_anim", "attack_onehanded_anim", "attack_onehanded_ads_anim"):
    cn, cf, _ = read_smd(CARA + "\\" + att + ".smd")
    names = {i: nm for i, (nm, p) in cn.items()}
    kick = fire_kick(len(cf))
    frames = []
    for f, fr in enumerate(cf):
        car_by = {names[i]: m for i, m in fr.items()}
        frames.append([kick[f][k] if final_order[k] in ("def_c_bolt",) or final_order[k].startswith("def_c_reactive_spring")
                       else car_by.get(final_order[k], Matrix.Identity(4)) for k in range(len(final_order))])
    write_smd(ANIMOUT + "\\" + att + ".smd", nodes, frames)
    anim_report.append({"anim": att, "delta": True, "added": "spring+bolt kick"})

report["anims"] = anim_report
json.dump(report, open(OUT + r"\build_report.json", "w"), indent=1)
print("BUILD_VIEW_OK", len(anim_report), "anims", report["glow_tris"], "glow tris")


