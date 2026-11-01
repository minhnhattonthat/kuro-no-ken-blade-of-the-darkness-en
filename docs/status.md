# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 (release) done 2026-11-02. Full `python -X utf8 tools/release.py 1.0 --force` passed this session:
  35 tests, lint (0 errors), extraction/roundtrip, identity build, English build, cold-boot smoke, 161/161 tour scenes,
  visual gate (165/165) and story gate (12/12). It wrote `release/KuroNoKen_EN_v1.0.zip` (xdelta3 5,491,643 B +
  README.txt only; patch sha1 da22b7a267d4465088e277399d3904f163f64dcb; zip sha1
  c48f3ce7bf18d843410e54e225c9b1e3c1a87e57). Re-applied patch = build sha1 38a3e20609b3655d74833988be451a834732b481,
  CRC32 e67c9958. Not published (the user's call); phase is complete.
  Done: polish.md all ticked; story pass 12/12 chapters
  (`qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts` exit 0; reports `work/qa/story/reports/`,
  incl. `recheck_2026-11-02.md`); **BSX battle talk** (124 lines, 17 files, `script/bsx/`, chapter c12) extracted,
  translated, inserted (`insert.bsx_insert`: refs `03 01|02|03 <u16>`); `tools/release.py` + `docs/README.template.txt`;
  `jp_left.py` on the EXE text ranges: 0 runs.
  Release tour 2026-11-02 (`work/qa/tour_release/`, 161 scenes ok) copied into `work/qa/v8/scenes`; 34 changed
  shots re-reviewed (verdicts `c14_*.tsv`); `palman_label` now loads its event script first (inject op 36) and
  shows the label (fixed a missing opening quote in 17DRL03A:626).
  Next (optional, v1.1): an in-game look at a battle-talk line (the BSX condition table in front of its `03 02`
  refs gates it, see the BSX bullet below).
  Gates: `build.py` = `insert: 6811 strings, 5905 message ops relocated, 0 problems`; EXE romdiff gate
  (`data/exe_allowed.txt` = hooks/layout only; strings + pointers via the write journal, 139 writes; EXE sha1
  pinned in build.py); `tools/gate.py` on every archive (see its docstring); `batches.py lint` 0 errors;
  `check.py` = 35 tests (incl. `tests/test_english_build.py`, a fresh English build in a temp tree) + lint.
- **Phase 7 review (2026-11-02) fixed:** check.py now gates the English build + full lint; archive gate
  `tools/gate.py` (unedited files identical, member lists, SCN walk/slot, MES/SMX/BSX bytes outside text +
  pointer slots, Japanese left beside no English); EXE writes journaled (`romdiff --writes`); `insert.py check`
  = English + gate (was marker, always exit 1); field `flow()` pulls a word down onto a stub last line (< 6 chars,
  same page breaks; 0 left, test-enforced), 19IRE36:111d laugh shortened (a 29-char word was hard-split).
- **BSX closed (2026-11-02):** the non-talk SJIS runs in BSX files are per-enemy AI action labels (1,983 runs, 124
  distinct strings in 274 files: 剣で攻撃, 自爆《禁止》, 同カイエス, enemy spell lists) plus the `CB 90` fill of unused
  action records (decodes as 斥, read as 4-byte records - not text). Proven never displayed: in a complete fight
  (`battle_boss`, which loads `D070_T10.BSX`, 721 bytes; enemy acted, party wiped) `tools/debug/slot_reads.lua` shows
  202 bytes read but never 0x129-0x15b (its labels 呼ぶ 0x147, 《相打ち》 0x14c), and `tools/debug/text_draws.lua`
  shows the text layout drew only its fixed UI set (19 calls: party name, HP/MP/ST, 6 commands, numbers, game-over
  banner), nothing from the slot - also in the marker build, which shows the ids of every other text source. The
  displayed names come from EXE/SMX/SCN; the labels stay Japanese (D14, `docs/re/scenes.md`).
  Battle talk itself was checked at byte level only (337 records in the built BSX files: all English, all referenced,
  every file <= 0x1400); no scene reaches a talk line yet. Tried 2026-11-02: the Zephudol story fight run directly
  (06BLK04 slot 1, `RUN=0x32ba` = file 0x12ba, `5f bac_07` + `7f c021_x10`; party HP pinned at 9999 so the fight
  lasts several rounds) - the fight runs but no talk line is drawn (`text_draws.lua`: 54 draws, none from the BSX
  slot), so the trigger is not battle start or a turn count. The BSX's own condition table in front of its
  `03 02 <offset>` refs (C021_X10 0x866: `02 9f 07` / `ff`-separated entries) is not decoded: decode that, or find
  the AI action that shows a line, to see one in-game.
  A stale `work/states/base_kuro_en.sstate` (older build) hangs scenes ~frame 500: re-make it with the tour.
- **Phase 8 result:** tour `work/qa/tour11/` 155/155; visual-QA gate `qa_gate.py check work/qa/v8/manifest.tsv
  work/qa/v8/verdicts` exit 0 (159 shots: 155 scenes + `prologue_1..4`; brief `docs/visual-qa-brief.md`). Fixed in
  phase 8: battle name tab + status name ("Shinobu"), config options (coloured by JP byte range) + Text Speed highlight
  rects (0x80080d1c), VIS10 second caption loop ASCII-aware (`vis_ascii.asm`, max 62 columns: 63 wrapped the glyph
  upload past VRAM x 1024), credits + save prompts redrawn (`tools/gfx.py`, D13), **boot prologue FMV** in English
  (`tools/fmv.py`: BOD.STR, jPSXdec partial-replace, Java; in-game `work/qa/prologue/`). Graphics rows
  (`docs/re/graphics.md`): G1 credits English in VRAM during the ending warp (`work/qa/credits_vram/`; the screen
  shows a leftover field layer over them, also on the original), G2 + G4 English in-game, G3 logo kept (D5),
  G5 nothing legible. Game over = EXE banner "The party was wiped out." (fits). Party records 0x80094604 /
  0x80094720 (u32 HP cur, max, MP cur, max). Savestate VRAM: protobuf field 5 -> sub-field 3 (2 MB, first 1 MB =
  1024x512 16bpp).
- **Phase 8 not covered by a scene** (polish.md lines): status detail page, equip, save Overwrite, battle ailments,
  learn banner, area-entry banner. Probe: `tools/debug/win_calls.lua`.
- **Phase 7 so far:** SCN = `insert.scn_place` (runs of message ops: inline if it fits, else `3b 00 <addr>` +
  jump, text in freed bytes / file tail up to the slot; payloads a data u16 may point at keep an inline head +
  `3b 00 <rest>`), choice tables (op 7d) rebuilt and right-anchored for 8 px ASCII, MES/SMX pools rebuilt with
  their u16 tables remapped, EXE strings repacked in their two areas with every data word / lui+lo pointer
  rewritten (`exe_refs`). VIS fix: English caption pages overran the 0x6000-byte GPU packet buffer when skipped
  (field froze after VIS 0, no sprites); `vis_ascii.asm` defers past 0x4000 (docs/re/font.md). Bisect flags
  `build.py --only/--skip/--legacy/--keep-going/--no-grow/--out`. Full English build reaches the inn warp with
  English text and the YES/NO choice (`work/qa/bis_EN/`).
- **Phase 6 result:** every unit translated and merged into `script/` (`batches.py stats`: 6,682/6,682 incl. 1,282
  speaker labels; `check` OK on pilot + b001-b050). Every batch had a reviewer-agent pass, but its reports were
  not kept (`work/tl/reviews/` is empty), so those reviews can't be audited: the phase-9 story pass (every
  chapter, verdicts saved) is the auditable review and must cover the whole script. Repeated NPC lines unified.
  Glossary: D9 names, wave-1 decisions at its end. Batch work files (`work/tl/`) are gitignored; `script/` is
  the source of truth. Phase-6 review (2026-11-02) fixed: 3 『魔』 lines -> 'the demonic', 07CSL01A:aeb
  Yubaum-sama; the glossary check is now binding for every section (terms matched across ` / ` breaks, quoted
  『X』 needs 'X', kanji-compound / kana-verb false hits skipped, plurals ok), reviewed exceptions in
  `data/glossary_ok.tsv` (a test fails on a stale line).
