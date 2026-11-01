# Text engine

Encoding everywhere: **Shift-JIS** (cp932) full-width, NUL-terminated. Some EXE strings mix half-width ASCII
("pts の経験値を得た", "Gold を得た") - how the renderer draws ASCII is open (phase 5, `docs/re/font.md`).
RAM = EXE file offset - 0x800 + 0x80010000.

## 1. Scripts: SCN.MPS/*.SCN (bulk of the game: ~11,000 lines, ~308 KB SJIS)
Bytecode interpreted by the EXE. **verified** by disassembly (`tools/re.py dis`), gcc -O0 code, easy to read.
- Main interpreter 0x8002c8c0: fetch byte at script pointer (global word **0x80088fd4**), dispatch through a
  256-entry table at **0x800100ac** (file 0x8ac). Ops 0x99-0xfe go to the default 0x8002ebb4 (no-op/next).
  Op 0xff -> extended interpreter 0x8002ec48 (own dispatch, sub-opcode byte). Handler addresses: dump with
  `python tools/re.py` (the table is the 349-entry run at 0x8001004c, script ops start at index 0x18).
- Operand readers (each advances 0x80088fd4):
  - 0x8002bfdc: u16 little-endian.
  - 0x8002c5a8: u8.
  - 0x8002c194 "value": type byte; 0 -> u16 literal, 1 -> u16 variable index (0x8002c09c), other -> nothing (0).
  - 0x8002c2ec "address": a value, converted by 0x8002bb14 to a script address. **Jump targets are file offsets
    inside the SCN** (e.g. `06 c8 04`, `ff 0b 00 02 00 00 a6 01`).
  - 0x8002c60c "switch": var(u16), value, u8 N, N x 3-byte address values.
  - 0x8002c33c "string": type byte 0x02 -> inline NUL-terminated SJIS (pointer returned), else an address/value.
- **Message op 0x3b** (handler 0x8002d460): string operand -> 0x80055698 (draw) and 0x800545c8. In the files: `3b 02 <SJIS..> 00`.
  The speaker name is its own 0x3b line (`シノブ\n`), followed by the quote line(s).
- Escapes inside strings (counts over all SCN op-0x3b strings): `\n` newline 6633, `\f` end of page / wait 4372,
  `\xNN` (2 hex digits) x position, used to centre area-name banners (`\x18港町オールバイン`) 31, `\iN` 2
  (`\i0\tマルダー\n\i2`, guess: indent/icon), raw 0x09 tab (after names, choices) ~5.
- **Insertion constraint:** text is inline, so a longer line shifts every later byte and every address operand
  pointing past it. Plan (phase 4): a full bytecode parser from the handler table (operand signature per op),
  relocate all address operands on rebuild; roundtrip test re-assembling every SCN byte-identical. Fallback if
  some op can't be decoded: change op 0x3b to take a u16 offset into an appended text pool, padded to the original
  length so nothing moves.
- A regex scan for `3b 02 ... 00` gives false positives (`02OLB.SCN` 0x157 is data); use the parser.
- Sizes: largest SCN 12,923 bytes (25TOU). Load buffer size not yet known (phase 5: find the SCN load call).

## 2. Visual-scene text: VIS.MPS/*.MES (23 files, largest 2,347 bytes)
u16 table at 0: [0] = 4, [1] = ?, [2..] absolute offsets of strings (table ends where the first string starts).
Strings: SJIS, 0x0d = line break, NUL end; lines centred with full-width spaces (8140). The first line of a quote
is the speaker (`シノブ\r「...」`). Shown over the `*.CG` pictures (ship intro = VIS00, bedroom = VIS02, verified
in `work/qa/recon1` shots). **verified** for VIS00/VIS02 by decoding; table semantics of [0]/[1] guess.

## 3. Item / skill tables: SYS.MPS/*.SMX
`ITEM.SMX` (15,753 B), `KIES.SMX` (1,495, Caius's skills), `SHINOBU.SMX` (3,357, Shinobu's magic). Name[16]
header (`ITEM.SMX`), fixed records, then a pool of NUL-terminated SJIS names and descriptions at the end.
Records hold u16 offsets into the pool: **verified** for ITEM record 0 (`eb28 cc2e` -> 0x28eb `Ｄｕｍｍｙ`,
0x2ecc description). Record size/other fields: guess. Rebuild = rewrite pool + offsets; file may grow (check
load buffer).

## 4. EXE strings (SLPS_010.30)
- file 0x800-0x17c8 (RAM 0x80010000-0x80010fc8): menus, status labels, save/load/memory-card messages, option
  labels (`ステレオ　　モノラル`, `遅い　普通　速い`), battle results (`pts の経験値を得た`, `は レベルアップした`,
  `Gold を得た`, `パーティは全滅した。`), learned-technique lines, shop. Some carry escapes (`\e`, `\x12`, `\x48`).
- file 0x78c0c-0x79010 (RAM 0x8008840c-): 4-6 byte menu labels (記録 設定 魔法 装備 道具 強さ, 攻撃 防御 魔法 剣技
  撤退, 買う 売る, セーブ ロード ...). Fixed slots: English must fit the slot or be moved (lui/addiu refs; find
  with `disasm.py xref`).
- Full list: `python -X utf8 tools/sjstr.py work/orig/tree/SLPS_010.30` (369 hits; ~130 real strings in the two
  ranges above, the rest are code bytes).

## Free space
- Disc: files can grow on rebuild (mkpsxiso relayout) if the game finds them by name (guess, `archives.md`).
- EXE: t_addr 0x80010000, t_size 0x79000 (ends 0x80089000); BSS/heap above, stack top 0x801fff00. No free
  RAM region proven yet. Candidates for moved strings: grow the EXE (if the region after 0x80089000 is unused
  BSS; check in phase 5 with a RAM watch) or put text in the data files themselves.
- SCN/MES/SMX: rebuilt whole by our tools, so they grow freely up to the game's load buffer (size unknown).

## Not found as text
- Boot prologue on red (`はるか昔 この...`, frames ~1500-2400): no SJIS match in any file. **guess:** part of
  LOGO.STR FMV. Confirm in phase 5 (jPSXdec decode; running its jar here needs the user's permission rule).
