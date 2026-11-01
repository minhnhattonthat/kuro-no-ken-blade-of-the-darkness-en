# Text engine

Encoding everywhere: **Shift-JIS** (cp932) full-width, NUL-terminated. Some EXE strings mix half-width ASCII
("pts の経験値を得た", "Gold を得た"). RAM = EXE file offset - 0x800 + 0x80010000.

`tools/sctext.py` is the codec (`decode`/`encode`, byte-exact: `tests/test_extract.py`), `tools/extract.py` dumps
every string to `script/**/*.json` and gates coverage, `tools/scn.py` is the SCN codec (walk, assemble, rebuild).

## 1. Scripts: SCN.MPS/*.SCN (bulk of the game: 11,100 strings, ~236 KB SJIS)  **verified**
Bytecode interpreted by the EXE; gcc -O0, easy to read. Slot bases: 0 (area dispatcher), 0x2000 (map script),
0x4000 (99CMN), 0x5000 (event script) - RAM = 0x80168000 + address (`docs/re/scenes.md`).
- Dispatch table at RAM 0x800100ac (file 0x8ac), extended interpreter at 0x8002ec48 with its own table.
- Operand readers (each advances the script pointer 0x80088fd4):
  - 0x8002bfdc u16; 0x8002c5a8 u8; 0x8002ebe8 u32.
  - 0x8002c194 "value": type byte; 0 -> u16 literal, 1 -> u16 variable index, else 0.
  - 0x8002c2ec "address": a value, converted by 0x8002bb14 to a script pointer (jump targets, handler tables).
  - 0x8002c60c "switch": var u16, value, u8 N, N x address.
  - 0x8002c33c "string": type byte **2** -> inline NUL-terminated SJIS (pointer returned); any other type ->
    **an address of a string in whichever script owns that slot** (an area script can point into 99CMN).
  - 0x8002c3fc = 0x8002c33c plus a `d\` prefix skip: if byte 1 of the string is 0x5c the caller gets the name
    after the two-character command (`d\blk1`, `d\_sho_va3.bca` = resource names, not text).
- 0x3b is the message op (7,300 on the walked path; 11,100 counting the blocks reached through 0x7b).
- **Reachability** (phase 4): 0x7b stores "spawn a thread at address" for the next yield, so its operand is a
  control-flow edge - that is where whole conversation blocks hang off (`5b`/`55` … `7b #5043`). Following it
  takes the walk from 8,580 to 11,141 strings; the rest is found by scanning the file for `3b 02 <text> 00`
  (2,536 sites) and, for text with no message op at all (choice options, sign/hint texts, place-name banners
  like `\x18港町オールバイン`), by scanning for kana runs. 15 % of SCN bytes (130 KB of 866 KB) are data the walk
  cannot reach: zero padding plus tables and records of script addresses (door/choice dispatch pairs
  `7b 00 <addr> 06 <addr>`); none of it is text - `python -X utf8 tools/extract.py gaps` prints the split. Those
  tables are **not** relocated by `rebuild()` yet (it patches only u16s that match a moved op), so phase 7 has to
  add their form before a message in front of one grows.
- `tests/test_scn.py` tolerates two ops 0x52 whose "handler" value lands inside another op (15MKR02A 0x55f3,
  17DRL04 0x2cfc): either data or a form not decoded yet.
- **Escapes inside a string** (0x5c at a character boundary; SJIS trail bytes never reach 0x5c):
  handler table at RAM 0x80010a10, index = byte - 0x58, so only 0x58-0x79 are escapes:
  `n` newline (y += 14), `f` end of page, `h` half line (y += 7), `i`/`x`/`X`/`Y`/`u`/`t`/`c`/`e` take a decimal
  number parsed by 0x800120f0 (set x/indent/colour...), any other letter ends the box. Counts over 0x3b strings:
  `\n` 4383, `\f` 2872, `\i` 2, `\x` 1, raw tab 0x09 4. The renderer (0x80051a78) also turns a **double ASCII
  space into one full-width space** (0x80055698) - useful later for English indents.
- Inline text means a longer line shifts every later byte: `tools/scn.py rebuild()` re-lays the file (ops in
  address order, gaps verbatim), relocates every address operand and every data-table u16 that points at a
  moved block, and `tests/test_extract.py::test_rebuild_relocates` proves the result still walks cleanly.
- Sizes: largest SCN 12,923 bytes (25TOU). Load slots (measured from RAM in phase 5): area 0x80168000,
  map 0x8016a000, 99CMN 0x8016c000, event 0x8016d000, each file copied whole to its slot; sizes were never
  proven to have room to grow, which is why the marker build keeps every SCN file at its own length
  (`tools/insert.py`, phase 5).

