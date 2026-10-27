"""Copy a v53 MDL to a unique path, rewriting its internal model name in place (same byte length).
Usage: python -I rename_mdl.py <src.mdl> <dst.mdl> <old internal name> <new internal name>
"""
import sys

src, dst, old, new = sys.argv[1:5]
assert len(old) == len(new), "internal name must keep its length (in-place rewrite)"
d = open(src, "rb").read()
o, n = old.encode(), new.encode()
hits = d.count(o)
assert hits >= 1, f"internal name {old!r} not found"
out = d.replace(o, n)
assert len(out) == len(d)
open(dst, "wb").write(out)
print("RENAME_OK", hits, "occurrence(s)", old, "->", new)
