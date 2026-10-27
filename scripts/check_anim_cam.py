"""blender -b --factory-startup -P check_anim_cam.py : per animation, gun (def_c_base) and right hand
relative to jx_c_camera, ours vs stock, first/last frame. Flags anims whose gun ends up behind/away from the eye."""
import os
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name

STOCK = r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims"
OURS = r"D:\TitanfallMods\35_ProwlerCAR\build\view\anims"


def cam_rel(p, fi):
    n, f, _ = read_smd(p)
    fi = fi if fi >= 0 else len(f) + fi
    g = by_name(n, globals_(n, f[fi]))
    if "jx_c_camera" not in g or "def_c_base" not in g:
        return None
    if os.environ.get("REL") == "root":   # model origin (what the engine pins to the eye)
        return g["def_c_base"].translation.copy(), g["jx_c_camera"].translation.copy()
    ci = g["jx_c_camera"].inverted()
    return ci @ g["def_c_base"].translation, (ci @ g["ja_r_propHand"].translation) if "ja_r_propHand" in g else None


def fmt(v):
    return "(%7.2f,%7.2f,%7.2f)" % tuple(v) if v is not None else "None"


for fn in sorted(os.listdir(OURS)):
    if not fn.endswith(".smd") or not os.path.exists(os.path.join(STOCK, fn)):
        continue
    for fi in (0, -1):
        try:
            s, o = cam_rel(os.path.join(STOCK, fn), fi), cam_rel(os.path.join(OURS, fn), fi)
        except Exception as e:  # noqa: BLE001
            print(f"ANIM {fn} ERR {e}")
            break
        if s is None or o is None:
            continue
        d = (o[0] - s[0]).length
        print(f"ANIM {fn:40s} f{fi:+d} stock {fmt(s[0])} ours {fmt(o[0])} diff {d:6.2f} {'<<<' if d > 8 else ''}"
              + (f" cam stock {fmt(s[1])} ours {fmt(o[1])}" if os.environ.get("REL") == "root" else ""))
print("CHECK_ANIM_CAM_OK")
