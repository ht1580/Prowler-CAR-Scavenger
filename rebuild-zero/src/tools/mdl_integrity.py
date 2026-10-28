"""Check the final v53 header length after embedding VTX/VVD; optionally repair it.

MDLShit carries the v49 core-MDL length into its combined file. Stock Titanfall 2
v53 models declare the length of the complete embedded file at offset 80.
"""
import argparse
import json
import struct
from pathlib import Path


def check(path, fix_length=False):
    path = Path(path)
    data = bytearray(path.read_bytes())
    assert data[:4] == b"IDST" and struct.unpack_from("<I", data, 4)[0] == 53, "Expected Titanfall v53 MDL"
    declared = struct.unpack_from("<I", data, 80)[0]
    assert 0 < declared <= len(data), "Invalid declared model length"
    assert data.find(b"IDSV") > 0, "Embedded VVD missing"
    if declared != len(data) and fix_length:
        struct.pack_into("<I", data, 80, len(data))
        path.write_bytes(data)
    actual = struct.unpack_from("<I", path.read_bytes(), 80)[0]
    assert actual == len(data), f"MDL length mismatch: {actual} != {len(data)}"
    return {"path": str(path), "old_length": declared, "file_length": len(data), "changed": declared != actual}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    parser.add_argument("--fix-length", action="store_true")
    args = parser.parse_args()
    print("MDL_INTEGRITY_OK", json.dumps([check(path, args.fix_length) for path in args.models]))
