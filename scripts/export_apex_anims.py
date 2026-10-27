"""Export the Prowler reactive viewmodel with its anim rig + sequences (SMD) via RSX.

Uses the Respawn path->GUID hash (same as work/car_outlands/acquire.py) and the
patched rsx_nogui that accepts comma-separated GUID filters.
"""
import subprocess
import sys
from pathlib import Path

RSX = r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench\vendor\rsx\rsx_nogui.exe"
PAK = r"E:\Apex\paks\Win64\common(01).rpak"
OUT = Path(r"D:\TitanfallMods\35_ProwlerCAR\apex_native")


def guid(name):
    data = name.encode() + b"\0" * 8
    v1 = 0
    i = 0
    mask = (1 << 64) - 1
    while True:
        word = int.from_bytes(data[i:i + 4], "little")
        v4 = (~word & (word - 0x1010101) & 0x80808080) & 0xffffffff
        v5 = (v4 ^ (v4 - 1)) & 0xffffffff
        v6 = ((v5 & word) ^ 0x5c5c5c5c) & 0xffffffff
        v7 = (~v6 & (v6 - 0x1010101) & 0x80808080) & 0xffffffff
        v8 = v7 & -v7
        if v7 != v8:
            for v9 in (0xff000000, 0xff0000, 0xff00, 0xff):
                if v9 & v6 == 0:
                    v8 |= v9 & 0x80808080
        v11 = (0x633d5f1 * v1) & mask
        v12 = ((0xfb8c4d96501 * ((((v5 & word) - 45 * (v8 >> 7)) & 0xffffffff) & 0xdfdfdfdf)) & mask) >> 24
        if v4:
            break
        total = (v11 + v12) & mask
        v1 = (total >> 61) ^ total
        i += 4
    return (v12 + v11 - 0xae502812aa7333 * (i + (v5.bit_length() - 1) // 8)) & mask


if __name__ == "__main__":
    model = "mdl/techart/mshop/weapons/class/smg/prowler/prowler_react_v21_scavenger_v.rmdl"
    g = hex(guid(model))
    print("model guid", g, flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "guid":
        sys.exit(0)
    OUT.mkdir(parents=True, exist_ok=True)
    args = [RSX, "-nogui", "-export", "-exportfullpaths", "-exportdependencies", "-exportrigsequences",
            "--loadwhitelist", "arig,aseq,asqd,mdl_",
            # name-filter mode: unresolved asset names look like "mdl\0x8340E261DC9648C3"
            "--exportfilter", (sys.argv[1] if len(sys.argv) > 1 else "prowler_react_v21_scavenger_v"),
            "--exporttypes", "mdl_,arig,aseq",
            "--modelsetting", "3", "--animsetting", "3",
            "--exportdir", str(OUT), PAK]
    print(" ".join(args), flush=True)
    subprocess.run(args, cwd=str(Path(RSX).parent), check=False)

