"""mps.py: PSMG archive (*.MPS) reader/writer.

Format (docs/re/archives.md): "PSMG", u32 count, u32 data_start (header size, sector multiple), u32 0,
then count entries of 20 bytes: name[12] (NUL padded), u32 offset (from data_start), u32 size.
Entries are 0x800-aligned; gaps are zero filled.

    python tools/mps.py list FILE.MPS
    python tools/mps.py unpack FILE.MPS OUTDIR
"""
import struct
import sys
from pathlib import Path

SECTOR = 0x800


def read(data):
    """-> (data_start, [(name, offset_abs, bytes)])"""
    magic, count, start, zero = struct.unpack_from("<4sIII", data, 0)
    assert magic == b"PSMG", magic
    out = []
    for i in range(count):
        name, off, size = struct.unpack_from("<12sII", data, 16 + 20 * i)
        name = name.split(b"\0")[0].decode("ascii")
        out.append((name, start + off, data[start + off:start + off + size]))
    return start, out


def write(entries, start, total=None):
    """entries: [(name, bytes)]; packs back to back on sector boundaries. total pads the archive."""
    hdr = bytearray(struct.pack("<4sIII", b"PSMG", len(entries), start, 0))
    body = bytearray()
    for name, blob in entries:
        hdr += struct.pack("<12sII", name.encode("ascii"), len(body), len(blob))
        body += blob
        body += bytes(-len(body) % SECTOR)
    assert len(hdr) <= start, "header overflow"
    out = bytes(hdr) + bytes(start - len(hdr)) + bytes(body)
    if total is not None:
        assert len(out) <= total, f"archive grew {len(out):#x} > {total:#x}"
    return out


if __name__ == "__main__":
    cmd, path = sys.argv[1], Path(sys.argv[2])
    start, ents = read(path.read_bytes())
    if cmd == "list":
        for name, off, blob in ents:
            print(f"{off:#09x} {len(blob):#08x} {name}")
    elif cmd == "unpack":
        out = Path(sys.argv[3])
        out.mkdir(parents=True, exist_ok=True)
        for name, off, blob in ents:
            (out / name).write_bytes(blob)
        print(len(ents), "files ->", out)
