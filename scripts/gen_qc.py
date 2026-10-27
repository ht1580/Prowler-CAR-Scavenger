"""blender -b -P gen_qc.py : stock CAR QC -> Prowler QC (same sequences/events/activities/layers)."""
import json
import math
import re
from mathutils import Matrix, Vector
import os
import sys
from pathlib import Path

ROOT = r"D:\TitanfallMods\35_ProwlerCAR"
STOCK = ROOT + r"\stock\view\ptpov_car101.qc"
OUT = ROOT + r"\build\view"
sk = json.load(open(OUT + r"\skeleton.json"))
order, parent = sk["final_order"], sk["final_parent"]
rest_local = {n: Matrix(m) for n, m in sk["rest_local"].items()}
rest_global = {n: Matrix(m) for n, m in sk["rest_global"].items()}
rep = sk["report"]
qc = open(STOCK, encoding="utf-8", errors="replace").read()
BODY_MAT = r"models\Weapons_R2\prowler_car\prowler_scavenger"
sys.path.insert(0, ROOT + r"\scripts")
from mdl_lib import Mdl
from smdlib import read_smd
stock_mdl = Mdl(ROOT + r"\stock\models\weapons\car101\ptpov_car101.mdl")


def absolute_delta_source(filename, crowbar_coordinates=False):
    """Give SFM an absolute pose, then let subtract(ref, 0) encode real deltas.

Crowbar writes raw delta SMDs but omits subtract commands. A sequence's delta
flag alone does not mark the underlying $animation as a delta in SFM.
Keep the raw SMD intact so repeated QC generation is deterministic.
"""
    source_nodes, frames, _ = read_smd(OUT + "\\anims\\" + filename)
    source_ids = {name: index for index, (name, _) in source_nodes.items()}
    result = ["version 1", "nodes"]
    result += [f'{index} "{name}" {order.index(parent[name]) if parent[name] else -1}' for index, name in enumerate(order)]
    result += ["end", "skeleton"]
    for index, frame in enumerate(frames):
        result.append(f"time {index}")
        for bone_index, name in enumerate(order):
            delta = frame[source_ids[name]] if name in source_ids else Matrix.Identity(4)
            # Crowbar rotates ROOT coordinates -90 degrees for SMD export even
            # when the decoded animation is an identity delta. Undo that export
            # basis before composing the delta with the bind pose. Authored
            # spinner/fire deltas already use the true local basis.
            if crowbar_coordinates and parent[name] is None:
                delta = Matrix.Rotation(math.pi / 2, 4, "Z") @ delta
            rest = rest_local[name]
            position = rest.to_translation() + delta.to_translation()
            rotation = (rest.to_quaternion() @ delta.to_quaternion()).to_euler("XYZ")
            result.append(f"{bone_index} " + " ".join(f"{value:.6f}" for value in (*position, *rotation)))
    result += ["end", ""]
    directory = OUT + r"\anims\delta_absolute"
    os.makedirs(directory, exist_ok=True)
    open(directory + "\\" + filename, "w", encoding="ascii", newline="\n").write("\n".join(result))
    return "delta_absolute\\" + filename


def definebone(n):
    m = rest_local[n]
    t = m.to_translation()
    e = [math.degrees(a) for a in m.to_euler("XYZ")]
    p = parent[n] or ""
    return f'$definebone "{n}" "{p}" {t.x:.6f} {t.y:.6f} {t.z:.6f} {e[1]:.6f} {e[2]:.6f} {e[0]:.6f} 0 0 0 0 0 0'


# 1) bodygroups
qc = qc.replace('studio "v_car101.smd"', 'studio "prowler_body.smd"')
qc = qc.replace('studio "v_car101_sight_on.smd"', 'studio "prowler_sight_on.smd"')
qc = qc.replace('studio "v_car101_magazine.smd"', 'studio "prowler_magazine.smd"')
# no glow, no client script (0.1.20): the attachment table stays exactly the stock CAR's

# 2) skin families: every family -> the Prowler material (camo/elite/prime indexes stay valid)
qc = re.sub(r'\{ "models\\Weapons_R2\\car_smg\\CAR_smg[^"]*"\s*\}', '{ "' + BODY_MAT.replace("\\", "\\\\") + '" }', qc)

