; vis_ascii.asm: ASCII in VIS/MES captions (docs/re/font.md "Rendering").
;   armips tools/asm/vis_ascii.asm -strequ EXE <tree>/SLPS_010.30      (tools/build.py does this)
;
; The caption parser (0x8005fd3c) takes every byte that is not 00/0d/20/81 40/'c' as a SJIS lead byte and draws
; it with the BIOS kanji font (Krom2RawAdd, 16x15 1bpp, 2 columns of 8 px, MSB = leftmost pixel). This rewrites the parser's tail
; (the 'c' colour escape - no MES file uses it - and the SJIS branch, 0x8005ffc8-0x80060123, entered only at
; its start) so that a byte < 0x80 is one glyph of one column (8 px), and hooks the font call in the glyph
; builder 0x8005f684 so that codes < 0x80 come from SYSTEM.FNT's half-width table (gp+0xe04, resident in RAM
; in every scene, VIS included), converted to the 1bpp 16x15 layout Krom2RawAdd returns.
; Verified in-game: work/qa/vis_ascii (cold boot, warp vis_00, --qa stress lines).

.psx
.open EXE, 0x8000F800

KROM2RAWADD equ (0x80067f38)
GLYPH       equ (0x8005f684)     ; a0 = code -> v0 = 4bpp cell buffer or 0
CELLPOS     equ (0x8005fcbc)     ; a0 = &xy
DRAW        equ (0x80044a00)     ; a0 x, a1 y, a2 buffer
PARSE_NEXT  equ (0x8005fe54)
GLYPHBUF    equ (0x80156800)     ; GLYPH clears and reuses it only after reading the font bitmap
ROW0        equ (2)              ; first of the 12 half-width rows inside the 15-row cell

.org 0x8005f6ac
  jal   ascii_glyph

.org 0x8005ffc8
  lhu   v0, 0x14(fp)            ; this byte
  nop
  sltiu v1, v0, 0x80
  bnez  v1, @@glyph
  move  a0, v0                  ; ASCII: the code is the byte
  lui   v1, 0x8009              ; SJIS: code = byte << 8 | next byte (as the game did)
  lw    v1, -0x72bc(v1)
  sll   v0, v0, 8
  lbu   a0, 0(v1)
  addiu v1, v1, 1
  lui   at, 0x8009
  sw    v1, -0x72bc(at)
  or    a0, v0, a0
  sh    a0, 0x14(fp)
@@glyph:
  jal   GLYPH
  nop
  beqz  v0, @@advance
  sw    v0, 0x10(fp)
  jal   CELLPOS
  addiu a0, fp, 0x18
  lh    a0, 0x18(fp)
  lh    a1, 0x1a(fp)
  lw    a2, 0x10(fp)
  jal   DRAW
  nop
@@advance:
  lhu   v1, 0x14(fp)
  lui   v0, 0x8009
  sltiu v1, v1, 0x80            ; ASCII advances 1 column, SJIS 2
  lhu   a0, -0x70cc(v0)         ; column
  lhu   a1, -0x72b4(v0)         ; per-glyph delay
  addiu a0, a0, 2
  subu  a0, a0, v1
  sh    a0, -0x70cc(v0)
  j     PARSE_NEXT
  sh    a1, -0x72ac(v0)

; a0 = code. code >= 0x80: the BIOS font. Else build a Krom2RawAdd-style bitmap (15 rows x 2 bytes, MSB = left)
; from the half-width glyph (12 rows x 3 bytes, 8 px x 3 bits, pixel x in bits 3x..3x+2): lit = value != 0
; (the font draws each stroke as a 5 + 1 pixel pair).
ascii_glyph:
  sltiu t0, a0, 0x80
  beqz  t0, @@krom
  lui   v0, GLYPHBUF >> 16
  ori   v0, v0, GLYPHBUF & 0xffff
  addiu t1, v0, 32
@@clear:
  addiu t1, t1, -4
  bne   t1, v0, @@clear
  sw    zero, 0(t1)
  lw    t1, 0xe04(gp)           ; half-width table
  sll   t0, a0, 3
  addu  t0, t0, a0
  sll   t0, t0, 2               ; code * 36
  addu  t1, t1, t0
  addiu t2, v0, ROW0 * 2
  li    t3, 12
@@row:
  lbu   t4, 0(t1)
  lbu   t5, 1(t1)
  lbu   t6, 2(t1)
  sll   t5, t5, 8
  or    t4, t4, t5
  sll   t6, t6, 16
  or    t4, t4, t6
  move  t5, zero
  li    t6, 8
@@pixel:
  andi  t7, t4, 7               ; pixel 0 (leftmost) first: shifted up 7 times it ends in bit 7
  sltu  t7, zero, t7
  sll   t5, t5, 1
  or    t5, t5, t7
  addiu t6, t6, -1
  bnez  t6, @@pixel
  srl   t4, t4, 3
  sb    t5, 0(t2)
  addiu t1, t1, 3
  addiu t3, t3, -1
  bnez  t3, @@row
  addiu t2, t2, 2
  jr    ra
  nop
@@krom:
  j     KROM2RAWADD
  nop

.if org() > 0x80060124
  .error "vis_ascii: parser tail overflows into 0x80060124"
.endif

.close
