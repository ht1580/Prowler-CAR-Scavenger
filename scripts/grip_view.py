"""blender -b --factory-startup -P grip_view.py -- out.png
Full side views (z forward, y up, def_c_base space) of both first-person meshes with the real hand bones of each
gun's own idle pose (green = right hand: wrist/prop/index/middle/thumb, cyan = left hand) and def_c_base (red)."""
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from smdlib import read_smd, globals_, by_name
import json
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

out = sys.argv[sys.argv.index("--") + 1]
CASES = [("stock CAR (CAR first-person anim)", r"D:\TitanfallMods\35_ProwlerCAR\stock\view\v_car101.smd",
          r"D:\TitanfallMods\35_ProwlerCAR\stock\view\ptpov_car101_anims\reload_seq.smd"),
         ("Prowler (Apex first-person anim)", r"D:\TitanfallMods\35_ProwlerCAR\build\view\prowler_body.smd",
          r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\animrig\weapons\prowler_smg\anims_ptpov_prowler_smg\ptpov_prowler_smg_reload_01_dmx__4C976C7A.smd")]
RIGHT = ["def_r_wrist", "ja_r_propHand", "def_r_finIndexA", "def_r_finIndexB", "def_r_finIndexC", "def_r_finMidA",
         "def_r_finMidB", "def_r_finThumbA", "def_r_finThumbB"]
LEFT = ["def_l_wrist", "ja_l_propHand", "def_l_finIndexA", "def_l_finIndexB", "def_l_finMidA", "def_l_finMidB"]
DATA = out + ".json"
if Image is None:
    dump = []
    for label, mesh, anim in CASES:
        mn, mf, tris = read_smd(mesh)
        b0 = by_name(mn, globals_(mn, mf[0]))["def_c_base"].translation
        an, af, _ = read_smd(anim)
        g = by_name(an, globals_(an, af[0]))
        ib = g["def_c_base"].inverted()
        pts = [[float(p[2]) - b0.y, float(p[3]) - b0.z] for mat, vs in tris for p in vs]
        hands = {n: list((ib @ g[n].translation)[1:]) for n in RIGHT + LEFT if n in g}
        dump.append({"label": label, "pts": pts, "hands": hands})
    json.dump(dump, open(DATA, "w"))
    print("GRIP_VIEW_OK", DATA)
    raise SystemExit
S, PW, PH = 30, 1300, 460
img = Image.new("RGB", (PW, PH * 2), (26, 26, 30))
dr = ImageDraw.Draw(img)
for row, (label, mesh, anim) in enumerate(CASES):
    mn, mf, tris = read_smd(mesh)
    rest = by_name(mn, globals_(mn, mf[0]))
    b0 = rest["def_c_base"].translation
    an, af, _ = read_smd(anim)
    g = by_name(an, globals_(an, af[0]))
    ib = g["def_c_base"].inverted()
    OX, OY = 520, row * PH + 250

    def P(v):
        return OX + v.z * S, OY - v.y * S

    for z in range(-16, 24, 2):
        dr.line([P(type(b0)((0, -7, z))), P(type(b0)((0, 9, z)))], fill=(44, 44, 50))
    for mat, vs in tris:
        for p in vs:
            v = type(b0)((float(p[1]), float(p[2]), float(p[3]))) - b0
            dr.point(P(v), fill=(165, 165, 165) if row == 0 else (235, 150, 50))
    for names, colr in ((RIGHT, (60, 230, 90)), (LEFT, (60, 200, 255))):
        pts = [P(ib @ g[n].translation) for n in names if n in g]
        for k, q in enumerate(pts):
            r = 7 if k < 2 else 4
            dr.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), outline=colr, width=2)
        if len(pts) > 2:
            dr.line(pts[2:5], fill=colr, width=2)
    o = P(type(b0)((0, 0, 0)))
    dr.line([(o[0] - 12, o[1]), (o[0] + 12, o[1])], fill=(255, 60, 60), width=3)
    dr.line([(o[0], o[1] - 12), (o[0], o[1] + 12)], fill=(255, 60, 60), width=3)
    dr.text((10, row * PH + 10), label + "   red = def_c_base   green = right hand (big: wrist/prop)   cyan = left hand   grid 2in  forward ->",
            fill=(230, 230, 230))
img.save(out)
print("GRIP_VIEW_OK", out)

