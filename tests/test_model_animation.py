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

    def test_no_extra_sequences_or_pose_parameters(self):
        # the drum turns inside the stock fire (attack) deltas, so the tables are exactly the stock CAR's
        self.assertEqual([n for _, n in self.built.table(192, 232, 4)], [n for _, n in self.stock.table(192, 232, 4)])
        self.assertEqual(self.built.poseparams(), self.stock.poseparams())

    def test_embedded_payload_is_inside_declared_mdl_length(self):
        world_name = "w_car101_conv.mdl" if self.built_path.stem.endswith("_conv") else "w_car101.mdl"
        for name, model in (("view", self.built), ("world", Mdl(str(self.built_path.with_name(world_name))))):
            with self.subTest(model=name):
                self.assertEqual(model.i(80), len(model.d), "v53 length must cover the complete embedded MDL/VTX/VVD payload")


if __name__ == "__main__":
    unittest.main()
