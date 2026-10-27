import glob
import os
import sys
import numpy as np
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from audio_tools import load

for p in sorted(glob.glob(r"D:\TitanfallMods\35_ProwlerCAR\audio_raw\apex\audio\Wpn_ProwlerPDW_*WpnFire_*.wav")):
    a = np.asarray(load(p), dtype=np.float64)
    pk = np.max(np.abs(a))
    over = int(np.sum(np.abs(a) > 1.0))
    flat = int(np.sum(np.abs(a) > 0.999))
    print(f"{os.path.basename(p):60s} peak {20 * np.log10(pk):6.2f} dBFS  >1.0: {over:6d}  >=0.999: {flat:6d}  rms {20 * np.log10(np.sqrt(np.mean(a ** 2))):6.1f}")
