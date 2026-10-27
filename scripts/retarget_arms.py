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
    keeping the original bend plane (pole = where the Prowler elbow pointed), and rebuilt with the TF2 arm
    rig's rules measured from the stock CAR: elbow = pure hinge (0.1.16 left up to 88 deg of upper-arm twist
    and 169 deg of forearm twist -> wrung sleeves / stretched hands in game), elbowB follows the bend,
    the forearm helper takes half the wrist twist.
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
REACH = 0.97
# Viewmodel frames (half angles, 16:9). Apex draws viewmodels at 70 deg (4:3): +-42.9 h / +-27.7 v; its reload
# swaps the magazine and fetches the new one just outside that (mag 44 deg h then teleports to -47 deg v, left
# hand 45 deg h). TF2 draws the viewmodel with the player FOV, up to 110 deg (4:3): +-62.2 h / +-46.9 v, so
# those off-screen moves showed up ("extra hand", "flying magazine"). Anything that has left the gun AND
# Apex keeps outside its frame is pushed outward until it is outside TF2's widest frame as well.
APEX_FRAME = (42.9, 27.7)
TF2_FRAME = (62.2, 46.9)
OFFSCREEN = ("def_l_wrist", "def_r_wrist", "def_c_magazine")

stock_mdl = Mdl(ROOT + r"\stock\models\weapons\car101\ptpov_car101.mdl")
DELTA = {name for row, name in stock_mdl.table(184, 92, 4) if stock_mdl.i(row + 12) & 4}

sn, sf, _ = read_smd(STOCK_ANIMS + r"\draw_seq.smd")
stock_local = {sn[i][0]: m for i, m in sf[-1].items()}


def signed_angle(m, axis):
    q = m.to_quaternion()
    return 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)


def measure_rig():
    """TF2 arm rig constants per side, from the stock CAR's own animations (offsets, elbow hinge axis,
    elbowB = c1 * bend + c0 fitted over every frame of several stock animations)."""
    rig = {}
    for s in "lr":
        L = lambda b: stock_local[f"def_{s}_{b}"]
        k = L("elbow").to_quaternion().axis.normalized()
        if signed_angle(L("elbow"), k) < 0:
            k = -k
        kb = L("elbowB").to_quaternion().axis.normalized()
        if signed_angle(L("elbowB"), kb) < 0:
            kb = -kb
        pts = []
        for fn in ("draw_seq", "reload_seq", "sprint_seq", "ads_in_anim", "reload_empty_seq"):
            n, frames, _ = read_smd(STOCK_ANIMS + "\\" + fn + ".smd")
            ix = {nm: i for i, (nm, _) in n.items()}
            for fr in frames:
                pts.append((signed_angle(fr[ix[f"def_{s}_elbow"]], k), signed_angle(fr[ix[f"def_{s}_elbowB"]], kb)))
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        c1 = sum((p[0] - mx) * (p[1] - my) for p in pts) / sum((p[0] - mx) ** 2 for p in pts)
        c0 = my - c1 * mx
        fit_err = max(abs(c1 * p[0] + c0 - p[1]) for p in pts)
        rig[s] = {"mid": L("shoulderMid").translation.copy(), "el": L("elbow").translation.copy(),
                  "wr": L("wrist").translation.copy(), "fo": L("forearm").translation.copy(),
                  "eb": L("elbowB").translation.copy(), "k": k, "kb": kb, "c1": c1, "c0": c0}
        print(f"RIG {s}: hinge {tuple(round(x, 3) for x in k)} elbowB = {c1:.3f}*bend + {math.degrees(c0):.1f} deg "
              f"(max fit error {math.degrees(fit_err):.2f} deg over {len(pts)} stock frames)")
        assert math.degrees(fit_err) < 2.0
    return rig


RIG = measure_rig()

