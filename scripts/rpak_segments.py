"""Check (and optionally repair) RePak 1.2 segment sizes vs page allocations (Codex car_stability.align_segments)."""
import struct
import sys
from pathlib import Path


def align_segments(path, write=False):
    d = bytearray(Path(path).read_bytes())
    assert d[:4] == b"RPak" and struct.unpack_from("<H", d, 4)[0] == 7
    assert struct.unpack_from("<Q", d, 24)[0] == struct.unpack_from("<Q", d, 40)[0] == len(d)
    stream, nseg, npages, patch = struct.unpack_from("<4H", d, 56)
    assert patch == 0
    seg = 88 + stream
    pages = seg + nseg * 16
    needed = [0] * nseg
    for i in range(npages):
        index, alignment, size = struct.unpack_from("<3I", d, pages + i * 12)
        assert index < nseg and alignment and alignment & (alignment - 1) == 0
        needed[index] = (needed[index] + alignment - 1) & ~(alignment - 1)
        needed[index] += size
    changes = []
    for i, size in enumerate(needed):
        old = struct.unpack_from("<Q", d, seg + i * 16 + 8)[0]
        if old != size:
            changes.append({"segment": i, "old": old, "required": size})
            if write:
                struct.pack_into("<Q", d, seg + i * 16 + 8, size)
    if write and changes:
        Path(path).write_bytes(d)
    return changes


if __name__ == "__main__":
    ch = align_segments(sys.argv[1], write="--fix" in sys.argv)
    print("SEGMENT_CHANGES", ch)
