# Font

## SYS.MPS/SYSTEM.FNT (94,032 bytes), loaded at RAM 0x80150000  **verified**
Header: u32 0x10, u32 0x2410, u32 0x3150, u32 0x069e. The loader (`0x80053e7c`) reads the first 14 bytes and
stores `count = 0x686` (1670) **hard-coded**; the header's 0x69e (1694) is the number of glyph slots, the last 24
code entries are zero.

| offset | contents |
|---|---|
| 0x0000 | header (4 u32) |
| 0x0010 | **half-width table**: 256 entries of 36 bytes, indexed by the raw byte value (`code < 0x8000`) |
| 0x2410 | 1694 big-endian SJIS codes, sorted ascending (8141 8142 8145 ... e661), 24 trailing zeros |
| 0x3150 | glyph data for those codes: 48 bytes each, 1694 slots |

RAM pointers the loader stores: `0xe04($gp)` = base+0x10 (half-width), `0xdfc($gp)` = base+0x2410 (code list),
`0xdf4($gp)` = base+0x3150 (glyphs), `0xe14($gp)` = 0x686 (count). gp = 0x800882dc.

### Full-width (SJIS) glyph: 12 rows x 4 bytes, each row a base-6 number  **verified**
`0x80053f04` decodes one record: for each of the 12 rows it divides the u32 by 6^11, 6^10 ... 6^0 (constant
0x159fd800 = 6^11, stepped down by x*0xaaaaaaab>>2) and stores the 12 quotients as bytes: **12 pixels per row,
6 grey levels each (0-5)**, leftmost pixel = the highest power of 6. Only 48 of the 12x12 pixels are not used;
the record is a plain greyscale bitmap in base 6, which is why a 2 bpp or 1 bpp reading only ever produced noise.
`python -X utf8 tools/fnt.py sheet` renders these.

### Half-width glyph: 12 rows x 3 bytes, 8 px, 3 bits per pixel, MSB first  **verified**
`0x800540ac` reads a 24-bit little-endian row and places the 3-bit groups (bits 0-2, 3-5, 6-8, 9-11 from the
second half on) into 4-bit nibbles of a 12x12 4 bpp cell: 8 pixels of 8 grey levels in the left 8 columns, columns
8-11 stay 0. The group at bit 21 is the leftmost pixel.
Verified two ways: (1) the 4 bpp glyphs the renderer hands the GPU (`tools/debug/glyph_dump.lua` at 0x800506f0)
match this decode pixel for pixel; (2) the game draws "HP 192 / MP 225 / ST 通常", "30 G", "YES/NO", "PAGE 1/1"
with it.

Coverage (0x20-0x7e): every letter and digit is present and correct. Some punctuation is **blank** in the disc's
font (`" # $ % & ' * ; < > ^ _ ` { | } ~` and `@`, `[`, `]` are drawn as bars or empty), so English that needs
them must add glyphs. `tools/fnt.py ascii-write FILE "charmap"` writes a glyph (or the whole printable set) into
the half-width table; the encoder asserts the 8 px cell.

## Rendering
Two renderers, and they do **not** agree on ASCII:

- **Field / message / menu text** (`0x80051904` layout, `0x80050508` per glyph, both verified by hooking the
  menu: codes 0x0033 '3', 0x0047 'G' and 0x8356 'シ' all pass through it). Bytes < 0x80 are drawn from the
  half-width table at **8 px per character**; a SJIS pair is 12 px. Escapes (`\n` = y+14, `\f` = end of page,
  `\h`, `\i<x>`, `\x<x>`, `\u<x>`) are handled here, and a double ASCII space becomes a full-width space
  (`0x80055698`). **English therefore needs no engine patch on this path.**
- **VIS/MES captions** (`0x8005fd3c` parser, `0x8005f684` per glyph): 0x0d = line break, 0x20 = a small space,
  and every other byte is taken as a SJIS lead byte (`code = byte<<8 | next`), so **ASCII letters are drawn as
  nothing and eat the following byte**. This path needs a code hook (treat byte < 0x80 as `0x8005f684(byte)` and
  advance 8 px) before VIS captions can be English; until then MES text must stay in the full-width font.
  The marker build shows this plainly: VIS scenes come out blank (`work/qa/mk_vis/`).

## Glyph cache and VRAM
`0x80050508` keeps a bitmap of used cells at `0x800890a0`, a VRAM cursor at `0x80088c6c` and a 0x1b8 (440) cell
area; a glyph is decoded into a 12x12 4 bpp buffer and uploaded when first used. So the font file is only read
for glyphs that are not in VRAM yet; a VIS scene loads its MES text to 0x80158000, which **overlaps the glyph
data** of SYSTEM.FNT (0x80153150-0x80166f50) - that is safe only because those glyphs are already uploaded.

## Window text metrics (phase 5 width gate, measured)
Standard message window (`inn` greeting, `work/qa/one/f001300.png`): **28 half-width characters per line** at
8 px, 4 lines per page, and the renderer **wraps by itself** - a 36-character line broke after "…01" and put
"23456789" on the next line, nothing clipped. Still to measure with `tools/debug/texttest.py`: the choice window,
the item description box, the shop list and the place-name banners.

## SYS.MPS/DBUGFON.TIM
TIM (4bpp, CLUT) debug font, 0x840 bytes. No user found in phases 1-5.