# where each off-screen candidate sits on the gun in the hip pose (gun space), from the Prowler draw end
_hn, _hf, _ = read_smd(ANIMS + r"\draw_seq.smd")
_hg = by_name(_hn, globals_(_hn, _hf[-1]))
HOME = {nm: _hg["def_c_base"].inverted() @ _hg[nm].translation for nm in OFFSCREEN}


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


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def keep_offscreen(G, idx, pushed):
    """Push hands / magazine that Apex hides just outside its frame out of TF2's frame (in place in G)."""
    cam = G[idx["jx_c_camera"]]
    ci = cam.inverted()
    base_i = G[idx["def_c_base"]].inverted()
    for nm in OFFSCREEN:
        if nm not in idx:
            continue
        i = idx[nm]
        p = ci @ G[i].translation
        if p.z <= 0.05:
            continue                                   # already behind the eye
        h, v = math.atan2(p.x, p.z), math.atan2(p.y, p.z)
        o = max(abs(math.degrees(h)) / APEX_FRAME[0], abs(math.degrees(v)) / APEX_FRAME[1])
        away = ((base_i @ G[i].translation) - HOME[nm]).length          # off its place on the gun
        w = smoothstep((o - 0.97) / 0.08) * smoothstep((away - 3.0) / 3.0)
        if w <= 0:
            continue
        t = max(abs(math.degrees(h)) / TF2_FRAME[0], abs(math.degrees(v)) / TF2_FRAME[1])
        s = 1 + (max(1.0, 1.08 / t) - 1) * w
        h2, v2 = max(-1.48, min(1.48, h * s)), max(-1.48, min(1.48, v * s))
        d = Vector((math.tan(h2), math.tan(v2), 1.0)).normalized() * p.length
        G[i] = Matrix.Translation(cam @ d - G[i].translation) @ G[i]
        pushed[nm] = max(pushed.get(nm, 0.0), w)


def retarget_frame(nodes, local, prev, pushed):
    idx = {nm: i for i, (nm, _) in nodes.items()}
    par = {i: p for i, (_, p) in nodes.items()}
    G = globals_(nodes, local)
    keep_offscreen(G, idx, pushed)
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
    stats = {}
    for s in "lr":
        need_names = [f"def_{s}_{b}" for b in ("clav", "shoulder", "shoulderMid", "elbow", "elbowB", "forearm", "wrist")]
        if not all(n_ in idx for n_ in need_names):
            continue
        cl, sh, mid, el, eb, fo, wr = (idx[n_] for n_ in need_names)
        r = RIG[s]
        a, b = (r["mid"] + r["el"]).length, r["wr"].length
        S, W = G1[sh].translation, G[wr].translation
        d = (W - S).length
        if d < 1e-4:
            continue
        reach = d / (a + b)
        # elbow position: two-bone IK; the free swivel of the elbow about the shoulder->wrist line is chosen
        # (below) for the least wrist twist, near the plane the Prowler elbow was bent in
        dd = min(d, (a + b) * 0.9995)
        x = (a * a - b * b + dd * dd) / (2 * dd)
        h = math.sqrt(max(0.0, a * a - x * x))
        axis = (W - S).normalized()
        o_axis = (G[wr].translation - G[sh].translation).normalized()
        pole = G[el].translation - G[sh].translation
        pole = pole - o_axis * pole.dot(o_axis)
        pole = pole - axis * pole.dot(axis)
        p0 = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
        p1 = axis.cross(p0)
        tx = r["wr"].normalized()
        A = (r["mid"] + r["el"]).normalized()

        def frame(x_, y_):
            n_ = (y_ - x_ * x_.dot(y_)).normalized()
            return Matrix((x_, n_, x_.cross(n_))).transposed()

        def build(phi):
            # TF2 arm rig (measured from the stock CAR): shoulderMid has no rotation, the elbow is a pure hinge
            # about RIG.k (no twist about the upper arm), elbowB follows the bend linearly, the forearm twist
            # helper carries half the wrist twist; the shoulder roll puts the hinge plane through the wrist.
            E = S + axis * x + (p0 * math.cos(phi) + p1 * math.sin(phi)) * h
            u, f = (E - S).normalized(), (W - E).normalized()
            theta = u.angle(f)
            B = (Matrix.Rotation(theta, 3, r["k"]) @ r["wr"]).normalized()
            G_sh = Matrix.Translation(S) @ (frame(u, f) @ frame(A, B).transposed()).to_4x4()
            L_el = Matrix.Translation(r["el"]) @ Matrix.Rotation(theta, 4, r["k"])
            L_wr = (G_sh @ Matrix.Translation(r["mid"]) @ L_el).inverted() @ G[wr]
            q = L_wr.to_quaternion()
            tw = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(tx), q.w)
            tw = (tw + math.pi) % (2 * math.pi) - math.pi
            return G_sh, theta, L_el, L_wr, tw

        prev_phi = prev.get(s)

        def cost(phi):
            c = abs(build(phi)[4]) + 0.25 * abs(phi)
            return c + (0.5 * abs(phi - prev_phi) if prev_phi is not None else 0)

        best = min((math.radians(k) for k in range(-180, 181, 5)), key=cost)
        best = min((best + math.radians(k) for k in range(-5, 6)), key=cost)
        prev[s] = best
        G_sh, theta, L_el, L_wr, tw = build(best)
        L[sh] = G1[cl].inverted() @ G_sh
        L[mid] = Matrix.Translation(r["mid"])
        L[el] = L_el
        L[eb] = Matrix.Translation(r["eb"]) @ Matrix.Rotation(r["c1"] * theta + r["c0"], 4, r["kb"])
        assert (L_wr.translation - r["wr"]).length < 0.02, \
            f"{s} wrist off its forearm by {(L_wr.translation - r['wr']).length:.3f} (reach {reach:.3f}, theta {math.degrees(theta):.1f})"
        L[fo] = Matrix.Translation(r["fo"]) @ Matrix.Rotation(0.5 * tw, 4, tx)
        L[wr] = Matrix.Translation(r["wr"]) @ L_wr.to_quaternion().to_matrix().to_4x4()   # exact rig length
        stats[s] = (reach, hi, math.degrees(tw), math.degrees(best))
    # gun keeps its world pose under the new spine; the magazine follows its (possibly pushed) world pose
    pg = idx["ja_c_propGun"]
    Gtmp = globals_(nodes, L)
    L[pg] = Gtmp[par[pg]].inverted() @ G[pg]
    Gtmp = globals_(nodes, L)
    for nm in ("def_c_magazine", "def_c_magazine1"):
        if nm in idx:
            L[idx[nm]] = Gtmp[par[idx[nm]]].inverted() @ G[idx["def_c_magazine"]]
    Gn = globals_(nodes, L)
    return L, Gn, stats, G


