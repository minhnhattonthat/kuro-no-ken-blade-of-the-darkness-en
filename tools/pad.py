"""pad.py: EM containers and PAD30 tiled images (docs/re/graphics.md).

EM:    "EM", u16 count, then count x (u32 offset, u32 size, char[4] ext) from byte 4... (see split_em).
PAD30: "PAD30", header 0x30 bytes: +0x08 u32 tile-map offset (0 = none), +0x0c u32 tile data offset,
       +0x10 u16 map cells, +0x12 u16 unique tiles, +0x14 u16 palette size in 16-colour units,
       +0x16 u16 cols, +0x18 u16 rows, +0x1a u16 flags (low byte = tile px 8/16, 0x1000 = 4bpp else 8bpp);
       palette (RGB555) at 0x30, optional u16 map (cell -> tile), tiles row-major.

    python tools/pad.py render FILE OUT.png      # a PAD30 file, or every .PAD inside an EM container
    python tools/pad.py sweep SRCDIR OUTDIR      # render every PAD30 found in SRCDIR/** (prints skips)
"""
import struct
import sys
from pathlib import Path

from PIL import Image


def split_em(b):
    """-> [(ext, bytes)] for an EM container, else None."""
    if b[:2] != b"EM":
        return None
    count = struct.unpack_from("<H", b, 2)[0]
    out = []
    for i in range(count):
        off, size, ext = struct.unpack_from("<II4s", b, 4 + 12 * i)
        out.append((ext.decode("latin1"), b[off:off + size]))
    return out


def pad_info(b):
    assert b[:5] == b"PAD30", b[:8]
    tmap, data = struct.unpack_from("<II", b, 0x08)
    n, n2, npal, cols, rows, flags = struct.unpack_from("<6H", b, 0x10)
    return dict(map=tmap, data=data, cells=n, tiles=n2, npal=npal * 16, ts=flags & 0xFF, cols=cols, rows=rows,
                flags=flags, bpp=4 if flags & 0x1000 else 8)


def palette(b, n=256):
    pal = []
    for i in range(n):
        v = struct.unpack_from("<H", b, 0x30 + 2 * i)[0]
        r, g, bl = (v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3
        pal.append((r, g, bl, 0 if v == 0 else 255))
    return pal


def render(b):
    h = pad_info(b)
    pal = palette(b, max(h["npal"], 16))
    pal += [(255, 0, 255, 255)] * (256 - len(pal))
    ts, bpp = h["ts"], h["bpp"]
    tb = ts * ts * bpp // 8
    img = Image.new("RGBA", (h["cols"] * ts, h["rows"] * ts))
    px = img.load()
    for c in range(min(h["cells"], h["cols"] * h["rows"])):
        t = struct.unpack_from("<H", b, h["map"] + 2 * c)[0] - 1 if h["map"] else c   # map: 0 = blank, n = tile n-1
        if t < 0:
            continue
        tile = b[h["data"] + t * tb:h["data"] + (t + 1) * tb]
        tx, ty = c % h["cols"] * ts, c // h["cols"] * ts
        for p in range(ts * ts):
            v = tile[p] if bpp == 8 else (tile[p // 2] >> (4 * (p & 1))) & 15
            px[tx + p % ts, ty + p // ts] = pal[v]
    return img


def pads(b):
    """Every PAD30 image in a file: [(label, bytes)]."""
    if b[:5] == b"PAD30":
        return [("", b)]
    em = split_em(b)
    return [(f"{i}{ext}", blob) for i, (ext, blob) in enumerate(em or []) if blob[:5] == b"PAD30"]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "render":
        for label, blob in pads(Path(sys.argv[2]).read_bytes()):
            render(blob).save(sys.argv[3].replace(".png", f"{label}.png"))
    elif cmd == "sweep":
        src, out = Path(sys.argv[2]), Path(sys.argv[3])
        n = 0
        for p in sorted(src.rglob("*")):
            if not p.is_file():
                continue
            found = pads(p.read_bytes())
            if not found:
                print("skip (no PAD30):", p.relative_to(src))
            for label, blob in found:
                dst = out / p.parent.name / f"{p.name}{label}.png"
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    render(blob).save(dst)
                    n += 1
                except Exception as e:  # report, never drop silently
                    print("skip (render error):", p.relative_to(src), label, e)
        print(n, "images ->", out)
