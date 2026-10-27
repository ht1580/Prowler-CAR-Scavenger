"""python -I audio_levels.py <wav or dir>... : peak / RMS (dBFS), clipped-sample count and the loudest 50 ms
window of each PCM16 WAV, to judge whether an override is hot enough to distort once the game mixes it."""
import math
import os
import struct
import sys
import wave


def levels(path):
    with wave.open(path, "rb") as w:
        ch, sr, n = w.getnchannels(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    s = struct.unpack(f"<{len(raw) // 2}h", raw)
    peak = max(abs(x) for x in s) or 1
    rms = math.sqrt(sum(x * x for x in s) / len(s)) or 1
    clip = sum(1 for x in s if abs(x) >= 32700)
    win = int(sr * 0.05) * ch
    loud = max(math.sqrt(sum(x * x for x in s[i:i + win]) / win) for i in range(0, max(1, len(s) - win), win)) or 1
    db = lambda v: 20 * math.log10(v / 32768)
    return f"{os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path):60s} {ch}ch {sr}Hz {n / sr:5.2f}s peak {db(peak):6.1f} rms {db(rms):6.1f} loud50ms {db(loud):6.1f} clipped {clip}"


for a in sys.argv[1:]:
    files = [os.path.join(r, f) for r, _, fs in os.walk(a) for f in fs if f.lower().endswith(".wav")] if os.path.isdir(a) else [a]
    for f in sorted(files):
        print(levels(f))
