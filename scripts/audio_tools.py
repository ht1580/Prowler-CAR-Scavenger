"""Audio helpers for the Prowler -> CAR sound port.

Run with Blender's bundled python (has numpy):
  python audio_tools.py analyze <wav> [<wav> ...]
"""
import sys
import subprocess
import numpy as np

FFMPEG = "ffmpeg"
SR = 48000


def load(path, sr=SR):
    """Decode any wav (incl. float32) to float32 [-1,1], shape (n, ch)."""
    probe = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
                           capture_output=True, check=True)
    a = np.frombuffer(probe.stdout, dtype=np.float32).reshape(-1, 2)
    return a.copy()


def onsets(a, sr=SR, win_ms=2.0, min_gap_ms=40.0, rel=0.35):
    """Transient onsets from an energy envelope; returns times in seconds."""
    mono = np.abs(a).mean(axis=1)
    w = max(1, int(sr * win_ms / 1000))
    env = np.convolve(mono, np.ones(w) / w, mode="same")
    d = np.diff(env, prepend=env[0])
    d[d < 0] = 0
    thr = d.max() * rel
    gap = int(sr * min_gap_ms / 1000)
    idx, last = [], -gap
    for i in np.flatnonzero(d > thr):
        if i - last >= gap:
            idx.append(i)
            last = i
    return np.array(idx) / sr


def analyze(paths):
    for p in paths:
        a = load(p)
        t = onsets(a)
        iv = np.diff(t)
        med = float(np.median(iv)) if len(iv) else 0
        print(f"{p.split(chr(92))[-1]}: dur={len(a)/SR:.2f}s onsets={len(t)} "
              f"median_interval={med*1000:.1f}ms ({1/med if med else 0:.2f}/s) first={t[:6].round(3).tolist()}")


if __name__ == "__main__":
    if sys.argv[1] == "analyze":
        analyze(sys.argv[2:])