# 3) skeleton
lines = qc.split("\n")
first = next(i for i, l in enumerate(lines) if l.startswith("$definebone"))
last = max(i for i, l in enumerate(lines) if l.startswith("$definebone"))
lines[first:last + 1] = [definebone(n) for n in order]
qc = "\n".join(lines)
# HK560 (Titanfall2AnimationModTutorial, "使用$bonemerge"): declare every merged-in bone with $bonemerge so
# studiomdl never collapses/optimises it; the stock list (73) is kept as is, the new Prowler bones are appended
stock_merge = set(re.findall(r'^\$bonemerge "([^"]+)"', qc, re.M))
CAR_BONES = set(stock_mdl.bones())
new_merge = [n for n in order if n not in stock_merge and n not in CAR_BONES]
assert len(new_merge) == len(order) - len(CAR_BONES), (len(new_merge), len(order), len(CAR_BONES))
last_merge = list(re.finditer(r'^\$bonemerge "[^"]+"\n', qc, re.M))[-1]
qc = qc[:last_merge.end()] + "".join(f'$bonemerge "{n}"\n' for n in new_merge) + qc[last_merge.end():]

# 4) attachments that sat on CAR-specific geometry
base = rest_global["def_c_base"]
shell_rel = rep.get("shell_rel")
def repl_att(name, newpos):
    global qc
    qc = re.sub(r'(\$attachment "' + name + r'" "def_c_base") [-\d.]+ [-\d.]+ [-\d.]+',
                lambda m: m.group(1) + f" {newpos[0]:.2f} {newpos[1]:.2f} {newpos[2]:.2f}", qc)
if shell_rel:
    repl_att("shell", shell_rel)
    repl_att("shell_fp", shell_rel)

# 5) animations from the rebuilt set
qc = qc.replace("ptpov_car101_anims\\", "anims\\")

# Restore the actual animation encoding, not only the sequence descriptor.
# noanimation (0x20) descriptors already carry DELTA and have no motion payload.
delta_anims = [name for row, name in stock_mdl.table(184, 92, 4)
               if stock_mdl.i(row + 12) & 4 and not stock_mdl.i(row + 12) & 0x20]
for name in delta_anims:
    assert not name.startswith("@"), f"inline stock delta requires explicit handling: {name}"
    filename = name + ".smd"
    # Decide from the data, not from byte identity: build_view copies the stock attack deltas (root
    # included) and only adds the bolt/spring kick and drum turn, so those files differ from the
    # decompile yet still carry Crowbar's -90 deg root. 0.1.12/0.1.13 missed exactly these, and every
    # shot then turned the whole viewmodel 90 deg ("the model flies away when firing").
    raw_nodes, raw_frames, _ = read_smd(OUT + "\\anims\\" + filename)
    root_id = next(i for i, (nm, p) in raw_nodes.items() if p == -1)
    root_rots = {tuple(round(a, 4) for a in fr[root_id].to_euler("XYZ")) for fr in raw_frames}
    crowbar_coordinates = root_rots == {(0.0, 0.0, round(-math.pi / 2, 4))}
    assert crowbar_coordinates or root_rots == {(0.0, 0.0, 0.0)}, f"unexpected root delta in {filename}: {root_rots}"
    rebased = absolute_delta_source(filename, crowbar_coordinates=crowbar_coordinates)
    pattern = r'(^\$animation "' + re.escape(name) + r'" )"anims\\[^\"]+"( \{)'
    qc, changed = re.subn(pattern, lambda match: match.group(1) + '"anims\\' + rebased + '"' + match.group(2) + '\n\tsubtract "ref" 0', qc, flags=re.M)
    assert changed == 1, f"delta $animation declaration missing: {name}"

# 6) drum spin the stock L-STAR way: "fire_layer" = looping delta sequence, no activity, which the engine
#    plays by name while firing (L-STAR: flags loop|delta|realtime, nothing in script or other sequences
#    references it). APPENDED after the stock sequences (stock indices unchanged; HK560: new sequences only at
#    the end). No pose parameter, no autoplay layer, no client script: 0.1.17-0.1.19 drove the drum that way
#    and it flew whenever it turned.
fire_src = absolute_delta_source(rep["fire_layer"]["file"])
spin_bones = {"def_c_bolt"}                      # the coil drum rides the stock bolt bone
weights = '\n$weightlist "drum_only" {\n' + "\n".join(
    f'\t"{name}" {1 if name in spin_bones else 0}' for name in order) + '\n}\n\n'
