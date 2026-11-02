"""gfx.py: English redraws of the Japanese drawn as graphics in SYS.MPS (docs/re/graphics.md G1, G2).

    python -X utf8 tools/gfx.py preview OUT.png     # every redrawn image next to its original, x2

G1 credits KRED00-15.PAD: 8bpp 16x16 tiles, no map, grey ramp (0 = box, 1 = outline, 2..15 = ink). Each text
band of the original keeps its place; the English is drawn centred in it with Liberation Sans (fonts/, OFL),
shrunk to fit the card width, then outlined like the original. Card sizes never change.
G2 save/load prompts WIN02.PAD: 4bpp 8x8 tiles with a map; lines at y = 16 + 16 i, x 0..143 (line 3: 0..119),
drawn with the game's own half-width font (SYSTEM.FNT), proportionally spaced. Ink 1, half-tone 4.
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fnt  # noqa: E402
import pad  # noqa: E402

FONT = ROOT / "fonts" / "LiberationSans-Bold.ttf"

# one entry per original text band, top to bottom (small = role/character label, big = name); None keeps it.
# Readings of the staff handles are best guesses (docs/decisions.md D13).
CREDITS = {
    "KRED00": ["CAST"],
    "KRED01": ["Caius", "Takehito Koyasu", "Shinobu", "Junko Iwao"],
    "KRED02": ["Zephudol", "Kiyoyuki Yanada", "Riel", "Miki Nagasawa", "Hiko", "Sayuri", "Ennis", "Ai Orikasa"],
    "KRED03": ["Galsa", "Tomoko Kawakami", "Gordon", "Nobuyuki Furuta", "Narration", "Banjo Ginga"],
    "KRED04": ["Production Director", "Toru Ishizuka"],
    "KRED05": ["Graphic Coloring", "Tatesen Rokusui", "Shinotomaru"],
    "KRED06": ["Graphic Design", "Koji Yoshikawa", "Tamao Fujii", "Ichiro Matsumoto", "Hajime Shoji", "Akka Botsu"],
    "KRED07": ["Programming", "Kou-kun", "Keijiro"],
    "KRED08": ["Sound Production", "Arper King A", "Hi-Power Anna F", "Gonteru"],
    "KRED09": ["Direction", "Toru Ishizuka", "Recording / Casting", "Natsuki", "Hanapon"],
    "KRED10": ["Package / Manual Design", "Rafflesia", "Manual Editing", "Taro Nokizaki"],
    "KRED11": ["Test Play", "Yashiron", "Tomothuke", "Kazu Itsuki", "Jiro Yamada", "Publicity", "Masanobu Watanabe"],
    "KRED13": ["General Director", "Tatsuya"],
    "KRED14": ["Produced by", "CD BROS.", None, None],
}
SAVE_LINES = ["Save to which file?", "Load which file?", "New save data",
              "Save to which slot?", "Load from which slot?"]
SAVE_WIDTH = [144, 144, 120, 144, 144]


# ------------------------------------------------------------------ KRED (8bpp, no map)

def kred_pixels(b):
    h = pad.pad_info(b)
    ts, cols = h["ts"], h["cols"]
    W, H = cols * ts, h["rows"] * ts
    px = [[0] * W for _ in range(H)]
    for c in range(h["cells"]):
        t = b[h["data"] + c * ts * ts:h["data"] + (c + 1) * ts * ts]
        for p in range(ts * ts):
            px[c // cols * ts + p // ts][c % cols * ts + p % ts] = t[p]
    return px


def kred_bytes(b, px):
    h = pad.pad_info(b)
    ts, cols = h["ts"], h["cols"]
    out = bytearray(b)
    for c in range(h["cells"]):
        o = h["data"] + c * ts * ts
        for p in range(ts * ts):
            out[o + p] = px[c // cols * ts + p // ts][c % cols * ts + p % ts]
    return bytes(out)


def bands(px):
    """[(y0, height)] of the rows holding ink (index >= 2)."""
    rows = [any(v >= 2 for v in r) for r in px]
    out, y = [], 0
    while y < len(rows):
        if rows[y]:
            s = y
            while y < len(rows) and rows[y]:
                y += 1
            out.append((s, y - s))
        else:
            y += 1
    return out


def draw_text(text, size, width):
    """-> (font, w, h, image L) at the largest size <= `size` that fits `width`."""
    while True:
        f = ImageFont.truetype(str(FONT), size)
        x0, y0, x1, y1 = f.getbbox(text)
        if x1 - x0 <= width or size <= 8:
            im = Image.new("L", (x1 - x0, y1 - y0))
            ImageDraw.Draw(im).text((-x0, -y0), text, font=f, fill=255)
            return im
        size -= 1


def kred(b, texts):
    px = kred_pixels(b)
    W, H = len(px[0]), len(px)
    bs = bands(px)
    assert len(bs) == len(texts), (len(bs), texts)
    for (y0, bh), text in zip(bs, texts):
        if text is None:
            continue
        for y in range(max(0, y0 - 1), min(H, y0 + bh + 1)):
            px[y] = [0] * W
        im = draw_text(text, 13 if bh <= 13 else 20, W - 6)
        ox, oy = (W - im.width) // 2, y0 + (bh - im.height) // 2
        g = im.load()
        for y in range(im.height):
            for x in range(im.width):
                v = g[x, y]
                if v >= 48 and 0 <= oy + y < H:
                    px[oy + y][ox + x] = min(15, 2 + round(v * 13 / 255))
        for y in range(max(0, oy - 1), min(H, oy + im.height + 1)):   # 1 px outline, 8-neighbour
            for x in range(max(0, ox - 1), min(W, ox + im.width + 1)):
                if px[y][x] == 0 and any(px[yy][xx] >= 2 for yy in range(max(0, y - 1), min(H, y + 2))
                                         for xx in range(max(0, x - 1), min(W, x + 2))):
                    px[y][x] = 1
    return kred_bytes(b, px)


# ------------------------------------------------------------------ WIN02 (4bpp, 8x8 tiles, map)

def glyph(font, ch):
    """(columns, width) of a half-width glyph, trimmed to its ink; space = 3 px."""
    rows = fnt.ascii_rows(font, ord(ch))
    used = [x for x in range(8) if any(r[x] for r in rows)]
    if not used:
        return rows, 0, 3
    return rows, used[0], used[-1] - used[0] + 1


def text_width(font, s):
    return sum(glyph(font, c)[2] + 1 for c in s) - 1


def win02(b, font):
    h = pad.pad_info(b)
    cols, rows = h["cols"], h["rows"]
    W, H = cols * 8, rows * 8
    mp = list(struct.unpack_from(f"<{h['cells']}H", b, h["map"]))
    tiles = [b[h["data"] + 32 * i:h["data"] + 32 * (i + 1)] for i in range(h["tiles"])]
    px = [[-1] * W for _ in range(H)]   # -1 = map 0 (transparent cell)
    for c, m in enumerate(mp):
        if m:
            t = tiles[m - 1]
            for p in range(64):
                px[c // cols * 8 + p // 8][c % cols * 8 + p % 8] = (t[p // 2] >> (4 * (p & 1))) & 15
    for i, (s, lw) in enumerate(zip(SAVE_LINES, SAVE_WIDTH)):
        assert text_width(font, s) <= lw, (s, text_width(font, s), lw)
        y0 = 16 + 16 * i
        for y in range(y0, y0 + 16):
            px[y][:lw] = [0] * lw
        x = 0
        for word in s.split(" "):      # each word starts on a tile column: repeated words share their tiles
            x = -(-x // 8) * 8
            for ch in word:
                g, first, w = glyph(font, ch)
                for gy in range(12):
                    for gx in range(w):
                        v = g[gy][first + gx]
                        if v:
                            px[y0 + 2 + gy][x + gx] = 1 if v == fnt.INK else 4
                x += w + 1
            x += 3                     # >= 4 px between words
        assert x - 4 <= lw, (s, x, lw)
    # re-tile: cells that were map 0 and stayed empty keep 0; equal tiles are shared
    new_tiles, index, new_map = [], {}, []
    for c in range(cols * rows):
        cx, cy = c % cols * 8, c // cols * 8
        cell = [px[cy + p // 8][cx + p % 8] for p in range(64)]
        if all(v == -1 for v in cell):
            new_map.append(0)
            continue
        cell = [max(v, 0) for v in cell]
        raw = bytes(cell[2 * k] | cell[2 * k + 1] << 4 for k in range(32))
        if raw not in index:
            index[raw] = len(new_tiles) + 1
            new_tiles.append(raw)
        new_map.append(index[raw])
    out = bytearray(b[:h["data"]])
    struct.pack_into(f"<{len(new_map)}H", out, h["map"], *new_map)
    struct.pack_into("<H", out, 0x12, len(new_tiles))
    # the game loads WIN02 at boot into a buffer of its own size: 146 tiles (VWF, no sharing) froze the boot
    assert len(new_tiles) <= h["tiles"], f"WIN02 needs {len(new_tiles)} tiles > {h['tiles']}"
    return bytes(out) + b"".join(new_tiles)


def apply(name, blob, font):
    """SYS.MPS entry -> redrawn bytes (unchanged for entries not redrawn). font = original SYSTEM.FNT bytes."""
    stem = name.split(".")[0]
    if stem in CREDITS:
        return kred(blob, CREDITS[stem])
    if stem == "WIN02":
        return win02(blob, font)
    return blob


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        sysdir = ROOT / "work" / "orig" / "mps" / "SYS"
        font = fnt.patch_ascii((sysdir / "SYSTEM.FNT").read_bytes())[0]
        pairs = []
        for n in ["WIN02"] + sorted(CREDITS):
            b = (sysdir / f"{n}.PAD").read_bytes()
            pairs.append((pad.render(b), pad.render(apply(n + ".PAD", b, font))))
        Wd = max(a.width + c.width + 8 for a, c in pairs)
        Ht = sum(a.height + 4 for a, _ in pairs)
        sheet = Image.new("RGBA", (Wd, Ht), (90, 90, 90, 255))
        y = 0
        for a, c in pairs:
            sheet.paste(a, (0, y), a)
            sheet.paste(c, (a.width + 8, y), c)
            y += a.height + 4
        sheet.resize((Wd * 2, Ht * 2), Image.NEAREST).save(sys.argv[2])
        print(sys.argv[2])
