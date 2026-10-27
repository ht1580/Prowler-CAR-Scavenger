"""Compiled world geometry: Apex two-hand hold, rigid (undeformed) gun, stock world timing."""
import json
import math
import os
import struct
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def world_matrices(doc, pose):
    matrices = []
    values = {row["index"]: row for row in pose["locals"]}
    for index, bone in enumerate(doc["bones"]):
        value = values.get(index, bone)
        rx, ry, rz = value["rot"]
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        rotation_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        rotation_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        rotation_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        local = np.eye(4)
        local[:3, :3] = rotation_z @ rotation_y @ rotation_x
        local[:3, 3] = value["pos"]
        matrices.append(matrices[bone["parent"]] @ local if bone["parent"] >= 0 else local)
    return {bone["name"]: matrix for bone, matrix in zip(doc["bones"], matrices)}


def vertex_extent(path):
    data = Path(path).read_bytes()
    vvd = data.index(b"IDSV")
    count = struct.unpack_from("<I", data, vvd + 16)[0]
    start = struct.unpack_from("<I", data, vvd + 56)[0]
    points = np.array([struct.unpack_from("<3f", data, vvd + start + index * 48 + 16) for index in range(count)])
    return points.min(axis=0), points.max(axis=0)


class WorldFit(unittest.TestCase):
    """Third person: the Prowler is held like in Apex -- right hand on the slanted pipe grip with the
    trigger inside the second (big) loop, left hand on the taped front grip. The gun is placed rigidly
    (never stretched/squashed, 0.1.13 squashed the rear to 55%); the grip hand keeps the CAR's
    l_hand_ik and the support-hand IK target r_hand_ik moves onto the taped grip (the game uses it:
    stock guns carry per-gun values, Alternator z 2.4 / CAR 8.4 / Hemlok 9.3)."""

    def test_grip_hand_and_timing_match_the_original(self):
        stock = json.loads((ROOT / "tests/fixtures/native-world-stock.json").read_text(encoding="utf-8"))
        built = json.loads(Path(os.environ.get("PROWLER_NATIVE_WORLD", ROOT / "build/native-world.json")).read_text(encoding="utf-8"))
        reference = {(pose["name"], pose["frame"]): pose for pose in stock["poses"]}
        for pose in built["poses"]:
            key = (pose["name"], pose["frame"])
            with self.subTest(pose=key):
                self.assertTrue(key in reference, f"World animation timing differs from the original CAR: {key}")
                self.assertEqual(pose["frames"], reference[key]["frames"])
                original = world_matrices(stock, reference[key])
                actual = world_matrices(built, pose)
                np.testing.assert_allclose(actual["l_hand_ik"], original["l_hand_ik"], atol=0.0001, rtol=0)
                support = np.linalg.inv(actual["def_c_base"]) @ actual["r_hand_ik"]
                self.assertTrue(3.0 < support[2, 3] < 7.0, f"support hand must sit on the taped grip, z={support[2, 3]:.2f}")

    def test_world_gun_is_not_deformed(self):
        model = Path(os.environ.get("PROWLER_WORLD_MDL", ROOT / "build/sfm_game/models/weapons/car101/w_car101_conv.mdl"))
        low, high = vertex_extent(model)
        self.assertGreater(high[2] - low[2], 18.4, "the Prowler is ~18.7 long; a shorter world model was squashed")


if __name__ == "__main__":
    unittest.main()