first_animation = qc.index("$animation ")
qc = qc[:first_animation] + weights + qc[first_animation:]
fire_seq = ['$sequence "fire_layer" {', f'\t"anims\\{fire_src}"', '\tweightlist "drum_only"', '\tsubtract "ref" 0',
            "\tdelta", "\tfadein 0.1", "\tfadeout 0.2", "\tfps 16", "\tloop", "}", ""]   # 8 steps @16 fps = 2 turns/s; flags = L-STAR's 0x15
qc = qc.rstrip("\n") + "\n\n" + "\n".join(fire_seq) + "\n"
spin = [fire_src]

# ---- re-emit $animation/$sequence blocks in the stock MDL's anim-desc order -------------------------
# Crowbar writes all $animation blocks first, so inline-sequence anims (@ref, @reload_seq, ...) would land at
# the end of the anim table. Walk the stock anim table: named anims emit their $animation block; "@seq" entries
# emit (in stock sequence order) every pending sequence up to that one. Result: identical anim AND seq indices.
import sys as _sys
_sys.path.insert(0, ROOT + r"\scripts")
from mdl_lib import Mdl


def top_blocks(text, kind):
    out = []
    for m in re.finditer(r'^\$' + kind + r' "([^"]+)"', text, re.M):
        i = text.index("{", m.end())
        depth, j = 1, i + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        out.append((m.group(1), m.start(), j))
    return out


anim_blocks = top_blocks(qc, "animation")
seq_blocks = top_blocks(qc, "sequence")
region_start = min(s for _, s, _ in anim_blocks + seq_blocks)
region_end = max(e for _, _, e in anim_blocks + seq_blocks)
atext = {n: qc[s:e] for n, s, e in anim_blocks}
stext = {n: qc[s:e] for n, s, e in seq_blocks}
seq_order = [n for n, _, _ in seq_blocks]
stock_anims = stock_mdl.anims()
assert [s["name"] for s in stock_mdl.sequences()] == seq_order[:len(stock_mdl.sequences())]


def seq_anim_refs(body):
    return [r for r in re.findall(r'^\s*"([^"]+)"\s*$', body, re.M) if not r.lower().endswith(".smd")]


emitted_a, emitted_s, out_blocks = set(), [], []


def emit_seq(name):
    for ref in seq_anim_refs(stext[name]):
        assert ref in emitted_a, f"sequence {name} needs $animation {ref} before it"
    out_blocks.append(stext[name])
    emitted_s.append(name)


for a in stock_anims:
    if a.startswith("@"):
        target = a[1:]
        while target not in emitted_s:
            nxt = seq_order[len(emitted_s)]
            inline_first = seq_anim_refs(stext[nxt]) == [] and nxt != target
            assert not inline_first, f"inline sequence {nxt} would be emitted before {target}"
            emit_seq(nxt)
    else:
        out_blocks.append(atext[a])
        emitted_a.add(a)
for name in seq_order[len(emitted_s):]:          # remaining (non-inline) stock sequences + appended ones
    emit_seq(name)
assert len(out_blocks) == len(anim_blocks) + len(seq_blocks)
qc = qc[:region_start] + "\n\n".join(out_blocks) + "\n" + qc[region_end:]

# guard: every stock sequence / attachment / bodygroup / pose parameter keeps its index
stock = open(STOCK, encoding="utf-8", errors="replace").read()
for kind in ("sequence", "attachment", "bodygroup", "poseparameter"):
    a = re.findall(r'^\$' + kind + r' "([^"]+)"', stock, re.M)
    b = re.findall(r'^\$' + kind + r' "([^"]+)"', qc, re.M)
    assert b[:len(a)] == a, f"{kind} order differs from stock"
print("ORDER_OK", {k: len(re.findall(r'^\$' + k + ' ', qc, re.M)) for k in ("sequence", "attachment", "bodygroup", "poseparameter")})

qc = qc.replace('$modelname "weapons/car101/ptpov_car101.mdl"',
                '$modelname "weapons/car101/ptpov_car101.mdl"\n$maxverts 65000')
open(OUT + r"\ptpov_car101.qc", "w", encoding="ascii", errors="replace", newline="\n").write(qc)
print("GEN_QC_OK", len(order), "bones")
print("DELTA_SOURCES_OK", len(delta_anims), "stock delta animations and", len(spin), "fire layer")