## Insertion (phase 5, `tools/insert.py`, `tests/test_insert.py`)
- English is written as **ASCII bytes**: the field/message renderer draws them at 8 px/char (docs/re/font.md);
  a message page wraps by itself (28 chars in a standard box, measured).
- A message op is `3b 02 <text> 00`. Two modes:
  - **marker / in place** (the marker build, `build.py --marker`): the text is cut or space-padded to the op's
    original payload length, so no file changes size and no pointer moves.
  - **relocate** (the English insert, `relocate=True`): the op may grow; `scn.rebuild()` relocates every address
    operand and the u16 data tables that point at moved blocks. The build then re-walks the file and falls back
    to in-place when a new walk error appears. Growing files was **not** safe at phase 5: with relocation every
    SCN file at once the intro hung on "Now Loading" (a pointer form the codec misses), so a whole-file
    relocation needs that walk gate plus an in-game tour before it can be trusted.
- **Text that has no message op** (choice-option lists, place-name banners like `\x18港町オールバイン`) is a data
  run referenced by tables the codec does not relocate, and its leading control byte matters: the marker build
  leaves those runs alone (`DATA_RUNS = 0`) and reports them. Three of the phase-4 "strings" are not text at
  all: e.g. `02OLB:159` is the op `01 2024` plus the jump `06 018a`; a file scan for kana still matches it, and
  writing there hangs the intro. `insert.scn_insert()` skips any entry whose bytes overlap a walked op block
  unless it is a message payload.
- MES (VIS captions) and SMX (item/skill pools) have fixed offsets, so their strings keep their byte length.
  MES text cannot be ASCII at all until the VIS renderer is patched (docs/re/font.md).
- EXE labels: the same string can sit in two places (強さ at 0x78c0c **and** 0x78dec); both are extracted and
  written, and the field menu in the marker build still showed Japanese, so at least one more copy (or an image)
  feeds the menu - check with `jp_left.py` and the phase-8 tour.

## 2. Visual-scene text: VIS.MPS/*.MES (23 files, largest 2,347 bytes)  **verified**
u16 table at 0: [0] = 4 (header), then growing absolute offsets of the first string of each page; the strings
themselves start at the first of those offsets and are NUL-separated **lines**. Inside a line 0x0d is a line
break and the lines are centred with full-width spaces (8140). The first line of a page is the speaker
(`シノブ\r「...」\r`). Directives share the pool: a line starting 0x01/0x02 + an id (`\x01V13010`, `\x02`) is a
voice/sound cue, not text (no Japanese in it, so the extractor skips it). 374 captions in `script/mes/`.

## 3. Item / skill tables: SYS.MPS/*.SMX (2 files with text)  **verified**
`ITEM.SMX` (15,753 B), `KIES.SMX` (1,495), `SHINOBU.SMX` (3,357). Fixed records holding u16 offsets into a
NUL-separated pool at the end (ITEM pool starts 0x28eb with `Ｄｕｍｍｙ`); record size/other fields still guess.
The pool also holds resource names (`d\_sho_va3.bca`), which the extractor skips. 296 strings in `script/smx/`.

## 4. EXE strings (SLPS_010.30)  **verified**
- file 0x800-0x17e0 (RAM 0x80010000-): menus, status labels, save/load/memory-card messages, option labels
  (`ステレオ　　モノラル`, `遅い　普通　速い`), battle results, learned-technique lines, shop (`買う`/`売る`).
- file 0x78c0c-0x79030: 2-4 byte fixed-slot labels (記録 設定 魔法 装備 道具 強さ, 攻撃 防御 魔法 剣技 撤退,
  買う 売る, セーブ ロード, status names 痺 眠 黙 禁 …). English must fit the slot or the strings move
  (lui/addiu refs, find with `disasm.py xref`).
- The region between the two ranges is code and tables; segment-level roundtrip filtering leaves 112 labels.
- Quirk: the 記録 menu label is stored as `8b 4c e6 5d` = 記 **訃** in cp932 where 記録 is meant - the disc's
  own bytes; the English ("Save") removes the question.

## Free space
- Disc: files can grow on rebuild (mkpsxiso relayout) if the game finds them by name (guess, `archives.md`).
- EXE: t_addr 0x80010000, t_size 0x79000 (ends 0x80089000); BSS/heap above, stack top 0x801fff00. No free
  RAM region proven yet. Candidates for moved strings: grow the EXE (if the region after 0x80089000 is unused
  BSS; check in phase 5 with a RAM watch) or put text in the data files themselves.
- SCN/MES/SMX: rebuilt whole by our tools, so they grow freely up to the game's load buffer (size unknown).

## Not found as text
- Boot prologue on red (`はるか昔 この...`, frames ~1500-2400): no SJIS match in any file. **guess:** part of
  LOGO.STR FMV. Confirm in phase 5 (jPSXdec decode; running its jar here needs the user's permission rule).
