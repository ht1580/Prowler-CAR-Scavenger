"""Prowler gun sounds -> CAR fire events (Northstar audio override). Run with Blender's python (numpy).

Loops are re-sliced per shot at the Prowler period (auto-detected) and re-laid at the CAR fire rate
(14.1 rps) with circular overlap-add, so sound and muzzle flashes stay in sync with no pitch shift.
Output: 48 kHz / 16-bit / stereo PCM, no metadata chunks.
"""
import json
import struct
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from audio_tools import load, SR

APEX = Path(r"D:\TitanfallMods\35_ProwlerCAR\audio_raw\apex")
OUT = Path(r"D:\TitanfallMods\35_ProwlerCAR\mod_src\audio")
CAR_RPS = 14.1
LOOP_SHOTS = 56                       # 56 / 14.1 = 3.97 s loop
REPORT = {}


def src(name):
    return load(str(next(APEX.rglob(name + ".wav"))))


def period(a, lo=0.06, hi=0.11):
    """Shot period by envelope autocorrelation in [lo, hi] seconds."""
    env = np.abs(a).mean(axis=1)
    w = int(SR * 0.002)
    env = np.convolve(env, np.ones(w) / w, mode="same")
    env = env[: SR * 3] - env[: SR * 3].mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    l0, l1 = int(lo * SR), int(hi * SR)
    return (l0 + int(np.argmax(ac[l0:l1]))) / SR


