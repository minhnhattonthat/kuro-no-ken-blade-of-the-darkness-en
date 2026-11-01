# Graphics

## PAD30 tiled image - verified (every PAD in the disc renders; `tests/test_archives.py`)
`tools/pad.py render|sweep`. `"PAD30"`, 0x30-byte header: +0x08 u32 tile-map offset (0 = none), +0x0c u32 tile
data offset, +0x10 u16 map cells, +0x12 u16 unique tiles, +0x14 u16 palette size /16, +0x16 cols, +0x18 rows,
+0x1a flags (low byte = tile px 8/16; 0x1000 = 4bpp else 8bpp). Palette RGB555 at 0x30. Map: u16 per cell,
0 = blank, n = tile n-1. Used by .PAD .CG .KAO and inside EM containers (.PAD/.PAO).

## Static sweep (2026-11-01)
`python tools/pad.py sweep work/orig/mps work/orig/gfx`: 472 images, 0 render errors. Skipped (no PAD30): BSX (274
data files), OTO (sound), SCN/MES/SMX (text), FNT/CLT/BIN/TIM (font, palettes, data), BEP/YSK2BG.BG (unknown
format, 1 file: check in phase 5). Sheets read by the controller in `work/qa/gfx/*.png`.

## Japanese drawn as graphics (to translate, D5)
| # | Element | Source | Notes |
|---|---|---|---|
| G1 | Staff credits (cast + staff, 16 cards) | SYS.MPS `KRED00-15.PAD` (8bpp 16x16 tiles, own palette) | JP names + role labels; KRED13 "SPECIAL THANKS..." already English, KRED15 "STAFF" English. Credits English per D3. **Done** (`tools/gfx.py`, D13); not yet seen in-game: the ending warp shows its backdrops as tile garbage and no cards |
| G2 | Save/load prompts: セーブするファイルをえらんでください, ロードする..., あたらしくセーブデータをつくる, セーブするスロット..., ロードするスロット... | SYS.MPS `WIN02.PAD` (4bpp) | save/load screen. **Done**, English in-game (scenes `save_slot`, `load_slot`); must stay <= 120 tiles (loaded at boot into a buffer of its size) |
| G3 | Title logo 黒の剣 | VIS.MPS `TITLES.CG` | menu NEW GAME/LOAD GAME/OPTION already English; logo kept unless an official English logo exists (D5) |
| G4 | Boot prologue text on red | guess LOGO.STR FMV (`docs/re/text.md`) | needs STR decode + re-encode if video |
| G5 | Small paper talisman sprites (battle) | BCP `_KR_*` group | marks too small to read at sheet scale; zoom check in phase 5 |

Already English: END.PAD ("END"), NL_.PAD ("Now Loading"), title menu, CD BROS. logo. No text seen in KAO (faces),
BP (battle backgrounds), BEP (map tilesets, checked at 1/3 scale: re-check signs zoomed in the phase 8 tour),
CP (field sprites), VIS CG pictures, BCP effects/monsters, COMMON.BCP (digits 0-9 only).

Tour-only screens still to visit with the debug tool (phase 2+): menus, battle UI, shop, game over, ending,
name/memory-card screens, location banners (font text, `\xNN`).
