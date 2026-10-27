"""python -I compare_ports.py name=path.mdl ... : how working Apex->TF2 viewmodel ports are built, side by side.
Bones (count, extra bones vs the first model = stock), sequences / pose parameters / attachments appended,
animation descriptor count, and whether the embedded animation data of each key sequence is byte-identical
to the stock model's (i.e. the port kept the TF2 animation) or replaced."""
import hashlib
import struct
import sys
sys.path.insert(0, r"D:\TitanfallMods\35_ProwlerCAR\scripts")
from mdl_lib import Mdl

models = [(a.split("=", 1)[0], Mdl(a.split("=", 1)[1])) for a in sys.argv[1:]]
stock_name, stock = models[0]
sb = stock.bones()


def anim_blob(m, name):
    """bytes of an animation's local data (anim desc -> animindex .. next anim desc's), as a fingerprint."""
    rows = m.table(184, 92, 4)
    for k, (row, n) in enumerate(rows):
        if n == name:
            start = row + m.i(row + 56)             # animindex (v53 mstudioanimdesc: +56)
            return hashlib.md5(m.d[start:start + 4096]).hexdigest()[:10]
    return None


for name, m in models:
    b = m.bones()
    extra = [x for x in b if x not in sb]
    order_ok = b[:len(sb)] == sb
    seqs = [s["name"] for s in m.sequences()]
    print(f"== {name}: bones {len(b)} (stock-prefix order {'same' if order_ok else 'DIFFERENT'}), extra {len(extra)}: {extra[:12]}{' ...' if len(extra) > 12 else ''}")
    print(f"   sequences {len(seqs)} extra {[s for s in seqs if s not in [x['name'] for x in stock.sequences()]]}  poseparams {m.poseparams()}")
    print(f"   anims {len(m.anims())}  attachments extra {[a['name'] for a in m.attachments() if a['name'] not in [x['name'] for x in stock.attachments()]]}")
    keys = ("@draw_seq", "@reload_seq", "@reload_empty_seq", "@sprint_seq", "attack_anim", "idle_anim_autoplay", "ads_in_anim")
    print("   anim data identical to stock: " + ", ".join(f"{k}:{'same' if anim_blob(m, k) == anim_blob(stock, k) else 'replaced'}" for k in keys))
