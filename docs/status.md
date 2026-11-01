# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (engine spike + marker build) in progress 2026-11-02. Marker build boots and message boxes show
  their ids; VIS/MES captions still need a renderer patch. Next: that patch, then the width gate for the other
  box variants, then phase 6 (translate).
- **Done:**
  - Step 0: template, decisions D1-D7, dump pinned, PCSX-Redux + BIOS, hooks (see git history).
  - Phase 1: no earlier fan patch exists (PS1 or PC-98). Recon notes in `docs/re/` (index `README.md`):
    disc + PSMG/EM archives (verified, `tests/test_archives.py`), SCN bytecode interpreter + op 0x3b message +
    operand readers + escapes, MES and SMX formats, EXE string ranges, SYSTEM.FNT structure, PAD30 image format,
    static graphics sweep (472 images) with the graphics-text list G1-G5 in `docs/re/graphics.md`.
  - `mkpsxiso -y layout.xml` on the unedited dump already gives the pinned sha1 (phase 3 just wires it as a test).
  - Tools: `tools/mps.py`, `pad.py`, `re.py`, `sjstr.py`, `fnt.py` (draft). mkpsxiso/dumpsxiso 2.30 and armips
    0.11.0 in `tools/` (gitignored).
  - Phase 2: `tools/debug/` warp + tour (commands in AGENTS.md), notes `docs/re/scenes.md`, SCN disassembler
    `tools/scn.py` (+ `tests/test_scn.py`). Scenes: every area x every progress value its dispatcher tests
    (generated from `scenes_data.lua`), VIS 00-16, ending + credits, field menu + 6 sub-menus, item shop, inn,
    random / boss / event fight. Warp = play the intro from cold boot, then set var 3 (the game's own area
    change); tour saves `work/states/base_<cue>.sstate` at the intro's end and starts the other scenes there.
    Tour on the original disc: 150/150 proofs ok; sheets reviewed (menus, shop, inn, 3 fight types, VIS, END
    card all correct). Known limits (`docs/re/scenes.md`): area scenes use entrance 0, so some open on an empty
    corner (02OLB dock, 05SKS black); ending credits show tile garbage over their backdrops in the warp (check
    against a real ending before blaming the build).
  - Phase 3: `tools/build.py` (check dump, unpack once, copy tree to `work/build/tree`, `edit()` hook - empty -
    then mkpsxiso with the dump's layout; ~2 s). `tests/test_build.py`: repack of `work/orig/tree` = pinned sha1.
    Build smoke ok. LBA-shift test (SCN.MPS +16 sectors, every later file shifted): `tools/debug/cd_seeks.lua`
    shows all 122 seeks of boot + intro (XA, STR, MPS) follow the shift; warp tour on that disc 150/150 ok, proofs
    differ from the original tour only in animation/typing timing. So files may grow freely (`docs/re/archives.md`).
  - Phase 4: `tools/sctext.py` (cp932 + escape codec, byte-exact), `tools/scn.py` (walk with op-0x7b thread edges,
    `assemble`/`rebuild` with relocation of every address operand and of data-table u16s), `tools/extract.py`
    (`dump` writes `script/{scn,mes,smx}/*.json` + `script/exe.json`; `check` = roundtrip + coverage gate).
    **12,230 strings in 245 files**: scn 11,141 (7,300 walked, ~2,500 message ops found by file scan, ~1,200 kana
    runs for choice options/signs/banners), mes 374, smx 296, exe 112. Every entry roundtrips to its original bytes;
    no message op and no kana run is left unextracted (15 % of SCN bytes are data tables/padding, `extract.py gaps`).
    `tests/test_extract.py`: roundtrip + coverage + `test_rebuild_relocates` (grow a message in 5 files, file still
    walks clean and every jump lands on an op). A rebuild-with-an-edit runs over all 218 SCN files:
    215 stay clean, 3 do not (15MKR02A, 15MKR02C, 24UMB57 - a 0x52 handler value pointing into data, the same
    form as the two known cases `tests/test_scn.py` tolerates). Glossary seeded with the
    character/place/term names the script uses.
  - Phase 5 so far (2026-11-02): **font decoded** (`docs/re/font.md`): full-width glyphs are 12 rows x 4 bytes,
    each row a 12-digit base-6 number (6 grey levels); the half-width table at 0x10 is 256 x 36 bytes =
    8 px of 3 bits, 8 grey levels, and **the game already draws ASCII with it at 8 px/char** (menu "HP 192",
    "30 G", "YES/NO" - verified in-game). `tools/fnt.py` (sheet / ascii / ascii-write / dump) +
    `tests/test_insert.py::test_font_codec_roundtrip`. Two renderers: field/message/menu (`0x80051904`) takes
    ASCII; VIS/MES (`0x8005fd3c`) takes every byte as a SJIS lead, so ASCII there draws nothing.
  - Phase 5 insertion: `tools/insert.py` (`check` / marker mode) writes `[id]` markers through the real build
    (`python -X utf8 tools/build.py --marker` -> `build/kuro_marker.bin`). Marker mode keeps every SCN file at
    its own length and skips data runs: 12,230 strings, 2,489 sites too small for the full id.
    **The marker build boots and message boxes show their id** (`work/qa/mk_inn/f001300.png`,
    `work/qa/one/f001300.png` = a 36-char English line that wraps by itself). Width gate, first numbers:
    standard message box = **28 half-width chars per line, 4 lines per page, auto-wrap**.
- **Next (phase 5, finish):** (1) patch the VIS/MES renderer for ASCII (0x8005fd3c default branch: byte < 0x80 ->
   0x8005f684(byte), advance 8 px) - without it VIS captions (374 strings) cannot be English; (2) width gate for
    the choice window, item description, shop list and banners with `tools/debug/texttest.py`; (3) glyphs for the
    ASCII punctuation the disc's font leaves blank (`" ' * ; < > [ ] { } @ # $ % & ^ _ ` | ~`: `fnt.py
    ascii-write`); (4) why the field menu still shows Japanese while its EXE copies are marked (duplicate copy or
    an image); (5) whole-file relocation of a grown SCN needs the walk gate plus a tour before it is trusted -
    doing it everywhere hung the intro.
- **Later phases, known work:** op 0x7c (2,536 gap messages are found by scanning, not by following 0x7c) and the
  two 0x52 handler values that land inside ops (15MKR02A 0x55f3, 17DRL04 0x2cfc) - decode only if the marker
  build shows text we miss; `DBUGFON.TIM` users not looked for (warp works without a debug menu); credits KRED00-15
  and WIN02 as images; boot prologue probably in LOGO.STR (FMV).
- **Open bugs:** none.
- **Not verified:** GUI keyboard input in `tools/pcsx/`. Seeks beyond the intro (later XA/BOD.STR ending) after an
  LBA shift: same read path (pc 8006A780) and by-name lookup, so expected fine; re-tour every build anyway.
- **Waiting on the user:**
  - (non-blocking) Running the downloaded jPSXdec jar (`work/dl/jp/`) was refused by the auto-mode permission
    check; needed later to decode/re-encode LOGO.STR if the prologue is FMV. A permission rule for
    `java -jar tools/jpsxdec/jpsxdec.jar` would unblock it.
  - (non-blocking) Title logo 黒の剣: default keep (D5); the disc's volume id is BLADE_OF_THE_DARKNESS
    (official English subtitle), so an English subtitle line under the logo is the fallback plan.
