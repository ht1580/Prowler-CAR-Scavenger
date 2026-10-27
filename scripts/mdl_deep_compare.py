"""Deep structural comparison of a built Titanfall MDL v53 against the stock one.

Every stock entry must keep its index and meaning; built extras may only be appended:
bones, bodyparts (name/options/base), attachments (name/parent bone), pose parameters, anim descs (order),
sequences (name/activity/blend grid/referenced anims/loop/delta/autoplay), skin family count.
Also: every sequence anim index (incl. appended sequences) must be a valid anim desc.
Usage: python -I mdl_deep_compare.py <stock.mdl> <built.mdl>
"""
import sys
sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from mdl_lib import Mdl


def compare(label, a, b, key=lambda x: x):
    bad = [k for k in range(len(a)) if k >= len(b) or key(a[k]) != key(b[k])]
    extra = b[len(a):]
    msg = f"{label:24s} stock {len(a):3d} built {len(b):3d}  {'OK' if not bad else 'MISMATCH'}"
    if bad:
        k = bad[0]
        msg += f"  first bad #{k}: {key(a[k])} vs {key(b[k]) if k < len(b) else None}"
    if extra:
        msg += f"  appended {len(extra)}: {[key(x) for x in extra][:3]}"
    print(msg)
    return not bad


st, bu = Mdl(sys.argv[1]), Mdl(sys.argv[2])
ok = True
ok &= compare("bones", st.bones(), bu.bones())
ok &= compare("bodyparts", st.bodyparts(), bu.bodyparts(), key=lambda x: (x["name"], x["options"], x["base"]))
ok &= compare("attachments(+bone)", st.attachments(), bu.attachments(), key=lambda x: (x["name"], x["bone"]))
ok &= compare("poseparams", st.poseparams(), bu.poseparams())
ok &= compare("anim descs (order)", st.anims(), bu.anims())
seq_key = lambda x: (x["name"], x["activity"], tuple(x["blend"]), tuple(x["anims"]), x["looping"], x["delta"], x["autoplay"])
ok &= compare("sequences (full)", st.sequences(), bu.sequences(), key=seq_key)
ok &= compare("seq anim INDICES", st.sequences(), bu.sequences(), key=lambda x: (x["name"], tuple(x["raw"])))
invalid = [(s["name"], s["raw"]) for s in bu.sequences() if any(a.startswith("#INVALID") for a in s["anims"])]
print(f"{'invalid anim refs':24s} {'none' if not invalid else invalid}")
ok &= not invalid
sk_a, sk_b = st.skins(), bu.skins()
print(f"{'skin families':24s} stock {len(sk_a)} built {len(sk_b)}  {'OK' if len(sk_a) == len(sk_b) else 'MISMATCH'}")
ok &= len(sk_a) == len(sk_b)
print("DEEP_COMPARE_OK" if ok else "DEEP_COMPARE_FAIL")