report = []
for fn in sorted(os.listdir(ANIMS)):
    name = fn[:-4]
    if not fn.endswith(".smd") or name == "ref" or name in DELTA or name.startswith(("prowler_spin", "fire_anim_layer")):
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
    out_frames, worst, err, shift, twist, err_at = [], 0.0, 0.0, 0.0, 0.0, ""
    prev, pushed = {}, {}
    for fi, local in enumerate(frames):
        try:
            new_local, Gn, st, G = retarget_frame(nodes, local, prev, pushed)
        except AssertionError as e:
            raise AssertionError(f"{fn} frame {fi}: {e}") from None
        # invariants: gun and hands where the retarget put them (hands only moved when pushed off screen)
        chk = globals_(nodes, new_local)
        idx = {nm: i for i, (nm, _) in nodes.items()}
        for nm in ("def_c_base", "def_l_wrist", "def_r_wrist", "def_c_magazine", "jx_c_camera"):
            if nm in idx:
                e_ = (chk[idx[nm]].translation - G[idx[nm]].translation).length
                if e_ > err:
                    err, err_at = e_, f"{nm} frame {fi}"
        worst = max([worst] + [v[0] for v in st.values()])
        shift = max([shift] + [v[1] for v in st.values()])
        twist = max([twist] + [abs(v[2]) for v in st.values()])
        out_frames.append(new_local)
    assert err < 0.03, f"{fn}: {err_at} off its target by {err:.3f}"
    assert worst <= REACH + 1e-3, f"{fn}: arm cannot reach the hand (reach {worst:.3f})"
    write_smd(path, nodes, out_frames, tail)
    report.append((fn, len(frames), worst))
    print(f"RETARGET {fn:40s} frames {len(frames):4d} max reach {worst:5.3f} max body shift {shift:5.2f} max wrist twist {twist:5.1f}"
          + (f"  off-screen push {', '.join(f'{k}:{v:.2f}' for k, v in pushed.items())}" if pushed else ""))
print(f"RETARGET_OK {len(report)} animations")
