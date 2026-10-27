"""blender -b --factory-startup -P retarget_arms.py : fit the Apex (Prowler) first-person poses to the TF2
pilot arms. Runs after build_view.py and before gen_qc.py, on build/view/anims/*.smd (full poses only).

Why: the game bonemerges the TF2 pilot arms model (models/weapons/arms/pov_pilot_*.mdl) onto the viewmodel by
bone name. The Apex rig is ~2 units taller at the spine and its clavicles are rolled forward, so with the TF2
arms mesh (full sleeves + shoulders, Apex arms have none) the shoulders and upper arms end up in front of the
camera (left shoulder 3.1 units ahead of the eye; stock CAR keeps it 0.9 behind) -> arm chunks / a "floating
hand" fill the view (sim_fp_arms.py shows it with the real arms mesh).

What (per frame, world space):
  * body above the arms (hip/spine/neck/head/clavicles) = the stock CAR hip pose (draw_seq end) locals;
  * gun (ja_c_propGun subtree) and both hands (def_*_wrist subtree) keep their exact Prowler world pose;
  * shoulder -> elbow -> wrist is re-solved with two-bone IK from the new shoulder to the unchanged wrist,
    keeping the original bend plane (pole = where the Prowler elbow pointed).
Delta animations (stock delta descriptors) and ref.smd are left alone."""
import math
import os
import sys
from mathutils import Matrix, Vector
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name
from mdl_lib import Mdl

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
ANIMS = ROOT + r"\build\view\anims"
STOCK_ANIMS = ROOT + r"\stock\view\ptpov_car101_anims"
BODY = ("def_c_hip", "def_c_spineA", "def_c_spineB", "def_c_spineC", "def_c_neckA", "jx_c_neckB", "def_c_neckB",
        "def_c_head", "def_l_clav", "def_r_clav")
KEEP_WORLD = ("ja_c_propGun", "def_l_wrist", "def_r_wrist")
REACH = 0.97

stock_mdl = Mdl(ROOT + r"\stock\models\weapons\car101\ptpov_car101.mdl")
DELTA = {name for row, name in stock_mdl.table(184, 92, 4) if stock_mdl.i(row + 12) & 4}

sn, sf, _ = read_smd(STOCK_ANIMS + r"\draw_seq.smd")
stock_local = {sn[i][0]: m for i, m in sf[-1].items()}


def write_smd(path, nodes, frames, tail):
    out = ["version 1", "nodes"] + [f'{i} "{nodes[i][0]}" {nodes[i][1]}' for i in sorted(nodes)] + ["end", "skeleton"]
    for f, locs in enumerate(frames):
        out.append(f"time {f}")
        for i in sorted(locs):
            t, e = locs[i].to_translation(), locs[i].to_euler("XYZ")
            vals = (t.x, t.y, t.z, e.x, e.y, e.z)
            assert all(math.isfinite(v) for v in vals), (path, f, nodes[i][0])
            out.append(f"{i} " + " ".join(f"{v:.6f}" for v in vals))
    out.append("end")
    open(path, "w", encoding="ascii", newline="\n").write("\n".join(out + tail) + "\n")


def rot_between(a, b):
    return a.normalized().rotation_difference(b.normalized()).to_matrix().to_4x4()


def about(p, R):
    return Matrix.Translation(p) @ R @ Matrix.Translation(-p)


