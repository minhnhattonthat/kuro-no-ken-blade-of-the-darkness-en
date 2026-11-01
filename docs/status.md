# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3 (identity build) done 2026-11-01. Next: phase 4 (extract). Build = unedited disc (sha1 = dump).
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
- **Next (phase 4, extract):** SCN bytecode parser with address relocation + roundtrip test re-assembling every
  SCN byte-identical; MES/SMX/EXE string extraction into `script/` (format: `references/pipeline.md` §Extract);
  hook it into `build.py`'s `edit()` later (phase 5 marker build).
- **Later phases, known work:** SCN parser open ops (phase 4): item-shop list
  after 02OLB01 0x19db, 17DRL04 data at 0x2cfc, see `docs/re/scenes.md`); `DBUGFON.TIM` users not looked for
  (warp works without a debug menu); font glyph format
  undecoded, no ASCII glyphs (phase 5); credits KRED00-15 and WIN02 as images; boot prologue probably in
  LOGO.STR (FMV).
- **Open bugs:** none.
- **Not verified:** GUI keyboard input in `tools/pcsx/`. Seeks beyond the intro (later XA/BOD.STR ending) after an
  LBA shift: same read path (pc 8006A780) and by-name lookup, so expected fine; re-tour every build anyway.
- **Waiting on the user:**
  - (non-blocking) Running the downloaded jPSXdec jar (`work/dl/jp/`) was refused by the auto-mode permission
    check; needed later to decode/re-encode LOGO.STR if the prologue is FMV. A permission rule for
    `java -jar tools/jpsxdec/jpsxdec.jar` would unblock it.
  - (non-blocking) Title logo 黒の剣: default keep (D5); the disc's volume id is BLADE_OF_THE_DARKNESS
    (official English subtitle), so an English subtitle line under the logo is the fallback plan.
