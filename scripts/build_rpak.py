"""Prowler reactive textures -> DDS -> RePak 1.2 (inline map, B3 template) with native coil emission."""
import json
import struct
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(r"D:\TitanfallMods\35_ProwlerCAR")
SRC = Path(r"D:\Apex_猎兽进化皮_v21_scavenger\02_贴图_Textures\基础色_base")
TEXCONV = r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench\vendor\tools\texconv.exe"
REPAK = r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench\vendor\tools\RePak-1.2.0.exe"
NAME = "prowler_car"
MAT = "models/Weapons_R2/prowler_car/prowler_scavenger"
TEXDIR = "texture/models/Weapons_R2/prowler_car"
R = ROOT / "repak"
ASSETS = R / "assets" / TEXDIR
STAGE = R / "png"
EMISSIVE_TINT = [2.2, 0.75, 0.22]       # Apex reactive L2 (emissiveIntensity 2) hot-coil orange

# suffix: (format, srgb)
SPEC = {
    # gls as BC7 linear: RePak 1.2 crashes (0xC0000409) on BC4 input; B3 shipped BC7 for every slot
    "col": ("BC7_UNORM_SRGB", True), "nml": ("BC5_UNORM", False), "gls": ("BC7_UNORM", False),
    "spc": ("BC7_UNORM_SRGB", True), "ao": ("BC7_UNORM", False), "cav": ("BC7_UNORM", False),
    "ilm": ("BC7_UNORM", False),
}
DXGI = {"BC7_UNORM_SRGB": 99, "BC5_UNORM": 83, "BC4_UNORM": 80, "BC7_UNORM": 98}

ASSETS.mkdir(parents=True, exist_ok=True)
STAGE.mkdir(parents=True, exist_ok=True)
(R / "maps").mkdir(parents=True, exist_ok=True)
report = {}
for suf, (fmt, srgb) in SPEC.items():
    im = Image.open(SRC / f"prowler_v21_react_scavenger_{suf}.png")
    if suf == "col":
        im = im.convert("RGB").convert("RGBA")          # alpha forced to 255 (Codex rule)
    elif suf in ("gls", "ao", "cav", "ilm"):
        im = im.convert("L").convert("RGBA")
    else:
        im = im.convert("RGBA")
    stem = f"prowler_scavenger_{suf}"
    png = STAGE / f"{stem}.png"
    im.save(png)
    args = [TEXCONV, "-nologo", "-y", "-dx10", "-m", "0", "-f", fmt, "-o", str(ASSETS), str(png)]
    args[1:1] = ["-srgb"] if srgb else ["--ignore-srgb"]
    subprocess.run(args, check=True, capture_output=True)
    dds = ASSETS / f"{stem}.dds"
    data = dds.read_bytes()
    assert data[:4] == b"DDS " and data[84:88] == b"DX10", stem
    dxgi = struct.unpack_from("<I", data, 128)[0]
    assert dxgi == DXGI[fmt], (stem, dxgi)
    report[suf] = {"format": fmt, "dxgi": dxgi, "bytes": len(data)}


def tex(s):
    return f"{TEXDIR}/prowler_scavenger_{s}"


def matl(kind, subtype):
    textures = [tex("col"), tex("nml"), tex("gls"), tex("spc"), tex("ilm")] + [""] * 6 + [tex("ao"), tex("cav")]
    # RePak 1.2 reads "selfillumtint" (RGBA) for emission; "emissiveTint"/"albedoTint" are ignored keys
    return {"$type": "matl", "subtype": subtype, "type": kind,
            "shaderset": f"shaderset/uberAoCavEmitEntcolmeSamp2222222_{kind}.rpak",
            "version": 12, "path": MAT, "surface": "weapon", "width": 2048, "height": 2048,
            "selfillumtint": EMISSIVE_TINT + [1.0], "textures": textures,
            "visibilityflags": "opaque", "faceflags": 6}


m = {"name": NAME, "assetsDir": "../assets", "outputDir": "../build", "version": 7,
     "starpakPath": f"{NAME}.starpak",
     "files": [{"$type": "txtr", "path": tex(s)} for s in SPEC] + [matl("skn", "viewmodel"), matl("fix", "worldmodel_noglow")]}
mp = R / "maps" / f"{NAME}.json"
mp.write_text(json.dumps(m, indent=2))
r = subprocess.run([REPAK, str(mp)], cwd=str(R / "maps"), capture_output=True, text=True, errors="replace")
(R / "repak.log").write_text(r.stdout + r.stderr)
out = R / "build"
built = {p.name: p.stat().st_size for p in out.glob(f"{NAME}.*")} if out.exists() else {}
report["repak_exit"] = r.returncode
report["built"] = built
(R / "rpak_report.json").write_text(json.dumps(report, indent=2))
print("RPAK", r.returncode, built)
if r.returncode != 0 or f"{NAME}.rpak" not in built:
    print(r.stdout[-2000:], r.stderr[-2000:])
    sys.exit(1)