def resequence(a, src_period, shots=LOOP_SHOTS, rps=CAR_RPS, skip=1):
    ts, tt = src_period, 1.0 / rps
    n_out = int(round(shots * tt * SR))
    out = np.zeros((n_out, 2), np.float32)
    slen = int((ts + 0.012) * SR)
    fin = int(0.002 * SR)
    fout = int(max(0.0, ts - tt + 0.012) * SR) + fin
    win = np.ones(slen, np.float32)
    win[:fin] = np.linspace(0, 1, fin)
    win[-fout:] = np.minimum(win[-fout:], np.linspace(1, 0, fout))
    # phase: cut each slice 3 ms before a shot's attack (sharpest envelope rise in the first period),
    # otherwise every slice carries the previous shot's tail and the cadence smears
    env = np.convolve(np.abs(a).mean(axis=1), np.ones(int(SR * 0.002)) / int(SR * 0.002), mode="same")
    rise = np.diff(env[: int(ts * SR) + 1])
    t0 = max(0, int(np.argmax(rise)) - int(0.003 * SR))
    avail = int((len(a) / SR - slen / SR - t0 / SR) // ts) - skip
    for k in range(shots):
        s = t0 + int(((k % max(1, avail)) + skip) * ts * SR)
        seg = a[s:s + slen] * win[:, None]
        d = int(round(k * tt * SR))
        idx = (np.arange(len(seg)) + d) % n_out          # circular -> seamless loop
        np.add.at(out, idx, seg)
    return out


def fade_tail(a, seconds):
    n = min(len(a), int(seconds * SR))
    a = a[:n].copy()
    f = int(0.25 * SR)
    a[-f:] *= np.linspace(1, 0, f)[:, None]
    return a


def mix(*layers):
    n = max(len(x) for x, _ in layers)
    out = np.zeros((n, 2), np.float32)
    for x, g in layers:
        out[:len(x)] += x * g
    return out


# Northstar matches override EventIds case-sensitively (audio.cpp: m_loadedAudioOverrides.find(eventName),
# no lowercasing) against the Miles bank names, which are lowercase "weapon_car_*" (+ "_BU1"/"_OLD2"
# suffixes) -- NOT the capitalised spelling used in mp_weapon_car.txt. Every CAR variant the bank has
# (interior _int*, enemy, backup) is listed so whichever one the mixer picks is replaced.
# Names: rwynx/Northstar-Commands-and-Audio-Overriding all_audio_events.txt (audio_raw/events copy).
EVENTS = {
    "weapon_car_firstshot_1p": ["weapon_car_firstshot_1p", "weapon_car_firstshot_1p_int"],
    "weapon_car_loop_1p": ["weapon_car_loop_1p"],
    "weapon_car_loopend_1p": ["weapon_car_loopend_1p", "weapon_car_loopend_1p_int", "weapon_car_loopend_1p_OLD"],
    "weapon_car_loop_3p": ["weapon_car_loop_3p", "weapon_car_loop_3p_BU1", "weapon_car_loop_3p_enemy",
                           "weapon_car_loop_3p_enemy_BU", "weapon_car_loop_3p_enemy_BU1", "weapon_car_loop_3p_OLD2"],
    "weapon_car_loopend_3p": ["weapon_car_loopend_3p", "weapon_car_loopend_3p_enemy", "weapon_car_loopend_3p_int",
                              "weapon_car_loopend_3p_int_enemy"],
    "weapon_car_loop_3p_npc_a": ["weapon_car_loop_3p_npc_a", "weapon_car_loop_3p_npc", "weapon_car_loop_npc"],
    "weapon_car_loopend_npc": ["weapon_car_loopend_npc", "weapon_car_loopend_npc_int"],
    # per-shot CAR crack (fire_sound_2) and the unused 3P/NPC first shots: silent, the Prowler loop
    # carries every shot like it does in Apex
    "weapon_car_secondshot_1p": ["weapon_car_secondshot_1p", "weapon_car_secondshot_1p_BU",
                                 "weapon_car_secondshot_1p_intlg", "weapon_car_secondshot_1p_intlg_BU",
                                 "weapon_car_secondshot_1p_intmed", "weapon_car_secondshot_1p_intmed_BU",
                                 "weapon_car_secondshot_1p_intsm", "weapon_car_secondshot_1p_intsm_BU"],
    "weapon_car_secondshot_3p": ["weapon_car_secondshot_3p", "weapon_car_secondshot_3p_BU1", "weapon_car_secondshot_3p_OLD2",
                                 "weapon_car_secondshot_3p_enemy", "weapon_car_secondshot_3p_enemy_BU",
                                 "weapon_car_secondshot_3p_enemy_BU1", "weapon_car_secondshot_3p_enemy_OLD2",
                                 "weapon_car_secondshot_3p_enemy_intlg", "weapon_car_secondshot_3p_enemy_intlg_BU1",
                                 "weapon_car_secondshot_3p_enemy_intlg_OLD2", "weapon_car_secondshot_3p_enemy_intmed",
                                 "weapon_car_secondshot_3p_enemy_intmed_BU1", "weapon_car_secondshot_3p_enemy_intmed_OLD2",
                                 "weapon_car_secondshot_3p_enemy_intsm", "weapon_car_secondshot_3p_enemy_intsm_BU1",
                                 "weapon_car_secondshot_3p_enemy_intsm_OLD2", "weapon_car_secondshot_3p_int",
                                 "weapon_car_secondshot_3p_int_enemy", "weapon_car_secondshot_3p_intlg",
                                 "weapon_car_secondshot_3p_intlg_OLD2", "weapon_car_secondshot_3p_intmed",
                                 "weapon_car_secondshot_3p_intmed_OLD2", "weapon_car_secondshot_3p_intsm",
                                 "weapon_car_secondshot_3p_intsm_OLD2",
                                 "weapon_car_firstshot_3p_BU1", "weapon_car_firstshot_3p_enemy"],
    "weapon_car_secondshot_npc": ["weapon_car_secondshot_npc", "weapon_car_secondshot1_npc",
                                  "weapon_car_secondshot_npc_intlg", "weapon_car_secondshot_npc_intmed",
                                  "weapon_car_secondshot_npc_intsm", "weapon_car_firstshot_npc_BU1"],
    "car_lowammo_shot1": ["car_lowammo_shot1"],
}
LIST = Path(r"D:\TitanfallMods\35_ProwlerCAR\audio_raw\events\tf2_all_audio_events.txt")
KNOWN = {l.split(",", 1)[1].strip() for l in LIST.read_text().splitlines() if "," in l}
_missing = [e for ids in EVENTS.values() for e in ids if e not in KNOWN]
assert not _missing, f"event ids not in the TF2 bank list: {_missing}"
_flat = [e for ids in EVENTS.values() for e in ids]
assert len(_flat) == len(set(_flat)), "an EventId is listed twice (Northstar keeps only the first)"

# remove previously generated definitions (capitalised names never matched in game)
for old in list(OUT.glob("*.json")):
    if old.stem not in EVENTS:
        folder = OUT / old.stem
        for w in folder.glob("*.wav"):
            w.unlink()
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
        old.unlink()


HEADROOM = 10 ** (-6 / 20)       # -6 dBFS: the burst start plays FirstShot and the loop on top of each other,
                                 # and the game mixes on top; 0.1.15 shipped both at -0.2 dBFS and distorted


def write(event, a, name="1.wav"):
    # clean linear gain only (no saturation/limiting: that is distortion too); FirstShot and the loop both
    # peak near full scale before this, so the same -6 dB keeps the hand-off balance between them
    peak = float(np.max(np.abs(a))) or 1.0
    if peak > HEADROOM:
        a = a * (HEADROOM / peak)
    pcm = (np.clip(a, -1, 1) * 32767).astype("<i2")
    d = OUT / event                                   # sample folder = definition file stem
    d.mkdir(parents=True, exist_ok=True)
    with wave.open(str(d / name), "wb") as w:        # RIFF/fmt/data only
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    (OUT / f"{event}.json").write_text(json.dumps({"EventId": EVENTS[event], "AudioSelectionStrategy": "sequential"}, indent=1))
    REPORT[event] = {"seconds": round(len(a) / SR, 3), "peak": round(min(peak, HEADROOM), 3), "ids": len(EVENTS[event])}


loop1p = src("Wpn_ProwlerPDW_1p_WpnFire_Loop_Close_C_v1_01")      # quiet centre layer of the 1p loop
mech1p = src("Wpn_ProwlerPDW_1p_WpnFire_Loop_Mech_2ch_v1_01")
# no reactive "Fire_Swt" sweetener: it is a decaying one-shot, and slicing it like a loop made the
# full-auto loop stutter (40/40/60 ms) and fade over its 4 s
loop3p = src("Wpn_ProwlerPDW_3p_WpnFire_Loop_Close_2ch_v1_01")
loopmid = src("Wpn_ProwlerPDW_3p_WpnFire_Loop_Mid_2ch_v1_01")
p1, pm, p3, pmid = period(loop1p), period(mech1p), period(loop3p), period(loopmid)
REPORT["periods_ms"] = {"1p": round(p1 * 1000, 1), "mech": round(pm * 1000, 1), "3p": round(p3 * 1000, 1), "mid": round(pmid * 1000, 1)}

def rms(a):
    return float(np.sqrt(np.mean(a ** 2))) or 1e-9


first = src("Wpn_ProwlerPDW_1p_WpnFire_FirstShot_Close_2ch_v1_01")
write("weapon_car_firstshot_1p", first)
# full-auto body = the Prowler close loop (3p Close carries the report; 1p centre + mech add the
# in-hand detail), all re-laid at the CAR rate
loop_1p = mix((resequence(loop3p, p3), 1.0), (resequence(loop1p, p1), 4.0), (resequence(mech1p, pm), 0.45))
# match the loop's per-shot loudness to the first shot's body (first 70 ms) so the hand-off is seamless
target = rms(first[: int(0.07 * SR)])
shot = rms(loop_1p[: int(SR / CAR_RPS) * 8])
loop_1p *= min(4.0, target / shot)
REPORT["loop1p_gain"] = round(min(4.0, target / shot), 3)
write("weapon_car_loop_1p", loop_1p)
write("weapon_car_loopend_1p", fade_tail(src("Wpn_ProwlerPDW_3p_WpnFire_Tail_Mid_2ch_v1_01"), 2.2))
write("weapon_car_loop_3p", resequence(loop3p, p3))
write("weapon_car_loopend_3p", fade_tail(src("Wpn_ProwlerPDW_3p_WpnFire_Tail_Mid_2ch_v1_02"), 2.5))
write("weapon_car_loop_3p_npc_a", resequence(loopmid, pmid))
write("weapon_car_loopend_npc", fade_tail(src("Wpn_ProwlerPDW_3p_WpnFire_Tail_Mid_2ch_v1_03"), 2.5))
# the CAR also plays fire_sound_2 (secondshot) on every shot: that is the stock CAR crack layered over
# the loop, so it is replaced by silence (the loop already carries every shot). 50 ms > Northstar's
# 45-byte EMPTY_WAVE header copy.
for ev in ("weapon_car_secondshot_1p", "weapon_car_secondshot_3p", "weapon_car_secondshot_npc"):
    write(ev, np.zeros((int(0.05 * SR), 2), np.float32))
write("car_lowammo_shot1", mix((src("Wpn_ProwlerPDW_3p_WpnFire_LowAmmo_Pop_2ch_v1_01"), 0.8),
                               (src("Wpn_ProwlerPDW_3p_WpnFire_LowAmmo_Mech_2ch_v1_01"), 0.6)))
(Path(r"D:\TitanfallMods\35_ProwlerCAR\build") / "audio_report.json").write_text(json.dumps(REPORT, indent=1))
print("AUDIO_OK", json.dumps(REPORT))
