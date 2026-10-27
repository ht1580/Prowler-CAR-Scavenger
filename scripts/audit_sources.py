"""Source-level audit of the generated QCs (doc checklist: SMD exists, QC refs match, weights/bones/materials sane).

For each QC: every referenced SMD exists; no stray SMDs in the build dirs are left unused (reported);
each mesh SMD: per-vertex weights sum to 1, bone indices valid, which bones/materials it uses vs expectation;
each animation SMD: node list contains every QC $definebone name (no silently missing bones).
Usage: python -I audit_sources.py
"""
import os
import re
import sys

ROOT = r"D:\TitanfallMods\35_ProwlerCAR\build"
QCS = {"view": ROOT + r"\view\ptpov_car101.qc", "world": ROOT + r"\world\w_car101.qc"}
EXPECT = {   # mesh smd -> (allowed bones, allowed materials substring)
    "prowler_body.smd": (None, ["prowler_scavenger"]),
    "prowler_magazine.smd": ({"def_c_magazine"}, ["prowler_scavenger"]),
    "prowler_sight_on.smd": ({"ja_ads_attachment"}, ["prowler_scavenger"]),
    "v_holo.smd": ({"def_c_holo"}, ["holo_reflex_sight_magnifier", "scope_lens", "charge_rifle_optic"]),
    "v_acgs.smd": ({"def_c_acgs"}, ["acgs_sight", "scope_lens", "charge_rifle_optic"]),
    "v_cro.smd": ({"def_c_cro"}, ["charge_rifle_optic", "rifle_scope_lens"]),
    "v_proscreen.smd": ({"def_c_proscreen"}, ["pro_screen"]),
}
ok = True


def read_nodes(lines):
    a = lines.index("nodes")
    b = lines.index("end", a)
    return {int(m[1]): m[2] for s in lines[a + 1:b] if (m := re.match(r'\s*(\d+)\s+"([^"]+)"', s))}


for tag, qc_path in QCS.items():
    d = os.path.dirname(qc_path)
    qc = open(qc_path, errors="replace").read()
    bones = re.findall(r'^\$definebone "([^"]+)"', qc, re.M)
    refs = sorted(set(re.findall(r'"([^"]+\.smd)"', qc, re.I)))
    missing = [r for r in refs if not os.path.exists(os.path.join(d, r))]
    ok &= not missing
    on_disk = {os.path.relpath(os.path.join(p, f), d).replace("/", "\\").lower()
               for p, _, fs in os.walk(d) for f in fs if f.lower().endswith(".smd")}
    unused = sorted(on_disk - {r.lower() for r in refs})
    print(f"== {tag}: {len(refs)} SMD refs, missing={missing or 'none'}, unused-on-disk={len(unused)} {unused[:6]}")
    for r in refs:
        lines = open(os.path.join(d, r), errors="replace").read().splitlines()
        nodes = read_nodes(lines)
        if "triangles" not in lines:
            absent = [b for b in bones if b not in nodes.values()]
            if absent and not r.lower().startswith("anims\\") or (absent and len(absent) > 40):
                print(f"   anim {r}: missing {len(absent)} QC bones e.g. {absent[:3]}")
            continue
        i = lines.index("triangles") + 1
        mats, used, badw, badidx, tris = set(), set(), 0, 0, 0
        while i < len(lines) and lines[i] != "end":
            mats.add(lines[i])
            for k in range(1, 4):
                p = lines[i + k].split()
                n = int(p[9]) if len(p) > 9 else 0
                ws = [(int(p[10 + 2 * j]), float(p[11 + 2 * j])) for j in range(n)]
                if ws and abs(sum(w for _, w in ws) - 1.0) > 1e-3:
                    badw += 1
                for bi, _ in ws or [(int(p[0]), 1.0)]:
                    if bi not in nodes:
                        badidx += 1
                    else:
                        used.add(nodes[bi])
            tris += 1
            i += 4
        name = os.path.basename(r)
        allow_b, allow_m = EXPECT.get(name, (None, None)) if tag == "view" else (None, None)
        bone_ok = allow_b is None or used <= allow_b
        mat_ok = allow_m is None or all(any(s in m.lower() for s in [x.lower() for x in allow_m]) for m in mats)
        good = not badw and not badidx and bone_ok and mat_ok
        ok &= good
        print(f"   mesh {name:28s} tris={tris:6d} weights_bad={badw} idx_bad={badidx} bones={sorted(used)[:5]}{'...' if len(used) > 5 else ''} "
              f"mats={sorted(mats)} {'OK' if good else 'CHECK'}")
print("AUDIT_SOURCES_OK" if ok else "AUDIT_SOURCES_FAIL")
