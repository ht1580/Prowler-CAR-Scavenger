"""Check decoded final MDL motion, not just descriptor bits."""
import json
import math
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELTA_LAYERS = ("idle_anim_autoplay", "idle_ads_anim_autoplay", "attack_anim", "attack_ads_anim", "attack_slide_anim",
                "attack_onehanded_anim", "attack_onehanded_ads_anim")


class NativePose(unittest.TestCase):
    def test_delta_layers_do_not_move_the_entire_viewmodel(self):
        # Crowbar exports every delta root with a -90 deg correction; it must be undone for the idle layers
        # AND for the attack layers (0.1.12/0.1.13 missed the attack ones -> the model flew off on every shot)
        doc = json.loads(Path(os.environ.get("PROWLER_NATIVE_POSES", ROOT / "build/native-view.json")).read_text(encoding="utf-8"))
        names = [bone["name"] for bone in doc["bones"]]
        root = names.index("jx_c_delta")
        checked = set()
        for pose in doc["poses"]:
            if pose["name"] not in DELTA_LAYERS:
                continue
            with self.subTest(animation=pose["name"], frame=pose["frame"]):
                value = next((value for value in pose["locals"] if value["index"] == root), None)
                if value is not None:
                    for angle in value["rot"]:
                        self.assertLess(abs(math.remainder(angle, 2 * math.pi)), 0.001,
                                        "Crowbar's root coordinate correction must not become a layer rotation")
                    self.assertLess(max(map(abs, value["pos"])), 0.001)
            checked.add(pose["name"])
        self.assertEqual(checked, set(DELTA_LAYERS))

    def test_shoulders_stay_behind_the_eye(self):
        # the TF2 pilot arms (bonemerged by name) have full sleeves/shoulders: with the raw Apex body the
        # shoulders sat 3 units in front of the camera and arm chunks filled the view (0.1.15 report).
        # retarget_arms.py puts the stock-CAR body back; the idle pose (draw_seq end) must keep both
        # shoulders within 1.5 units of the eye plane (stock: -0.9 / -3.9; 0.1.15: +3.1 / +0.1).
        doc = json.loads(Path(os.environ.get("PROWLER_NATIVE_POSES", ROOT / "build/native-view.json")).read_text(encoding="utf-8"))
        bones = doc["bones"]
        names = [b["name"] for b in bones]
        pose = max((p for p in doc["poses"] if p["name"] == "@draw_seq"), key=lambda p: p["frame"])
        local = {v["index"]: v for v in pose["locals"]}

        def matrix(v):
            x, y, z = v["rot"]
            cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
            r = [[cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz],
                 [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz],
                 [-sy, sx * cy, cx * cy]]
            return [r[0] + [v["pos"][0]], r[1] + [v["pos"][1]], r[2] + [v["pos"][2]], [0, 0, 0, 1]]

        def mul(a, b):
            return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

        cache = {}

        def world(i):
            if i not in cache:
                m = matrix(local.get(i, bones[i]))
                cache[i] = mul(world(bones[i]["parent"]), m) if bones[i]["parent"] >= 0 else m
            return cache[i]

        cam = world(names.index("jx_c_camera"))
        for side in "lr":
            with self.subTest(shoulder=side):
                s = world(names.index(f"def_{side}_shoulder"))
                d = [s[i][3] - cam[i][3] for i in range(3)]
                forward = sum(d[i] * cam[i][2] for i in range(3))     # camera +Z = view direction
                self.assertLess(forward, 1.5)


if __name__ == "__main__":
    unittest.main()
