"""Artifact regressions for the fire-sound override (0.1.14).

Northstar looks override EventIds up case-sensitively against the Miles bank names, which are lowercase
("weapon_car_loop_1p"); the capitalised keyvalues spelling never matched (0.1.2-0.1.13 always played the
stock CAR). Run with Blender's Python: python -m unittest discover -s tests -v
Set PROWLER_STAGE to validate staged mod assets instead of mod_src.
"""
import io
import json
import os
import re
import struct
import unittest
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MOD = Path(os.environ.get("PROWLER_STAGE", ROOT / "mod_src"))
BANK = {line.split(",", 1)[1].strip() for line in
        (ROOT / "audio_raw/events/tf2_all_audio_events.txt").read_text().splitlines() if "," in line}
ROUTING = {
    "burst_or_looping_fire_sound_start_1p": "weapon_car_firstshot_1p",
    "burst_or_looping_fire_sound_middle_1p": "weapon_car_loop_1p",
    "burst_or_looping_fire_sound_end_1p": "weapon_car_loopend_1p",
    "burst_or_looping_fire_sound_middle_3p": "weapon_car_loop_3p",
    "burst_or_looping_fire_sound_end_3p": "weapon_car_loopend_3p",
    "burst_or_looping_fire_sound_middle_npc": "weapon_car_loop_3p_npc_a",
    "burst_or_looping_fire_sound_end_npc": "weapon_car_loopend_npc",
    "fire_sound_2_player_1p": "weapon_car_secondshot_1p",
    "fire_sound_2_player_3p": "weapon_car_secondshot_3p",
    "fire_sound_2_npc": "weapon_car_secondshot_npc",
}
AUDIBLE = ("weapon_car_firstshot_1p", "weapon_car_loop_1p", "weapon_car_loopend_1p", "weapon_car_loop_3p",
           "weapon_car_loopend_3p", "weapon_car_loop_3p_npc_a", "weapon_car_loopend_npc", "car_lowammo_shot1")


def definitions():
    return {p.stem: json.loads(p.read_bytes()) for p in (MOD / "audio").glob("*.json")}


def pcm(path):
    data = path.read_bytes()
    chunks, offset = [], 12
    while offset + 8 <= len(data):
        tag, size = struct.unpack_from("<4sI", data, offset)
        chunks.append(tag)
        offset += 8 + size + (size % 2)
    with wave.open(io.BytesIO(data)) as w:
        fmt = (w.getnchannels(), w.getsampwidth(), w.getframerate())
        s = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, 2) / 32767
    return data, chunks, fmt, s


class ReleaseFixes(unittest.TestCase):
    def test_every_override_id_is_a_real_lowercase_bank_event(self):
        seen = []
        for stem, d in definitions().items():
            with self.subTest(definition=stem):
                self.assertIn(d["AudioSelectionStrategy"], ("sequential", "random"))
                self.assertTrue(list((MOD / "audio" / stem).glob("*.wav")), "sample folder = definition stem")
                for event in d["EventId"]:
                    self.assertIn(event, BANK, "Northstar matches EventIds case-sensitively against the bank")
                seen += d["EventId"]
        self.assertEqual(len(seen), len(set(seen)), "a duplicated EventId is skipped by Northstar")

    def test_weapon_routes_the_stock_loop_to_overridden_events(self):
        text = (MOD / "keyvalues/scripts/weapons/mp_weapon_car.txt").read_text(encoding="utf-8")
        keys = dict(re.findall(r'^\s*"([^"]+)"\s+"([^"]*)"', text, re.MULTILINE))
        self.assertEqual(keys.get("looping_sounds"), "1", "the Prowler full-auto sound is a loop")
        ids = {e for d in definitions().values() for e in d["EventId"]}
        for key, event in ROUTING.items():
            with self.subTest(key=key):
                self.assertEqual(keys.get(key), event)
                self.assertIn(event, ids)

    def test_samples_are_clean_pcm16_and_audible(self):
        for stem in AUDIBLE:
            with self.subTest(event=stem):
                data, chunks, fmt, s = pcm(MOD / "audio" / stem / "1.wav")
                self.assertEqual(data[:4], b"RIFF")
                self.assertEqual(chunks, [b"fmt ", b"data"], "Metadata can become audible noise in Northstar")
                self.assertEqual(fmt, (2, 2, 48000))
                self.assertGreater(float(np.sqrt(np.mean(s ** 2))), 0.005)
                self.assertLessEqual(float(np.max(np.abs(s))), 0.9801)

    def test_loops_are_seamless(self):
        for stem in ("weapon_car_loop_1p", "weapon_car_loop_3p", "weapon_car_loop_3p_npc_a"):
            with self.subTest(event=stem):
                _, _, _, s = pcm(MOD / "audio" / stem / "1.wav")
                edge = np.abs(s[-1] - s[0]).max()
                typical = np.abs(np.diff(s, axis=0)).max(axis=1)
                self.assertLessEqual(edge, np.percentile(typical, 99.9), "loop wrap must not click")


if __name__ == "__main__":
    unittest.main()