- **Phase 6 tooling:** `tools/batches.py` (units, split, check, merge, fit, pairs, names, story, stats;
  `tests/test_batches.py`). Unit = one message **page** (D8): the English paragraph lives in the box's first entry,
  the other entries get status `box`; speaker-label ops (`カイエス\n`) are filled from glossary.md's Speaker labels
  table by `batches.py names` (1,282 filled). Forms: dlg (name label, 3 lines on page 1), cont (next page of the
  same speech), narration, vis, choice/banner (data runs, byte limit), item/desc/menu/sys. Box geometry 28/27 x 4,
  auto page; check = 3-page hard limit + stub-page warning. Pilot 02OLB01 (59 units) translated by the controller
  and merged; `docs/style-reference.md`, `docs/synopsis.md` (from a four-part read), glossary rebuilt (D9 spellings:
  Black Sword, Leib-Bern, Yubaum, Zephudol, Goetz), `docs/translator-brief.md`, `docs/reviewer-brief.md`.
  Batch files `work/tl/bNNN.tsv` / `.out.tsv` (gitignored work/), terms `build/terms_bNNN.txt`.
- **Phase 6 loop:** per batch `batches.py check bNNN` -> `pairs bNNN` -> reviewer (read-only, report saved to
  `work/tl/reviews/`) -> fix Critical/Important -> `merge bNNN`; Minors to `docs/polish.md`.
- **Phase 7 must do for the English insert:** box distribution in `insert.py` (wrap the box paragraph with
  `batches.pages`, spread the lines over the box's ops, empty ops for the rest; boxes are recomputed with
  `batches.units()`), MES captions = speaker line from JP label table + wrapped text (62, centred), SMX/EXE fit or
  relocate, data runs (choice/banner) in place. The pilot has not been seen in-game yet (D10).
  Also (D11): banner/choice/menu/item/sys text was written in full; the check warns where it exceeds the JP bytes or
  today's window (`batches.py check bNNN | grep warn`) - relocate/widen, else a flagged fit pass. Re-attach JP
  prefix bytes (`\x18` banners, `\x6` choice) and raw tab indents at insert. Desc units keep their JP `\n`/`\f`.
  Three units start with a speaker-label op (polish.md). The SCN relocation-of-every-file hang (phase 5) is the
  first blocker: 2,521 of 4,944 message/caption boxes need more bytes than their JP ops hold (wrapped lines + `\n`).
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
- **Engine items (now phase 7; translators were given the post-engine targets: menu 6, choice = JP bytes,
  item 18, desc 2x22, sys 26)** (`data/windows.json` "engine"): (1) choice window sizing at 8 px per ASCII byte (op 7d handler) - else every
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
