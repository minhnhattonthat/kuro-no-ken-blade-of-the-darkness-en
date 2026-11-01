# Polish list

One line per deferred item (reviewer Minors, flagged shortenings). The polish pass ticks each `[x]`, fixed or
`waived: reason`; the release script refuses to run while any line is unticked.

## Engine-dependent (phase 7)
- [x] every `banner`/`choice` unit longer than its JP byte length: relocated (`insert.scn_place`, choice tables rebuilt and re-sized by `insert.choices`)
- [x] `menu` units over 6 chars, `sys` over 26, `item` over 18: main menu, battle column, shop, config (`tools/asm/menus.asm`, D12); battle-result banner (1700-177c, 16a4, 152c); item names <= 18 (d116ce5); title tabs Status/Equip/Magic fit (work/qa/menus9); status/equip labels and equipment names (6d3ff31); battle ST markers Po/Si/Se/Sl/Pa in 18 px slots (fa7819f); battle name box + status header "Shinobu" (menus.asm); field ST shows only Normal/Poison (78df4-78e28), "Normal" stays inside the box (work/qa/menus9/z_box.png); save prompt 78f5c 上書き -> "Save" (the game draws "?" at x 44 and "..." 36 px after the word: "Overwrite" collided; static, `tools/asm` records 0x80080b58/0x80080b7c). waived: magic tab "Sword skill" (78e9c, x 148..236 on the 320 px magic page) not seen in-game: no member knows magic at the warp's new game
- [x] 17DRL03A:626, 06BLK02B:395, 06BLK02E:93f - speaker-label units: 626 now "Palman\n..." (the label line keeps its break; lint allows one `\n` after a label), 395 "Caius / Girl" and 93f "Caius, Mercenary" are label-only units (no name repeated)
- [x] choice/banner prefix bytes and raw tab `[09]` indents: re-attached from the JP at insert (`insert.unit_text` LEAD/TRAIL)
- [x] 99CMN:7e7 80e bd4 bf5 c2d, SLPS_010.30:16d8 - suffixes after an engine-printed item name: 7e7, bd4, 16d8 start with a space (`insert.flow` keeps one leading space; lint allows it after a particle); 80e/bf5 start their own indented line (JP layout); c2d "GOLD obtained." follows the number as the JP does. Scene `item_get` shows the line (the inject sets no name, blank in the JP too)
- [x] SLPS_010.30:800 810 - these are the memory-card file title (the code patches digits at fixed SJIS offsets): kept as the JP full-width roman bytes; the in-game slot line is the engine's ASCII template, unchanged (work/qa/saveow3, saved to a card in the emulator)
- [x] desc units with `\n`/`\f` codes carry a space before the code (b049/b050): none left in script/ (checked)

## Check in-game (phase 8)
- [x] 06BLK01C:1221/1230 - waived: the script prints リール then シノブ (7e/04 label ops) before the line; the JP shows シノブ too, so "Shinobu" is faithful

## Reviewer Minors
Wave 1: the translators applied their batches' Minors right after review (their agents were still live, which
costs less than a later pass); only the ones they skipped are listed here.
Story pass (phase 9): every chapter report's Minors, applied by translator agents, one row per id with the reason
for each waiver in `work/qa/story/minors/*.tsv` (80 fixed, 51 waived: check-only/JP-quirk notes, width-bound menu
labels, glossary-bound forms such as "Balkrutha, the Capital" and 剣技 "Sword skill", optional rewrites not clearly better).
- [x] c01-c03 Minors: 25 fixed, 23 waived; VIS05:2fe/346 "???" label restored in `insert.vis_text` (seen in work/qa/vis05)
- [x] c04-c06 Minors: 25 fixed, 8 waived ("the Frontier" kept capitalised: glossary 辺境)
- [x] c07-c09 Minors: 19 fixed, 8 waived
- [x] c10-c11 Minors: 13 fixed, 11 waived
- [x] story re-check 2026-11-02 (c01/c05 full re-read, c02-c11 fixes re-checked, new c12 battle talk): 18 Minors applied, the rest waived with reasons in `work/qa/story/reports/recheck_2026-11-02.md` (width-bound EXE/item slots, optional rewrites)
- [x] stub pages from the rewrites (02OLB01:889, 20NNP93:8f6, 24UMB57:c41) and 03YSK01A:b11 rephrased: lint 0 stub pages
- [x] pilot 02OLB01 Minors: applied (13fe, ccb, 78d, 889, 19f0 + copies 01A:119b 01B:f35 02:a15 03:cb8, 1a58 + copies, 1ab3 + copies, 15c7). waived: 95c optional "That's the idea." (current line reads fine)