def retarget_frame(nodes, local):
    idx = {nm: i for i, (nm, _) in nodes.items()}
    par = {i: p for i, (_, p) in nodes.items()}
    G = globals_(nodes, local)
    L = dict(local)
    for nm in BODY:
        if nm in idx and nm in stock_local:
            L[idx[nm]] = stock_local[nm].copy()
    # the Prowler holds the gun further out than the CAR: slide the (stock-shaped) body forward along the
    # view direction just enough for both arms to reach their unchanged wrists (<= REACH of full length)
    hip = idx["def_c_hip"]
    hip_rest = L[hip].copy()
    fwd = (G[par[hip]].inverted().to_3x3() @ G[idx["jx_c_camera"]].to_3x3().col[2]).normalized()
    arms = [tuple(idx[f"def_{s}_{b}"] for b in ("shoulder", "elbow", "wrist")) for s in "lr"]
    lens = [((G[e].translation - G[sh].translation).length, (G[w].translation - G[e].translation).length) for sh, e, w in arms]

    def need(shift):
        L[hip] = Matrix.Translation(fwd * shift) @ hip_rest
        g = globals_(nodes, L)
        return max([(G[w].translation - g[sh].translation).length / (a + b)
                    for (sh, e, w), (a, b) in zip(arms, lens) if a > 1e-4 and b > 1e-4] or [0.0])

    lo, hi = 0.0, 0.0
    if need(0.0) > REACH:
        hi = 1.0
        while need(hi) > REACH and hi < 16:
            hi *= 2
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if need(mid) <= REACH else (mid, hi)
    need(hi)
    G1 = globals_(nodes, L)                       # new body, everything else still on its old locals
    Gn = {}
    stats = {}

    def world(i):
        if i not in Gn:
            Gn[i] = (world(par[i]) if par[i] >= 0 else Matrix.Identity(4)) @ L[i]
        return Gn[i]

    fixed = set()
    for nm in KEEP_WORLD:
        if nm in idx:
            Gn[idx[nm]] = G[idx[nm]].copy()
            fixed.add(idx[nm])
    for s in "lr":
        sh, el, wr = (idx.get(f"def_{s}_{b}") for b in ("shoulder", "elbow", "wrist"))
        if None in (sh, el, wr):
            continue
        a = (G[el].translation - G[sh].translation).length
        b = (G[wr].translation - G[el].translation).length
        S = G1[sh].translation
        W = G[wr].translation
        d = (W - S).length
        if d < 1e-4 or a < 1e-4 or b < 1e-4:
            continue
        reach = d / (a + b)
        dd = min(d, (a + b) * 0.9995)
        x = (a * a - b * b + dd * dd) / (2 * dd)
        h = math.sqrt(max(0.0, a * a - x * x))
        axis = (W - S).normalized()
        o_axis = (G[wr].translation - G[sh].translation).normalized()
        pole = G[el].translation - G[sh].translation
        pole = pole - o_axis * pole.dot(o_axis)
        pole = pole - axis * pole.dot(axis)
        pole = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
        E = S + axis * x + pole * h
        # shoulder: aim the upper arm at E (upper-arm helpers ride along on their locals)
        E1 = (G1[sh] @ G[sh].inverted() @ G[el]).translation
        Gn[sh] = about(S, rot_between(E1 - S, E - S)) @ G1[sh]
        fixed.add(sh)
        # elbow: from the shoulder chain, then aim the forearm at the unchanged wrist
        e_kept = world(el)
        W1 = (e_kept @ G[el].inverted() @ G[wr]).translation
        Gn[el] = about(e_kept.translation, rot_between(W1 - e_kept.translation, W - e_kept.translation)) @ e_kept
        fixed.add(el)
        for k in [i for i in list(Gn) if i not in fixed]:
            del Gn[k]                             # drop cached descendants computed before the edit
        stats[s] = (reach, hi)
    for i in nodes:
        world(i)
    new_local = {i: ((Gn[par[i]].inverted() @ Gn[i]) if par[i] >= 0 else Gn[i]) for i in nodes}
    return new_local, Gn, stats


report = []
for fn in sorted(os.listdir(ANIMS)):
    name = fn[:-4]
    if not fn.endswith(".smd") or name == "ref" or name in DELTA:
        continue
    path = os.path.join(ANIMS, fn)
    stock_path = os.path.join(STOCK_ANIMS, fn)
    if os.path.exists(stock_path) and open(path, "rb").read() == open(stock_path, "rb").read():
        continue                                  # untouched stock CAR pose: already fits the TF2 arms
    nodes, frames, _ = read_smd(path)
    names = {nm for nm, _ in nodes.values()}
    if not {"def_l_wrist", "def_r_wrist", "ja_c_propGun", "def_l_shoulder"} <= names:
        continue
    raw = open(path, encoding="utf-8-sig").read().splitlines()
    tail = raw[raw.index("end", raw.index("skeleton")) + 1:]
    out_frames, worst, err, shift = [], 0.0, 0.0, 0.0
    for fi, local in enumerate(frames):
        new_local, Gn, st = retarget_frame(nodes, local)
        # invariants: gun and hands unchanged in world space
        G = globals_(nodes, local)
        chk = globals_(nodes, new_local)
        idx = {nm: i for i, (nm, _) in nodes.items()}
        for nm in ("def_c_base", "def_l_wrist", "def_r_wrist", "def_l_finIndexC", "def_r_finIndexC", "jx_c_camera"):
            if nm in idx:
                err = max(err, (chk[idx[nm]].translation - G[idx[nm]].translation).length)
        worst = max([worst] + [r for r, _ in st.values()])
        shift = max([shift] + [h for _, h in st.values()])
        out_frames.append(new_local)
    assert err < 1e-3, f"{fn}: gun/hand moved by {err}"
    assert worst <= REACH + 1e-3, f"{fn}: arm cannot reach the hand (reach {worst:.3f})"
    write_smd(path, nodes, out_frames, tail)
    report.append((fn, len(frames), worst))
    print(f"RETARGET {fn:40s} frames {len(frames):4d} max reach {worst:5.3f} max body shift {shift:5.2f}")
print(f"RETARGET_OK {len(report)} animations")
