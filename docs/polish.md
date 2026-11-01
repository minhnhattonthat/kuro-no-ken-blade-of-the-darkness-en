# Polish list

One line per deferred item (reviewer Minors, flagged shortenings). The polish pass ticks each `[x]`, fixed or
`waived: reason`; the release script refuses to run while any line is unticked.

## Engine-dependent (phase 7)
- [x] every `banner`/`choice` unit longer than its JP byte length: relocated (`insert.scn_place`, choice tables rebuilt and re-sized by `insert.choices`)
- [ ] `menu` units over 6 chars, `sys` over 26, `item` over 18 (`batches.py lint menu sys item`): main menu, battle column, shop and config done (`tools/asm/menus.asm`, D12); battle-result banner (26) fit pass done: SLPS_010.30:1700-177c "Learned <name>." (category dropped: 3 glossary warnings), 16a4 "pts of EXP gained.", 152c "Not enough free blocks."; left: item names 19-21 (glossary forms; item list x 77..226), title tabs Status/Equip/Magic overflow their small window, ST field ~4 chars (Normal, Poison, Paralysis...), battle ailment markers are 1-kanji slots (78fa8-78fb8), status/equip labels (Accuracy, Defense), magic tab "Sword skill", save "Overwrite", ailment "Paralysis", status "Normal" spills 1 px, battle name box + battle status header "Shinobu" overflow (name box creator not found yet)
- [ ] 17DRL03A:626, 06BLK02B:395, 06BLK02E:93f - unit starts with a speaker-label op (`パルマン`, `カイエス / 娘`, `カイエス / 傭兵`); the insert must keep those ops as labels and the English must not repeat the name
- [ ] choice/banner prefix bytes (`\x6シノブ`, `\x18港町...`) and raw tab `[09]` indents must be re-attached from the JP at insert
- [ ] 99CMN:7e7 80e bd4 bf5 c2d, SLPS_010.30:16d8 - suffixes after an engine-printed item name/amount start with ": " / no space; check in-game and add the leading space at insert if needed
- [ ] SLPS_010.30:800 810 - save-slot templates (kept in place, space padded): check the slot number/time positions in-game (1644 166c 165c done: options placed at the JP columns with `\xNN`, NN hex = gap in 2/3 px, D12)
- [ ] desc units with `\n`/`\f` codes carry a space before the code (b049/b050): check it renders harmlessly

## Check in-game (phase 8)
- [ ] 06BLK01C:1221/1230 - the disc labels a sceptical scholar's line シノブ (two labels in a row, リール then シノブ); see what the game shows

## Reviewer Minors
Wave 1: the translators applied their batches' Minors right after review (their agents were still live, which
costs less than a later pass); only the ones they skipped are listed here.
- [ ] pilot 02OLB01 Minors (shop/inn lines are reused verbatim in 02OLB01A/01B/02/03: change every copy together): 13fe "Funny sort of name" -> "Unusual name, huh?"; 95c optional "That's the idea."; ccb "will show me the way" -> "will tell me"; 78d "kept them all busy" -> "kept everyone's attention"; 889 drop "there"; 19f0 -> "Need armor for the road? Special bargain prices, going on right now!"; 1a58 "right this way ... right now" repetition; 1ab3 -> "...They all just order the cheap booze."; 15c7 -> "I'll say thanks, for what it's worth."
