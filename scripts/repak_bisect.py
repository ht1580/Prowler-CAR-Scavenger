"""Find which map feature crashes RePak 1.2 by toggling one thing at a time."""
import copy
import json
import subprocess
from pathlib import Path

R = Path(r"D:\TitanfallMods\35_ProwlerCAR\repak")
REPAK = r"D:\CodexStorage\Projects\2026-09-08\w-3\TitanfallModWorkbench\vendor\tools\RePak-1.2.0.exe"
base = json.loads((R / "maps" / "prowler_car.json").read_text())


def run(label, m):
    m = copy.deepcopy(m)
    m["name"] = "bisect"
    m["starpakPath"] = "bisect.starpak"
    p = R / "maps" / "bisect.json"
    p.write_text(json.dumps(m, indent=1))
    r = subprocess.run([REPAK, str(p)], cwd=str(R / "maps"), capture_output=True, text=True, errors="replace")
    tail = (r.stdout.strip().splitlines() or [""])[-1][:120]
    print(f"{label:34s} exit={r.returncode} last='{tail}'")


run("as-is", base)
m = copy.deepcopy(base); m["files"] = [f for f in m["files"] if f["$type"] == "txtr"]; run("textures only", m)
for suf in ("col", "nml", "gls", "spc", "ao", "cav", "ilm"):
    m = copy.deepcopy(base); m["files"] = [f for f in m["files"] if f["$type"] == "txtr" and f["path"].endswith(suf)]; run(f"only {suf}", m)
m = copy.deepcopy(base); m.pop("starpakPath"); m["files"] = [f for f in m["files"] if f["$type"] == "txtr"][:1]; run("col no starpak", m)
