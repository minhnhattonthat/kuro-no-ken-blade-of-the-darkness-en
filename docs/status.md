# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Session checks (2026-11-02, latest at `10bd219`):** no source change since `d9eaab2` (status.md only), no open
  `bug` issues, `main` synced with `origin/main`; zip `release/KuroNoKen_EN_v1.0.zip` SHA-1
  `9d610ee9b457f6eb74070aff06a1f0854009d2a4` (xdelta patch `c75e1c27..` + README.txt only) unchanged. Gates not
  rerun (nothing changed). Complete and unpublished (the user's call); a new session should only re-check this.
- **Release re-verified at HEAD d9eaab2 (2026-11-02, no source changes):** `release.py 1.0 --force --no-tour`
  passed 36 tests, lint 0 errors, extract 12,045 strings / 262 files / 0 problems, identity, archive gate, smoke,
  EXE `jp_left --orig` 0 runs, visual gate 168/168, story gate 12/12, and polish 0 unticked. Build SHA-1 is
  `6adb93743cbf17f53ca181421713c6c238042197`; the zip contains only `KuroNoKen_EN_v1.0.xdelta` (SHA-1
  `c75e1c27caad4db7187d147238b4176139e2690a`) + README.txt (2,929 B). Independent extraction and `xdelta3 -d`
  of the zipped patch against the pinned dump reproduces the build; the current zip SHA-1 is
  `9d610ee9b457f6eb74070aff06a1f0854009d2a4`. The reused full-tour manifest is current and all sheets have ok
  verdicts. Not published (the user's call).
- **Project complete; v1.0 release built and verified (latest full check 2026-11-02 at f438875 + the op-4 scene).**
  Source unchanged since 4d3c7e0 except `tools/debug/scenes.lua` (new scene) and `tools/debug/ai_probe.lua`. Full
  `tools/release.py 1.0 --force` passed the same session the scene landed: 36 tests, lint 0 errors, extract 12,045
  strings / 262 files / 0 problems, identity, archive gate, smoke, tour 164/164, visual gate 168/168, story gate
  12/12, polish 0 unticked, patch re-applied = build. `build.py` reproduces `build/kuro_en.bin` SHA-1
  `6adb93743cbf17f53ca181421713c6c238042197`; `release/KuroNoKen_EN_v1.0.zip` (5,494,817 B, SHA-1
  `92f56c014cd181ae4421b5a231835552cf5104e0`) = `KuroNoKen_EN_v1.0.xdelta` (5,491,646 B, SHA-1
  `c75e1c27caad4db7187d147238b4176139e2690a`) + README.txt (2,929 B); an independent `xdelta3 -d` of the zip's
  patch against the pinned dump gives `6adb9374..`, and the zip lists only those two files. The zip SHA-1 changes
  per rebuild (timestamps); the patch SHA-1 is the stable one. Not published (user's call). **A new session has
  nothing to do; don't re-run the release gates unless source changes.**
- **AI op 4, the last unseen battle-talk line (2026-11-02):** new scene `battle_talk_ko` shows the KO branch:
  `Zephudol / "Heh, how's the Ravenous Storm taste?"` (C021_X10 AI op-4 record 0x860, talk op 4 → entry 0 0x874 →
  record 0x94e/B06020). The op-4 handler 0x8003cae4 passes when actor 0 (`0x800945f0`, u16 HP at +0x14) is at 0 and
  gp+0xc31 (`0x80088f0d`) is 1, then zeroes gp+0xcb0 and calls the talk interpreter — `tools/debug/ai_probe.lua` logs
  the AI record at frame 1379 and the interpreter call (`04 02 74 08`, cb0 0). The old note that this needs a fight
  Kaies is in was wrong: the fight's two live party records are max 240 and 192 HP and the 240 one is pinned at 0.
  Proof `work/qa/talkko4/proof.png`, tour shot + verdict `work/qa/v8/verdicts/c17_000.tsv` ok; `docs/re/scenes.md`
  updated. `tools/debug/ai_probe.lua` is the promoted probe (AI records, talk calls, op 0/3/4 handler entries).
- **Battle talk, party branch (2026-11-02):** the talk sub-interpreter's op lengths were read off its dispatcher
  (`03` = 4 bytes, `05` = 2, `06` = 3), which dissolves the old "second reader" question: the `02 …` groups are just
  the talk streams handed to AI ops 0/3/4, not a separate condition table (`docs/re/scenes.md` §Talk refs). New scene
  `battle_talk_party` (same Zephudol fight; holds h[0x8008905e]=0 and h[0x800890b8]=5, the AI op-0 gate) shows the
  party line in the right-hand window slot: `Caius / "Looks like we can't escape..."` (record B00000); with
  h[0x8008905e]=1 it shows `Shinobu / "We can't escape?!"` (entry 2), confirming the op-4 index formula. All 337 BSX
  talk records carry a `03` ref (0 without), so none is left Japanese. Proofs `work/qa/talkparty{,2}/`; tour 163/163
  (162 shots byte-identical to the last release tour, only `battle_talk_party` new), verdict
  `work/qa/v8/verdicts/c16_000.tsv` ok.
- **Release re-verified at HEAD 4d3c7e0 (2026-11-02):** `tools/release.py 1.0 --force --no-tour` (36 tests,
  lint 0 errors, extract 0 problems, identity, build sha1 6adb93743cbf17f53ca181421713c6c238042197, smoke ok,
  EXE `jp_left` 0, visual gate 167/167, story gate 12/12, polish 0 unticked, patch re-applied = build). The zip
  `release/KuroNoKen_EN_v1.0.zip` (5,494,817 B; sha1 103ed844c29132bac1be98e42458561f7ecd6a51) contains only the
  patch + README.txt; patch sha1 c75e1c27caad4db7187d147238b4176139e2690a. Unpublished (the user's call); phase 9
  remains complete. Spot-check 2026-11-02 at 9104d05 (status-only commits since): `build.py` sha1 6adb9374.., zip
  sha1 103ed844.. unchanged. **Project is complete: a new session has nothing to do but publish when the user asks.**

- **Phase:** 9 (release) done 2026-11-02, **re-cut after the AI op-4 scene** (see the second bullet): `tools/release.py
  1.0 --force` (full tour 164/164 ok), then `--no-tour` after the new shot's verdict: 36 tests, lint 0 errors,
  roundtrip, identity, English build, smoke, visual gate 168/168, story gate 12/12. `release/KuroNoKen_EN_v1.0.zip`
  (xdelta3 5,491,646 B + README.txt only; patch sha1 c75e1c27caad4db7187d147238b4176139e2690a; zip sha1
  92f56c014cd181ae4421b5a231835552cf5104e0). Re-applied patch = build sha1 6adb93743cbf17f53ca181421713c6c238042197,
  CRC32 56e68c0f. Not published (the user's call); phase is complete. The hashes below for 38a3e2../72aaba28.. are
  superseded.
- **Battle talk seen in-game (2026-11-02):** decoded (`docs/re/scenes.md` §BSX battle talk: AI records `fb fa <op>`,
  talk sub-interpreter 0x8003c4a0); new tour scene `battle_talk` shows Zephudol's line page 1 (verdict
  `work/qa/v8/verdicts/talk_1.tsv`). Found + fixed: the page mark sits in column 25 of a page's 4th row; 5 records
  had a 25-char row there, `insert.bsx_text` now wraps that row at 24 (test-enforced). Other talk triggers (op 0
  party lines, op 4 "Kaies at 0 HP") not shown on screen; same box and wrap, so low risk.
  Done: polish.md all ticked; story pass 12/12 chapters
  (`qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts` exit 0; reports `work/qa/story/reports/`,
  incl. `recheck_2026-11-02.md`); **BSX battle talk** (124 lines, 17 files, `script/bsx/`, chapter c12) extracted,
  translated, inserted (`insert.bsx_insert`: refs `03 01|02|03 <u16>`); `tools/release.py` + `docs/README.template.txt`;
  `jp_left.py` on the EXE text ranges: 0 runs.
  Release tour 2026-11-02 (`work/qa/tour_release/`, 161 scenes ok) copied into `work/qa/v8/scenes`; 34 changed
  shots re-reviewed (verdicts `c14_*.tsv`); `palman_label` now loads its event script first (inject op 36) and
  shows the label (fixed a missing opening quote in 17DRL03A:626).
- **Release re-verified 2026-11-02 at HEAD 0908d2f:** `tools/build.py` reproduces sha1 6adb9374..; the zip
  (sha1 72aaba28..) holds patch + README.txt only; its patch (c75e1c27..) applied to the pinned dump gives 6adb9374..;
  README names dump + patched hashes; visual gate 166/166, story gate 12/12, polish.md 0 unticked. Unpublished
  (the user's call).
- **Next:** nothing required; publishing is the user's call. Battle talk is now covered in-game in every branch
  (`battle_talk` op 3, `battle_talk_party` op 0, `battle_talk_ko` op 4).
  Gates: `build.py` = `insert: 6811 strings, 5905 message ops relocated, 0 problems`; EXE romdiff gate
  (`data/exe_allowed.txt` = hooks/layout only; strings + pointers via the write journal, 139 writes; EXE sha1
  pinned in build.py); `tools/gate.py` on every archive (see its docstring); `batches.py lint` 0 errors;
  `check.py` = 36 tests (incl. `tests/test_english_build.py`, a fresh English build in a temp tree) + lint.
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
  slot), so the trigger is not battle start or a turn count. The BSX's own "condition table" in front of its
  `03 02 <offset>` refs (C021_X10: `02 9f 07` / `ff`-separated entries) turned out to be the AI ops' own talk
  streams, not a separate table (2026-11-02, docs/re/scenes.md §Talk refs; scene `battle_talk_party` shows one).
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
  - (non-blocking) Publishing v1.0 (`release/KuroNoKen_EN_v1.0.zip`): only on the user's say-so.
  (Resolved: jPSXdec runs via `tools/fmv.py`, prologue FMV is English; title logo kept per D5.)
