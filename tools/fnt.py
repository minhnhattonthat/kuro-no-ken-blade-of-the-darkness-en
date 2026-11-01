"""fnt.py: SYS.MPS/SYSTEM.FNT (12x12 1bpp, 18 bytes per glyph, rows MSB first, 5224 glyphs).

    python tools/fnt.py sheet SYSTEM.FNT OUT.png [FIRST] [COUNT]   # 32 glyphs per row, index labels per row
"""
import sys
from PIL import Image, ImageDraw

W = H = 12
SIZE = 18


def glyph(data, i):
    bits = int.from_bytes(data[i * SIZE:(i + 1) * SIZE], "big")
    return [[(bits >> (SIZE * 8 - 1 - (y * W + x))) & 1 for x in range(W)] for y in range(H)]


def sheet(data, first, count, scale=2):
    cols = 32
    rows = (count + cols - 1) // cols
    img = Image.new("RGB", (40 + cols * 14 * scale, rows * 14 * scale), "white")
    d = ImageDraw.Draw(img)
    for k in range(count):
        i = first + k
        r, c = divmod(k, cols)
        if c == 0:
            d.text((2, r * 14 * scale + 4), f"{i}", fill="red")
        g = glyph(data, i)
        for y in range(H):
            for x in range(W):
                if g[y][x]:
                    X, Y = 40 + c * 14 * scale + x * scale, r * 14 * scale + y * scale
                    d.rectangle([X, Y, X + scale - 1, Y + scale - 1], fill="black")
    return img


if __name__ == "__main__":
    data = open(sys.argv[2], "rb").read()
    first = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    count = int(sys.argv[5]) if len(sys.argv) > 5 else min(512, len(data) // SIZE - first)
    sheet(data, first, count).save(sys.argv[3])
