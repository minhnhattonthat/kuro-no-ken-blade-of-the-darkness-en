# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 done 2026-11-02 (marker build, VIS ASCII hook, width gate). Next: phase 6 (translate), starting
  with the engine items below.
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
    **12,230 strings in 245 files** (11,916 after phase 5 removed non-text): scn 11,141 (7,300 walked, ~2,500 message ops found by file scan, ~1,200 kana
    runs for choice options/signs/banners), mes 374, smx 296, exe 112. Every entry roundtrips to its original bytes;
    no message op and no kana run is left unextracted (15 % of SCN bytes are data tables/padding, `extract.py gaps`).
    `tests/test_extract.py`: roundtrip + coverage + `test_rebuild_relocates` (grow a message in 5 files, file still
    walks clean and every jump lands on an op). A rebuild-with-an-edit runs over all 218 SCN files:
    215 stay clean, 3 do not (15MKR02A, 15MKR02C, 24UMB57 - a 0x52 handler value pointing into data, the same
    form as the two known cases `tests/test_scn.py` tolerates). Glossary seeded with the
    character/place/term names the script uses.
  - Phase 5 (done 2026-11-02). **Font** (`docs/re/font.md`): full-width glyphs 12 rows x 4 bytes, base-6;
    half-width table 256 x 36 bytes, 8 px of 3 bits, **pixel x in bits 3x** (the first reading was mirrored; fixed).
    The field/menu renderer (`0x80051904`) draws ASCII at 8 px; the build fills the punctuation the disc leaves
    blank (`. , ' " ;` etc., `fnt.patch_ascii`). **VIS/MES captions use the BIOS kanji font** (Krom2RawAdd):
    `tools/asm/vis_ascii.asm` (armips, applied by `build.py`) rewrites the caption parser's tail so a byte < 0x80
    is one 8 px glyph built from the SYSTEM.FNT half-width table; `tests/test_asm.py` runs it under unicorn;
    in-game: VIS00 shows English (`work/qa/vis_ascii/`).
    **Marker build** (`build.py --marker`): tour 150/150 ok (`work/qa/mtour/`) - field boxes, menus, shop, battle
    banners, VIS captions all show ids (the old "menu still Japanese" was a warp from an original-disc state: a
    state keeps that build's EXE). **Non-text removed** from `script/`: 312 SMX record "strings" (`E8 03`),
    a bytecode run (02OLB 0x159), a binary run (25TOU 0x3e); 11,916 strings now (`test_no_binary_entries`).
    **Width gate**: `data/windows.json` (chars/lines per variant, shot, engine flags). Field box 28 x 4 (27 on a
    page's last line, auto-wrap, auto page), VIS 62 x 5 (no wrap), item name 18, description 22 x 2, battle
    banner 26, system message 26, choice 14 in today's window. `@` is a field-renderer control (`@64` = '@').
    Tools: `build.py --qa ID=TEXT [--data-runs]`, `tools/debug/boxes.py`, scene `choice_csl`.
- **Next: phase 6 (translate)**, after these engine items that change what translators may write
  (`data/windows.json` "engine"): (1) choice window sizing at 8 px per ASCII byte (op 7d handler) - else every
  choice overflows; (2) wider field menu / item+magic tabs / battle command column (3 chars today; English labels
  need ~7); (3) SMX pools keep JP byte lengths (names 4-14 B): relocate the pool's u16 offsets so names and
  descriptions can grow; (4) EXE labels are fixed slots (relocate with lui/addiu refs); (5) SCN data runs
  (24 choice options) are written in place only (`--data-runs`), so options must fit their JP byte length or
  the 7d tables get relocated. Then the translator tooling (batch check/fit against `data/windows.json`) and
  batches per `references/translation.md`. Not measured yet: battle item/magic lists (skill_name is a guess).
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
