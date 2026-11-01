# Font

## SYS.MPS/SYSTEM.FNT (94,032 bytes) - the dialogue/menu font
- Header: u32 0x10, u32 0x2410, u32 0x3150, u32 0x069e (= 1694 glyphs). **verified** (structure).
- 0x10-0x2410: 0x2400-byte table, mostly zero (non-zero 0x4b8-0x2336). **guess:** SJIS -> glyph lookup.
- 0x2410: 1694 big-endian SJIS codes, sorted (8141 8142 8145 ...). **verified.** Full-width only, **no ASCII**:
  the font holds only the characters the script uses.
- 0x3150-end: glyph data, ~48 bytes per glyph (81,408 / 1694). Format **not decoded**: 12 rows of 32 bits fit
  (glyph 1 = 。 shows as a 6x4 ring in the low bits) but the rest of each row is not a plain bitmap (2 planes or
  antialias bits, guess). `tools/fnt.py` is a first attempt (wrong for this layout).
- On screen (640x480 interlaced): 12x12 glyphs, grey antialiased, ~13 px advance (zoomed shot
  `work/qa/recon1/f010800.png`).
- Phase 5 plan: trace the draw call from op 0x3b (0x80055698) to the glyph blit, decode the format from the code,
  then choose: half-width/VWF ASCII glyphs added to the code list, or a renderer hook.

## SYS.MPS/DBUGFON.TIM
TIM (4bpp, CLUT) debug font, 0x840 bytes. Debug menu leftover? Look for its users in phase 2.
