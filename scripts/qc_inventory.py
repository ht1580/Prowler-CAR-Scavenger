"""Inventory CAR QC sequences/animations (delta or absolute, source smd, frames) and compare skeletons."""
import re
import json
import os
import sys

V = r"D:\TitanfallMods\35_ProwlerCAR\stock\view"
A = r"D:\TitanfallMods\35_ProwlerCAR\r5r_anims\animrig\weapons\prowler_smg"
qc = open(V + r"\ptpov_car101.qc", encoding="utf-8", errors="replace").read()


def blocks(kind):
    for m in re.finditer(r'\$' + kind + r'\s+"([^"]+)"\s*(?:"([^"]+)")?\s*\{', qc):
        start = m.end()
        depth = 1
        i = start
        while depth:
            c = qc[i]
            depth += (c == "{") - (c == "}")
            i += 1
        yield m.group(1), m.group(2), qc[start:i - 1]


anims = {}
for name, src, body in blocks("animation"):
    anims[name] = {"src": src, "delta": bool(re.search(r"^\s*(delta|subtract)", body, re.M)),
                   "subtract": re.search(r'subtract\s+"([^"]+)"', body).group(1) if "subtract" in body else None}
seqs = {}
for name, src, body in blocks("sequence"):
    first = re.findall(r'^\s*"([^"]+)"', body, re.M)
    seqs[name] = {"inline": src, "anims": first[:4], "delta": bool(re.search(r"^\s*delta\b", body, re.M)),
                  "activity": (re.search(r'activity\s+"([^"]+)"', body) or [None, None])[1],
                  "events": re.findall(r"event\s+(\w+)\s+(\d+)", body)}
print("animations:", len(anims), "sequences:", len(seqs))
for n, s in seqs.items():
    print(f"{n:42s} delta={int(s['delta'])} act={s['activity']} anims={s['anims'][:2]} ev={len(s['events'])}")
print("--- $animation blocks")
for n, a in anims.items():
    print(f"{n:44s} delta={int(a['delta'])} src={a['src']} sub={a['subtract']}")
json.dump({"anims": anims, "seqs": seqs}, open(r"D:\TitanfallMods\35_ProwlerCAR\work_qc_inventory.json", "w"), indent=1)

# skeleton compare
car_bones = re.findall(r'\$definebone\s+"([^"]+)"', qc)
prw_qc = open(A + r"\ptpov_prowler_smg.qc", encoding="utf-8", errors="replace").read()
prw_bones = re.findall(r'\$definebone\s+"([^"]+)"', prw_qc)
print("CAR bones", len(car_bones), "PRW bones", len(prw_bones))
print("CAR-only:", [b for b in car_bones if b not in prw_bones])
print("PRW-only:", [b for b in prw_bones if b not in car_bones])
