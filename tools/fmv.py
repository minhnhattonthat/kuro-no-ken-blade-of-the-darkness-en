"""fmv.py: the boot prologue text in BOD.STR (docs/re/graphics.md G4), redrawn in English.

    python -X utf8 tools/fmv.py preview OUT.png   # the peak frame of each page, JP | EN
    python -X utf8 tools/fmv.py build             # -> work/fmv/BOD_en.STR (cached; build.py calls apply())

BOD.STR: 320x240 MDEC video, 1369 frames, over a static red gradient. Four text pages, white 16 px gothic with a
1 px black outline, 15 rows tall at an 18 px pitch, each line centred and fading in on its own. Per page, every
frame gets the Japanese erased (the peak frame's glyphs, dilated over the outline, filled from the static plate =
median of text-free frames) and the English line drawn with the alpha its Japanese line has in that frame. jPSXdec
`-replaceframes` with <partial-replace> re-encodes only the changed macroblocks, so the file keeps its sectors.
Needs Java 8+ and jPSXdec 2.1 in tools/jpsxdec/ (docs/re/README.md).
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "tools" / "jpsxdec" / "jpsxdec.jar"
SRC = ROOT / "work" / "orig" / "tree" / "BOD.STR"
WORK = ROOT / "work" / "fmv"
FRAMES = WORK / "bod"                     # decoded original frames, BOD.STR[0][NNNN].png
OUT = WORK / "BOD_en.STR"
FONT = ROOT / "fonts" / "LiberationSans-Regular.ttf"
SIZE = 15
PLATE = [*range(176, 190), *range(562, 578), *range(713, 732)]   # frames with no text (faint fades included)

# (first frame, last frame, top row of line 1, English lines; one per Japanese line, same order)
PAGES = [
    (20, 174, 94, [                     # はるか昔 / その漆黒の竜は多くの国を焼きつくし / 幾千もの人の肉を喰らった
        "Long, long ago,",
        "that jet-black dragon burned many lands to ash",
        "and devoured the flesh of thousands.",
    ]),
    (191, 560, 67, [                    # 比類なき腕を誇った勇者の剣も / 偉大なる魔導師の天地を揺るがす魔法も /
        "Not the swords of heroes of matchless skill,",          # 聖なる神の力を具現する高僧の祈りも /
        "not the earth-shaking magic of great sorcerers,",        # 彼の者には通用せず /
        "not the high priests' prayers of divine might:",         # 追い詰められた人々は、ついに魔を以て、 /
        "nothing could prevail against it.",                       # これを打ち倒さんとした
        "Cornered at last, the people resolved",
        "to strike it down with the demonic.",
    ]),
    (579, 711, 103, [                   # 滅ぼせぬもの無き武器を / この世のものにあらざる武器を
        "A weapon that could destroy anything...",
        "a weapon not of this world...",
    ]),
    (733, 871, 103, [                   # ・・・そして / 一振の剣が造られたのである
        "...And so,",
        "a single sword was forged.",
    ]),
]
PITCH, ROWS = 18, 15


def frame(i):
    return np.asarray(Image.open(FRAMES / f"BOD.STR[0][{i:04d}].png").convert("RGB")).astype(np.float32)


def bright(px):
    return (px[..., 1] > 100) & (px[..., 2] > 100)          # white text; the gradient and embers are red/orange


def jpsxdec(*args):
    subprocess.run(["java", "-jar", str(JAR), *map(str, args)], check=True, cwd=WORK, stdout=subprocess.DEVNULL)


def decode():
    """The original frames as PNG (once)."""
    if (FRAMES / "BOD.STR[0][1368].png").is_file():
        return
    WORK.mkdir(parents=True, exist_ok=True)
    jpsxdec("-f", SRC, "-x", WORK / "bod.idx")
    jpsxdec("-x", WORK / "bod.idx", "-i", 0, "-dir", FRAMES, "-vf", "png", "-noaud")


def line_image(text, font):
    """RGBA strip 320 x (ROWS + 6): the line centred, white with a 1 px black outline like the original."""
    im = Image.new("RGBA", (320, ROWS + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=font)
    assert w <= 312, (text, w)                               # the widest Japanese line spans x 10..309
    d.text((160 - w / 2, (ROWS + 6) / 2), text, font=font, fill=(255, 255, 255, 255), anchor="lm",
           stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return np.asarray(im).astype(np.float32) / 255


def render():
    """{frame index: (English frame as uint8 array, rect x,y,w,h)} for every frame of every page."""
    decode()
    plate = np.median(np.stack([frame(i) for i in PLATE]), 0)
    font = ImageFont.truetype(str(FONT), SIZE)
    out = {}
    for first, last, top, lines in PAGES:
        peak_i = max(range(first, last + 1, 2), key=lambda i: bright(frame(i)).sum())
        peak = frame(peak_i)
        glyph, erase = [], np.zeros((240, 320), bool)
        for n in range(len(lines)):
            m = np.zeros((240, 320), bool)
            y = top + PITCH * n
            m[y - 1:y + ROWS + 1] = bright(peak)[y - 1:y + ROWS + 1]
            assert m.sum() > 40, (first, n)                  # a Japanese line is there
            glyph.append(m)
            xs = np.where(m.any(0))[0]
            erase[y - 3:y + ROWS + 3, xs.min() - 4:xs.max() + 5] = True   # the whole line: MDEC rings past the outline
        strips = [line_image(t, font) for t in lines]
        ref = [peak[..., 1][m].mean() for m in glyph]
        ys = np.where(erase.any(1))[0]
        y0 = ys.min() & ~15                                  # whole macroblock rows, full width (English is wider)
        rect = (0, y0, 320, ((ys.max() + 3 | 15) + 1) - y0)
        bgrows = ~erase.any(1)[:, None] & (plate[..., 0] > 20)  # background rows, for the frame's brightness
        for i in range(first, last + 1):
            src = frame(i)
            px = src.copy()
            k = np.median(src[..., 0][bgrows] / plate[..., 0][bgrows])  # page 1 still brightens (0.9 -> 1.0)
            px[erase] = plate[erase] * k
            for n, (m, s) in enumerate(zip(glyph, strips)):
                bg = plate[..., 1][m].mean()
                alpha = float(np.clip((src[..., 1][m].mean() - bg) / (ref[n] - bg), 0, 1))
                if alpha < 0.02:
                    continue
                y = top + PITCH * n - 3
                a = s[..., 3:] * alpha
                px[y:y + ROWS + 6] = px[y:y + ROWS + 6] * (1 - a) + s[..., :3] * 255 * a
            out[i] = (np.clip(px + 0.5, 0, 255).astype(np.uint8), rect)
    return out


def key():
    return hashlib.sha1(Path(__file__).read_bytes() + FONT.read_bytes()).hexdigest()


def build():
    """work/fmv/BOD_en.STR: a copy of the original with every page frame partially replaced (cached on key())."""
    stamp = OUT.with_suffix(".key")
    if OUT.is_file() and stamp.is_file() and stamp.read_text() == key():
        return OUT
    frames = render()
    edit = WORK / "bod_en"
    shutil.rmtree(edit, ignore_errors=True)
    edit.mkdir(parents=True)
    xml = ['<?xml version="1.0"?>', '<str-replace version="0.3">']
    for i, (px, (x, y, w, h)) in frames.items():
        Image.fromarray(px).save(edit / f"{i:04d}.png")
        xml.append(f'<partial-replace frame="{i}" tolerance="4" rect="{x},{y},{w},{h}">bod_en/{i:04d}.png</partial-replace>')
    xml.append("</str-replace>")
    (WORK / "bod_en.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    tmp = WORK / "BOD_tmp.STR"
    shutil.copyfile(SRC, tmp)
    jpsxdec("-f", tmp, "-x", WORK / "bod_tmp.idx")
    jpsxdec("-x", WORK / "bod_tmp.idx", "-i", 0, "-replaceframes", WORK / "bod_en.xml")
    assert tmp.stat().st_size == SRC.stat().st_size
    tmp.replace(OUT)
    stamp.write_text(key())
    return OUT


def apply(tree):
    shutil.copyfile(build(), Path(tree) / "BOD.STR")


def preview(path):
    frames = render()
    peaks = [max(range(f, l + 1, 2), key=lambda i: bright(frame(i)).sum()) for f, l, _, _ in PAGES]
    sheet = Image.new("RGB", (640, 240 * len(peaks)))
    for r, i in enumerate(peaks):
        sheet.paste(Image.open(FRAMES / f"BOD.STR[0][{i:04d}].png").convert("RGB"), (0, 240 * r))
        sheet.paste(Image.fromarray(frames[i][0]), (320, 240 * r))
    sheet.save(path)


if __name__ == "__main__":
    if sys.argv[1:2] == ["preview"]:
        preview(sys.argv[2])
    elif sys.argv[1:2] == ["build"]:
        print(build())
    else:
        sys.exit(__doc__)
