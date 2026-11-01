# Disc and archives

## Disc
- One MODE2/2352 data track, no CDDA. 41 files (`work/orig/layout.xml` from `dumpsxiso -x tree -s layout.xml`).
- **verified:** `mkpsxiso -y layout.xml` on the unedited dump rebuilds a .bin with the pinned sha1
  (`c25cc539...`). Test: `tests/test_build.py` (repacks `work/orig/tree` with `tools/build.py`'s `repack`).
- Root: `SLPS_010.30` (EXE), `SYSTEM.CNF`, 10 `*.MPS` archives, `LOGO.STR` (logo FMV, 5 MB), `BOD.STR` (32 MB,
  opening/ending FMV, guess), `SAFETY.DAT` (50 MB filler), `XA/` (26 `*.XAT` + `XA.XAG` voice/music).
- File lookup: the EXE links `CdSearchFile` (strings at file 0x1b8c); names built as `\<NAME>.MPS;1`,
  `\XA\<name>.XAT/.XAG`, `LOGO.STR`, `BOD.STR`. XAT files (`XIMG` index) hold offsets relative to XA.XAG.
- **verified (2026-11-01): file growth / LBA shifts are safe.** SCN.MPS grown by 16 sectors (every later file
  +16 LBA, incl. XA, STR): `tools/debug/cd_seeks.lua` logged all 122 Setloc targets over 24000 frames of boot +
  intro on both discs; every one moved by exactly +16 (32 of them into XA.XAG, plus LOGO/BOD.STR), none stayed
  absolute. Warp tour on the shifted disc: see `docs/status.md`. The single read path is `pc=8006A780`.

## PSMG archive (`*.MPS`) - verified (`tests/test_archives.py`, all 10 repack byte-identical)
`tools/mps.py list|unpack`.
- Header: `"PSMG"`, u32 count, u32 data_start (0x800 or 0x1800), u32 0.
- count x 20-byte entries from 0x10: name[12] NUL-padded, u32 offset (from data_start), u32 size.
- Entries sector-aligned (0x800), zero gaps, in table order.

| Archive | Files | Content |
|---|---|---|
| SCN.MPS | 218 `*.SCN` | event/field scripts (bytecode + inline SJIS text), `docs/re/text.md` |
| SYS.MPS | 31 | `SYSTEM.FNT` font, `ITEM/KIES/SHINOBU.SMX` item/skill tables, `KRED00-15.PAD` credits, `END.PAD`, `NL_.PAD`, `WIN01/02.PAD`, `SYSTEM/SEPIA.CLT` palettes, `DBUGFON.TIM`, `_CK/_CS/_PK/_PS.BIN` |
| VIS.MPS | 38 `*.CG` + 23 `*.MES` | visual scenes: full-screen pictures + their text |
| KAO.MPS | 26 `*.KAO` | 64x64 face portraits (PAD30) |
| CP.MPS | 94 `*.CP` | field character sprites (EM: CEL + PAD) |
| BP.MPS | 18 `*.BP` | battle backgrounds (EM: ANM + PAD) |
| BEP.MPS | 59 `*.BEP` | field maps (EM: BOD + EVE + PAD tileset), `YSK2BG.BG` |
| BCP.MPS | 217 `*.BCP` | battle sprites/effects (EM: BCS CEL PAD/PAO OTO VH VB) |
| BSX.MPS | 274 `*.BSX` | battle data, one file per fight (`7f 'd\<name>'` in a field script), copied whole to 0x80099170 (slot 0x1400; a file starts `00000000 xxxx 3c00`). Battle talk = tagged records `01 'B' id5 00 <name>\n<text> 00` (literal `\n`/`\f` escapes), reached only by `03 01|02|03 <u16 file offset>` + one byte; extracted to `script/bsx/`, rewritten by `insert.bsx_insert`. The other SJIS runs are per-enemy AI action labels (剣で攻撃, 自爆《禁止》, 同カイエス, enemy spell lists: 1,983 runs, 124 distinct strings in 274 files) plus the `CB 90` fill of unused action records, which decodes as 斥 and is not text (the engine reads it as 4-byte records). None is displayed: proven 2026-11-02 with `tools/debug/slot_reads.lua` + `tools/debug/text_draws.lua` in a complete fight - the label bytes are never read (the fill past the data end is) and the text layout draws only its fixed 19-string UI set, nothing from the slot; left in Japanese (D14, `docs/re/scenes.md`) |
| OTO.MPS | 64 | `BGM*.BGM`, `*.SE` sound |

## EM container (`.CP .BP .BEP .BCP .SE`) - verified by rendering every PAD inside
`"EM"`, u16 count, then count x 12 bytes from offset 4: u32 offset, u32 size, char[4] ext (`.PAD .CEL .BOD ...`).
`tools/pad.py` `split_em`.

## SCN slack
Many `*.SCN` entries end with leftover bytes after the script (x86 code / old data from the PC-98 tools, e.g.
`02OLB00A.SCN` from 0xec). Not text; the extractor must stop at the script's real end (bytecode parse), never scan
to the entry size.
