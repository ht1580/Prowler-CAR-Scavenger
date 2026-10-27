import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

S = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims"
O = r"D:\TitanfallMods\35_ProwlerCAR\build\view\anims"
W = ["jx_c_pov", "jx_c_camera", "def_l_clav", "def_l_shoulder", "def_l_shoulderTwist", "def_l_elbowB", "def_l_shoulderMid", "def_l_elbow",
     "def_l_forearm", "def_l_wrist"] + [f"def_l_fin{f}" for f in ("IndexA", "IndexB", "IndexC", "MidA", "MidB", "MidC", "ThumbA", "ThumbB", "ThumbC",
                                                              "RingCarpal", "RingA", "RingB", "RingC", "PinkyA", "PinkyB", "PinkyC")] + ["ja_l_propHand"]


def layered(base_dir):
    n, f, _ = read_smd(base_dir + r"\draw_seq.smd")
    wn, wf, _ = read_smd(S + r"\wind_loop_anim_layer.smd")
    wl = {wn[i][0]: m for i, m in wf[0].items()}
    idx = {nm: i for i, (nm, _) in n.items()}
    loc = dict(f[-1])
    base = by_name(n, globals_(n, loc))
    for nm in W:
        if nm in idx and nm in wl:
            loc[idx[nm]] = wl[nm]
    g = by_name(n, globals_(n, loc))
    return base, g


for tag, d in (("stock", S), ("ours", O)):
    base, g = layered(d)
    bi = g["def_c_base"].inverted()
    hip = base["def_c_base"].inverted() @ base["def_l_wrist"].translation
    wind = bi @ g["def_l_wrist"].translation
    print(f"{tag}: left wrist in gun space  hip {tuple(round(x, 1) for x in hip)}  wind {tuple(round(x, 1) for x in wind)}  shift {(wind - hip).length:.1f}")
