"""boxes.py: find the yellow-framed windows in a shot and the text extent inside each (width gate, phase 5).

    python -X utf8 tools/debug/boxes.py SHOT.png [SHOT.png ...]

Prints each window as x0..x1 y0..y1 (frame pixels) and the columns where light text pixels start/end inside it,
so a budget is (x1 - text_x0) // 8 half-width characters. Field/menu screens are 320x240.
"""
import sys

from PIL import Image


def yellow(p):
    r, g, b = p[:3]
    return r > 190 and g > 120 and r - b > 80       # frame colours (255,255,156) and (205,139,0)


def boxes(im):
    w, h = im.size
    px = im.load()
    rows = {}
    for y in range(h):          # horizontal yellow runs >= 16 px are frame edges
        x = 0
        while x < w:
            if yellow(px[x, y]):
                s = x
                while x < w and yellow(px[x, y]):
                    x += 1
                if x - s >= 16:
                    rows.setdefault((s, x - 1), []).append(y)
            else:
                x += 1
    out = []
    for (x0, x1), ys in rows.items():
        ys.sort()
        if len(ys) >= 2 and ys[-1] - ys[0] >= 10:
            out.append((x0, x1, ys[0], ys[-1]))
    return out


def text_extent(im, box):
    x0, x1, y0, y1 = box
    px = im.load()
    cols = [x for x in range(x0 + 3, x1 - 2)
            if any(sum(px[x, y][:3]) > 450 and not yellow(px[x, y]) for y in range(y0 + 3, y1 - 2))]
    return (cols[0], cols[-1]) if cols else None


if __name__ == "__main__":
    for path in sys.argv[1:]:
        im = Image.open(path).convert("RGB")
        print(path, im.size)
        for b in sorted(boxes(im)):
            t = text_extent(im, b)
            print(f"  box x {b[0]}..{b[1]} y {b[2]}..{b[3]}  inner {b[1] - b[0] - 5} px  text {t}")
