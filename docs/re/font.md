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

### Half-width glyph: 12 rows x 3 bytes, 8 px, 3 bits per pixel, leftmost pixel in the low bits  **verified**
`0x800540ac` reads a 24-bit little-endian row and places the 3-bit groups (bits 0-2, 3-5, 6-8, 9-11 from the
second half on) into 4-bit nibbles of a 12x12 4 bpp cell: 8 pixels of 8 grey levels in the left 8 columns, columns
8-11 stay 0. **Pixel x = bits 3x..3x+2** (bits 0-2 = leftmost; 4 bpp puts the low nibble on the left). Phase 5
first read it MSB-first, which dumps `(` as `)` and `?` mirrored; glyphs written that way came out mirrored in
the VIS test (`work/qa/vis_ascii`), fixed 2026-11-02. The disc draws strokes 2 px wide as value 5 + value 1
pairs (`!` = `...15...`); values used: 0, 1, 3, 5.
Verified two ways: (1) the 4 bpp glyphs the renderer hands the GPU (`tools/debug/glyph_dump.lua` at 0x800506f0)
match this decode pixel for pixel; (2) the game draws "HP 192 / MP 225 / ST 通常", "30 G", "YES/NO", "PAGE 1/1"
with it.

Coverage (0x20-0x7e): every letter and digit is present and correct. Blank in the disc's font:
`. , ' " ; * # $ % & < > @ \ ^ _ ` { | } ~` (period and comma too); `[` `]` are plain bars. The build fills the
blanks (`fnt.patch_ascii`, patterns in `tools/fnt.py`, 5 + shade-1 style like the disc's) in
`SYS.MPS/SYSTEM.FNT`; both renderers read them from there.

## Rendering
Two renderers, and they do **not** agree on ASCII:

- **Field / message / menu text** (`0x80051904` layout, `0x80050508` per glyph, both verified by hooking the
  menu: codes 0x0033 '3', 0x0047 'G' and 0x8356 'シ' all pass through it). Bytes < 0x80 are drawn from the
  half-width table at **8 px per character**; a SJIS pair is 12 px. Escapes (`\n` = y+14, `\f` = end of page,
  `\h`, `\i<x>`, `\x<x>`, `\u<x>`) are handled here, and a double ASCII space becomes a full-width space
  (`0x80055698`). **English therefore needs no engine patch on this path.**
- **VIS/MES captions** (`0x8005fd3c` parser, `0x8005f684` per glyph): **a different font - the BIOS kanji ROM**
  (`0x80067f38` = Krom2RawAdd, B0:51; 16x15 1bpp, 2 bytes per row, MSB = left). The glyph is ORed (with a
  1 px right spread, then an outline) into two 1bpp line bitmaps at `0x80156000` / `0x80156400`, 0x40 bytes
  (64 columns of 8 px) per row, column counter u16 `0x80088f34`; `0x8005f684` converts 3 columns to a 4 bpp
  cell at `0x80156800` and `0x80044a00` uploads it at VRAM x = col*2+0x380, y = line*16+0x190. Bytes: 00 end,
  0d line break, 20 = one empty column (8 px), 81 40 = two columns, `c<hex>` colour (unused by every MES), the
  rest SJIS (2 columns). VIS screens run at **640x480**, so a column is 8 of 640 px.
  **Hook (`tools/asm/vis_ascii.asm`, built in):** the parser's tail is rewritten so a byte < 0x80 is one glyph
  of one column, and the font call in `0x8005f684` goes to `ascii_glyph`, which turns the SYSTEM.FNT half-width
  glyph (gp+0xe04, resident in RAM in every scene - checked in 48 RAM dumps over 7 scenes, VIS included) into
  the Krom2RawAdd layout (12 rows at rows 2-13, lit = value != 0). Unit-tested under unicorn
  (`tests/test_asm.py`); in-game: `work/qa/vis_ascii/f005300.png` (cold boot, VIS00 intro, `build.py --qa`).
  **Packet budget (verified):** each glyph's upload (`0x80044a00`) takes 0xc0 bytes of the frame's GPU packet
  buffer (two 0x6000-byte buffers, `0x8004470c`; current pointer gp+0x97c, frame index gp+0x298). A page
  skipped with circle (delay 0) draws in one frame; JP pages peak ~124 glyphs (~0x5d00), English ~210 overran it
  and the field after VIS 0 froze without sprites. The hook defers the rest of the page to the next frame
  past 0x4000 bytes (`PKT_ROOM`). Bisected with `work/qa/bis_*` (VIS00:87 alone triggered it).
  **Width: 62 characters per caption line** (a 70-char ruler showed "...9012", columns 0-61; a glyph needs 3
  bitmap bytes). Japanese captions centre with leading full-width spaces and run up to ~62 columns; 2-5 lines.
  No auto-wrap: lines break only at `\n` (0x0d).

## Glyph cache and VRAM
`0x80050508` keeps a bitmap of used cells at `0x800890a0`, a VRAM cursor at `0x80088c6c` and a 0x1b8 (440) cell
area; a glyph is decoded into a 12x12 4 bpp buffer and uploaded when first used. So the font file is only read
for glyphs that are not in VRAM yet; a VIS scene loads its MES text to 0x80158000, which **overlaps the glyph
data** of SYSTEM.FNT (0x80153150-0x80166f50) - that is safe only because those glyphs are already uploaded.

## Window text metrics (phase 5 width gate, measured)
Budgets per window variant: **`data/windows.json`** (chars, lines, shot, and which windows need engine work).
How they were measured: `python -X utf8 tools/build.py --qa ID=TEXT [--data-runs]` puts a ruler or torture line
into one entry, `tools/debug/tour.py --only <scenes>` cold-boots the build and warps there, and
`tools/debug/boxes.py SHOT` prints each window frame and the text extent inside it.
- Field message box: 28 chars, 4 lines per page, auto-wrap, a 5th line pages; the page mark covers the 4th
  line's last cell (27 there). Torture line: every printable ASCII draws; `_ { } ~` are faint (unlikely in
  English). **`@` is a control code** in this renderer (`0x80051a58`: `@` + decimal = draw that raw glyph code,
  the number parsed by `0x800120f0`), so `@` in English must be written `@64`; the JP script never uses it.
- VIS caption: 62 chars per line, no wrap, up to 5 lines.
- Choice window: sized from the option's byte count at the JP 6 px per byte and right-anchored, so ASCII
  (8 px per byte) overflows by a quarter: needs an engine fix before choices are translated.
- Menus and the battle command column hold 3 half-width chars (2 kanji): English labels need wider windows.

## SYS.MPS/DBUGFON.TIM
TIM (4bpp, CLUT) debug font, 0x840 bytes. No user found in phases 1-5.
