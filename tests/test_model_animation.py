"""Validate the compiled animation payload, beyond sequence names and indices."""
import os
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mdl_lib import Mdl


class CompiledAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = Mdl(str(ROOT / "stock/models/weapons/car101/ptpov_car101.mdl"))
        cls.built_path = Path(os.environ.get("PROWLER_VIEW_MDL", str(ROOT / "build/sfm_game/models/weapons/car101/ptpov_car101_conv.mdl")))
        cls.built = Mdl(str(cls.built_path))

    def test_animation_delta_semantics_match_original_indices(self):
        stock, built = self.stock.table(184, 92, 4), self.built.table(184, 92, 4)
        self.assertGreaterEqual(len(built), len(stock))
        for (sa, name), (ba, actual_name) in zip(stock, built):
            with self.subTest(animation=name):
                self.assertEqual(actual_name, name)
                self.assertEqual(bool(self.stock.i(sa + 12) & 4), bool(self.built.i(ba + 12) & 4),
                                 "A delta overlay compiled as an absolute pose moves the whole rig")

    def test_bone_set_is_exactly_stock(self):
        # every working Apex->TF2 viewmodel port keeps the stock bones; 0.1.11-0.1.18 appended 34 reactive
        # bones and the parts on them (drum, rings) kept flying in game
        self.assertEqual(self.built.bones(), self.stock.bones())

    def test_only_the_spin_layer_is_appended(self):
        # stock sequences / pose parameters keep their indices; the script-driven drum spin adds exactly one
        # autoplay delta layer and one pose parameter, both at the end
        stock_seq = [n for _, n in self.stock.table(192, 232, 4)]
        self.assertEqual([n for _, n in self.built.table(192, 232, 4)], stock_seq + ["prowler_spin_layer"])
        self.assertEqual(self.built.poseparams(), self.stock.poseparams() + ["prowler_spin"])
        spin = self.built.sequences()[-1]
        self.assertTrue(spin["delta"] and spin["autoplay"] and spin["looping"])
        self.assertEqual(len(spin["anims"]), 8)
        self.assertNotIn("#INVALID", " ".join(spin["anims"]), "MDLShit must keep every blend index valid")

    def test_embedded_payload_is_inside_declared_mdl_length(self):
        world_name = "w_car101_conv.mdl" if self.built_path.stem.endswith("_conv") else "w_car101.mdl"
        for name, model in (("view", self.built), ("world", Mdl(str(self.built_path.with_name(world_name))))):
            with self.subTest(model=name):
                self.assertEqual(model.i(80), len(model.d), "v53 length must cover the complete embedded MDL/VTX/VVD payload")


if __name__ == "__main__":
    unittest.main()
