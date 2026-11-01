; menus.asm: wider menu windows for English labels (data/windows.json menu_label / battle_command; D4).
;   armips tools/asm/menus.asm -strequ EXE <tree>/SLPS_010.30      (tools/build.py does this)
;
; A menu is built by 0x80053744(id, &menu, w, h): w/h in 8 px units (the a2/a3 immediates below); the menu
; struct holds x, y, columns, rows, a label table {char *text; u16 x, y, 0x0f/0x0e; u16 0} (12-byte entries,
; column-major) and a cursor-rect table {s16 x, y, w, h} (8-byte entries), both relative to the window.

.psx
.open EXE, 0x8000F800

; Field main menu (x 16): 2 columns x 3 rows. JP: labels at x 8 / 48, 24 px each, window 10 units.
; English: Status Items Equip (6 chars) | Magic Settings Save (8 chars): columns at x 8 / 64, window 17 units.
.org 0x800564b0
  addiu a2, zero, 17
.org 0x80080384 + 4                 ; column 2 labels: x
  .halfword 0x40
.org 0x80080390 + 4
  .halfword 0x40
.org 0x8008039c + 4
  .halfword 0x40
.org 0x800803b4                     ; cursor rects: column 1 x 6 w 52, column 2 x 62 w 68
  .halfword 6, 3, 52, 14,  6, 17, 52, 14,  6, 31, 52, 14
  .halfword 62, 3, 68, 14,  62, 17, 68, 14,  62, 31, 68, 14

; Battle command column (right edge 296, JP x 256, 5 units, labels at x 8): labels of up to 5 chars
; (script/exe.json 78fbc-78fec), 6 units from x 248 - left of that is the status box (to x 246).
.org 0x8005c8f8
  addiu v0, zero, 248
.org 0x8005c9b0                     ; 8 units (to x 312): its name tab takes the menu width, "Shinobu" needs 64
  addiu a2, zero, 8
.org 0x80080f8c + 4                 ; labels x 8 -> 6 (6 entries, 12 bytes apart)
  .halfword 6
.org 0x80080f98 + 4
  .halfword 6
.org 0x80080fa4 + 4
  .halfword 6
.org 0x80080fb0 + 4
  .halfword 6
.org 0x80080fbc + 4
  .halfword 6
.org 0x80080fc8 + 4
  .halfword 6
.org 0x80080fe0                     ; cursor rects: x 4 w 44
  .halfword 4, 6, 44, 14,  4, 20, 44, 14,  4, 34, 44, 14,  4, 48, 44, 14,  4, 63, 44, 14,  4, 77, 44, 14

; Battle name tab (0x8005c708): status window 6 at rect 0x80080dfc {x, y, w, h}, then a tab at x = w + 2 drawn
; by 0x80050f10(.., a3 = width 7 units) holding label 0x80080e0c, whose x the code sets to w + 6 * (i + 1).
; English: tab 8 units (to x 312, over the 8-unit command column), name at w + 4 ("Shinobu" = 56 px).
.org 0x8005c75c
  addiu v1, zero, 4
  nop
  nop
.org 0x8005c7c0
  addiu a3, zero, 8
; Status box names (label lists 0x80080e48 one member, 0x80080ea8 two): x 50 / 129 held 3 SJIS chars (36 px);
; 7 ASCII chars end inside the frame from x 42 / 122.
.org 0x80080e48 + 4
  .halfword 42
.org 0x80080ea8 + 4
  .halfword 42
.org 0x80080efc + 4
  .halfword 122

; Sub-menu title tab (Status / Items / Equip / Magic): window 0x800544b8(3, &text, text x 8, text y 6) with
; colour, x 16, y 20, w 40, h 24 on the stack. English up to 6 chars: w 56 (frame drawn ~5 px inside, so it
; ends where the item list's frame starts, x 68), text x 4.
.org 0x80055ccc
  addiu v0, zero, 56
.org 0x80055ce4
  addiu a2, zero, 4

; Field status box ST value: Normal (JP x 40) / Poison (JP x 46), 6 chars from x 28 end inside the frame.
.org 0x800803e4 + 4
  .halfword 0x1c
.org 0x800803f0 + 4
  .halfword 0x1c

; Shop: Buy / Sell (x 16, 5 units -> 6), cursor w 28 -> 36.
.org 0x8005dd2c
  addiu a2, zero, 6
.org 0x8008103c
  .halfword 6, 2, 36, 14,  6, 16, 36, 14

; Shop: Buy / Don't buy, Sell / Don't sell (x 64, 8 units -> 12), cursor w 52 -> 84.
.org 0x8005e0c4
  addiu a2, zero, 12
.org 0x800810e4
  .halfword 6, 6, 84, 14,  6, 20, 84, 14

.close
