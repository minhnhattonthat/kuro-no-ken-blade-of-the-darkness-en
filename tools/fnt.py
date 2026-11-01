"""fnt.py: SYSTEM.FNT codec — full-width (SJIS) and half-width (ASCII) glyphs.

    python -X utf8 tools/fnt.py sheet FILE OUT.png [FIRST] [COUNT]   # full-width glyphs, 32 per row, code labels
    python -X utf8 tools/fnt.py ascii FILE OUT.png                   # the 0x10 half-width table (0x20-0x7e)
    python -X utf8 tools/fnt.py ascii-write FILE                     # add the missing punctuation glyphs in place
    python -X utf8 tools/fnt.py dump FILE CODE                      # one glyph as text (# = lit)

Formats (docs/re/font.md, both verified against the game's own decoder and against screenshots):
  full-width  offset 0x3150 + 48*i, i = index in the 0x2410 code list; 12 rows of 4 bytes, each row is a
              12-digit base-6 number, most significant digit = leftmost pixel, 6 grey levels (0-5).
  half-width  offset 0x10 + 36*code; 12 rows of 3 bytes = 8 pixels of 3 bits, MSB first, 8 grey levels.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HDR, ASCII, CODES, GLYPHS, COUNT = 0x10, 0x10, 0x2410, 0x3150, 0x686
W, H = 8, 12


def codes(data):
    return [int.from_bytes(data[CODES + 2 * i:CODES + 2 * i + 2], "big") for i in range(COUNT)]


def sjis_rows(data, i):
    g = data[GLYPHS + 48 * i:GLYPHS + 48 * (i + 1)]
    rows = []
    for y in range(12):
        v = int.from_bytes(g[4 * y:4 * y + 4], "little")
        digits = []
        for k in range(11, -1, -1):
            digits.append(v // 6 ** k)
            v %= 6 ** k
        rows.append(digits)
    return rows


def ascii_rows(data, code):
    g = data[ASCII + 36 * code:ASCII + 36 * (code + 1)]
    rows = []
    for y in range(12):
        v = g[3 * y] | g[3 * y + 1] << 8 | g[3 * y + 2] << 16
        rows.append([(v >> (21 - 3 * x)) & 7 for x in range(W)])
    return rows


def ascii_bytes(rows):
    """rows: 12 lists of 8 values 0-7 -> the 36 bytes the renderer reads."""
    out = bytearray()
    for y in range(12):
        v = 0
        for x in range(W):
            v |= (rows[y][x] & 7) << (21 - 3 * x)
        out += v.to_bytes(3, "little")
    return bytes(out)


def draw(rows, maxv, scale=4, label=None):
    im = Image.new("L", (W * scale + 2, H * scale + (10 if label else 0)), 0)
    px = im.load()
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            for dy in range(scale):
                for dx in range(scale):
                    px[x * scale + dx, y * scale + dy] = int(255 * v / maxv)
    if label:
        ImageDraw.Draw(im).text((0, H * scale), label, fill=140)
    return im


def sheet(path, out, first=0, count=256, scale=3):
    data = Path(path).read_bytes()
    cs = codes(data)
    ims = [draw(sjis_rows(data, i), 5, scale, f"{i}" if (i - first) % 32 == 0 else None)
           for i in range(first, min(first + count, len(cs)))]
    cols, cw, ch = 32, ims[0].width, ims[0].height
    canvas = Image.new("L", (cols * cw, ((len(ims) + cols - 1) // cols) * ch), 0)
    for k, im in enumerate(ims):
        canvas.paste(im, ((k % cols) * cw, (k // cols) * ch))
    canvas.save(out)
    print(f"{len(ims)} glyphs -> {out}")


def ascii_sheet(path, out, scale=5):
    data = Path(path).read_bytes()
    ims = [draw(ascii_rows(data, c), 7, scale, f"{c:02x}") for c in range(0x20, 0x7F)]
    cols, cw, ch = 16, ims[0].width, ims[0].height
    canvas = Image.new("L", (cols * cw, ((len(ims) + cols - 1) // cols) * ch), 0)
    for k, im in enumerate(ims):
        canvas.paste(im, ((k % cols) * cw, (k // cols) * ch))
    canvas.save(out)
    print(f"{len(ims)} half-width glyphs -> {out}")


# 8x12 patterns for the printable ASCII the disc's font leaves blank. '#' = 7 (bright), '+' = 3.
PATTERNS = {
    "!": "........" * 0,   # '!' exists; listed below only where a glyph is missing
    '"': ["...##...", "...##...", "...##...", "........", "........", "........", "........", "........", "........", "........", "........", "........"],
    "'": ["...##...", "...##...", "...#....", "........", "........", "........", "........", "........", "........", "........", "........", "........"],
    "@": ["..####..", ".#....#.", ".#.##.#.", ".#.##.#.", ".#.##.#.", ".#.###..", ".#......", "..####..", "........", "........", "........", "........"],
    "#": ["..#..#..", "..#..#..", ".######.", "..#..#..", ".######.", "..#..#..", "..#..#..", "........", "........", "........", "........", "........"],
    "$": ["...##...", "..####..", ".#.#....", "..###...", "....#.#.", "..####..", "...##...", "........", "........", "........", "........", "........"],
    "%": ["##....#.", "##...#..", "....#...", "...#....", "..#.....", ".#...##.", "#....##.", "........", "........", "........", "........", "........"],
    "&": ["..###...", ".#...#..", ".#..#...", "..#.....", ".#.#.#..", ".#..#...", "..###.#.", "........", "........", "........", "........", "........"],
    "*": ["........", "..#.#...", "...##...", "..####..", "...##...", "..#.#...", "........", "........", "........", "........", "........", "........"],
    ";": ["........", "...##...", "...##...", "........", "........", "...##...", "...##...", "..#.....", "........", "........", "........", "........"],
    "<": [".....##.", "....##..", "...##...", "..##....", "...##...", "....##..", ".....##.", "........", "........", "........", "........", "........"],
    ">": [".##.....", "..##....", "...##...", "....##..", "...##...", "..##....", ".##.....", "........", "........", "........", "........", "........"],
    "[": ["..####..", "..#.....", "..#.....", "..#.....", "..#.....", "..#.....", "..#.....", "..####..", "........", "........", "........", "........"],
    "]": ["..####..", ".....#..", ".....#..", ".....#..", ".....#..", ".....#..", ".....#..", "..####..", "........", "........", "........", "........"],
    "^": ["...##...", "..#..#..", ".#....#.", "........", "........", "........", "........", "........", "........", "........", "........", "........"],
    "_": ["........", "........", "........", "........", "........", "........", "........", "........", "........", "........", "........", ".######."],
    "`": ["..#.....", "...#....", "........", "........", "........", "........", "........", "........", "........", "........", "........", "........"],
    "{": ["....##..", "...#....", "...#....", "..#.....", "...#....", "...#....", "....##..", "........", "........", "........", "........", "........"],
    "|": ["...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "........"],
    "}": ["..##....", "....#...", "....#...", ".....#..", "....#...", "....#...", "..##....", "........", "........", "........", "........", "........"],
    "~": ["........", "........", "..##..#.", ".#..##..", "........", "........", "........", "........", "........", "........", "........", "........"],
}


def write_ascii(path, only_missing=True):
    p = Path(path)
    data = bytearray(p.read_bytes())
    written = []
    for ch, pat in PATTERNS.items():
        assert len(pat) == 12 and all(len(s) == W for s in pat), ch
        rows = [[7 if c == "#" else 3 if c == "+" else 0 for c in line] for line in pat]
        if only_missing and any(any(r) for r in ascii_rows(bytes(data), ord(ch))):
            continue
        data[ASCII + 36 * ord(ch):ASCII + 36 * ord(ch) + 36] = ascii_bytes(rows)
        written.append(ch)
    p.write_bytes(bytes(data))
    print(f"wrote {len(written)} glyphs into {p}: {''.join(written)}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    data = Path(sys.argv[2]).read_bytes()
    if cmd == "sheet":
        sheet(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 0,
              int(sys.argv[5]) if len(sys.argv) > 5 else 256)
    elif cmd == "ascii":
        ascii_sheet(sys.argv[2], sys.argv[3])
    elif cmd == "ascii-write":
        write_ascii(sys.argv[2])
    elif cmd == "dump":
        i = codes(data).index(int(sys.argv[3], 16))
        for row in sjis_rows(data, i):
            print("".join(str(v) if v else "." for v in row))
    else:
        print(__doc__)
