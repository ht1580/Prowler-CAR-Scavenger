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


if __name__ == "__main__":
    unittest.main()
