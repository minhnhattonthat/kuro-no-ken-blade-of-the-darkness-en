# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4 (extract) done 2026-11-01. Next: phase 5 (engine spike + marker build). Build = unedited disc.
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
    no message op and no kana run is left unextracted (22 % of SCN bytes are data tables/padding).
    `tests/test_extract.py`: roundtrip + coverage + `test_rebuild_relocates` (grow a message in 5 files, file still
    walks clean and every jump lands on an op). 151/154 SCN files rebuild cleanly after an edit; the 3 that do not
    are the two known 0x52 handler cases plus 24UMB57/15MKR02C/15MKR02A-class data. Glossary seeded with the
    character/place/term names the script uses.
- **Next (phase 5, engine spike + marker build):** font glyph format (`docs/re/font.md`, still undecoded, no ASCII
  glyphs) and the width gate; `[id] marker text` for every entry of `script/`; SCN load buffer size (25TOU is
  12,923 B in an 8 KB slot pair - confirm before growing any SCN). Insertion uses `tools/scn.rebuild()`.
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
