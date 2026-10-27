"""Draw grip_view.py's JSON: side views (z forward, y up, def_c_base space) with real hand bone positions."""
import json
import sys
from PIL import Image, ImageDraw

data = json.load(open(sys.argv[1]))
out = sys.argv[2]
RIGHT = ["def_r_wrist", "ja_r_propHand", "def_r_finIndexA", "def_r_finIndexB", "def_r_finIndexC", "def_r_finMidA",
         "def_r_finMidB", "def_r_finThumbA", "def_r_finThumbB"]
LEFT = ["def_l_wrist", "ja_l_propHand", "def_l_finIndexA", "def_l_finIndexB", "def_l_finMidA", "def_l_finMidB"]
S, PW, PH = 30, 1300, 460
img = Image.new("RGB", (PW, PH * len(data)), (26, 26, 30))
dr = ImageDraw.Draw(img)
for row, case in enumerate(data):
    OX, OY = 520, row * PH + 250

    def P(y, z):
        return OX + z * S, OY - y * S

    for z in range(-16, 24, 2):
        dr.line([P(-7, z), P(9, z)], fill=(44, 44, 50))
        dr.text(P(-7.4, z), str(z), fill=(90, 90, 100))
    for y, z in case["pts"]:
        dr.point(P(y, z), fill=(165, 165, 165) if row == 0 else (235, 150, 50))
    for names, col in ((RIGHT, (60, 230, 90)), (LEFT, (60, 200, 255))):
        pts = [P(*case["hands"][n]) for n in names if n in case["hands"]]
        for k, q in enumerate(pts):
            r = 7 if k < 2 else 4
            dr.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), outline=col, width=2)
        if len(pts) > 4:
            dr.line(pts[2:5], fill=col, width=2)
    o = P(0, 0)
    dr.line([(o[0] - 12, o[1]), (o[0] + 12, o[1])], fill=(255, 60, 60), width=3)
    dr.line([(o[0], o[1] - 12), (o[0], o[1] + 12)], fill=(255, 60, 60), width=3)
    dr.text((10, row * PH + 10), case["label"] + "   red=def_c_base  green=right hand (big circles: wrist, prop)  cyan=left hand  grid 2in  forward ->",
            fill=(230, 230, 230))
img.save(out)
print("DRAW_OK", out)
