# Polish list

One line per deferred item (reviewer Minors, flagged shortenings). The polish pass ticks each `[x]`, fixed or
`waived: reason`; the release script refuses to run while any line is unticked.

## Engine-dependent (phase 7)
- [ ] every `banner`/`choice` unit longer than its JP byte length (check warns "phase 7 relocates or widens it"): relocate the data runs or the 7d tables, else shorten
- [ ] `menu` units over 6 chars, `sys` over 26, `item` over 18 (check warns): widen the windows (data/windows.json "engine") or shorten
- [ ] 17DRL03A:626, 06BLK02B:395, 06BLK02E:93f - unit starts with a speaker-label op (`パルマン`, `カイエス / 娘`, `カイエス / 傭兵`); the insert must keep those ops as labels and the English must not repeat the name
- [ ] choice/banner prefix bytes (`\x6シノブ`, `\x18港町...`) and raw tab `[09]` indents must be re-attached from the JP at insert
- [ ] 99CMN:7e7 80e bd4 bf5 c2d, SLPS_010.30:16d8 - suffixes after an engine-printed item name/amount start with ": " / no space; check in-game and add the leading space at insert if needed
- [ ] SLPS_010.30:800 810 1644 166c - templates and option rows laid out by full-width columns; check cursor/number positions in-game
- [ ] desc units with `\n`/`\f` codes carry a space before the code (b049/b050): check it renders harmlessly

## Reviewer Minors
- [ ] 09HIK01A:46b - 旦那 "Mister Caius here" stiff
- [ ] 10TNI03A:71e - "Shall I say that is an heir for you" awkward -> "Is this what it means to be an heir...?"
- [ ] 12MRS:86a - "under seal" -> "locked away"
- [ ] 14YMM:312/34b/39f - "It's come, a human has come" -> "A human's coming, a human's coming."
- [ ] 14YMM53:3e7 - "They shall not pass" meme -> "We won't let them pass, won't let them pass."
- [ ] 14YMM53:4b9 - 姉者 "Sister" -> "Elder sister"
- [ ] 15MKR01B:d43 - added "you old fool" not in JP
- [ ] 15MKR01D:4c1 - "Heeeelp meeeee" vs "Eeeeek!"
- [ ] 15MKR02A:4a1 - mantra "sardine" -> "saury" (optional)
- [ ] 15MKR02A:604 - ぞよ pomp lost: "The oracle has descended!"
- [ ] 15MKR02A:414 - 先生 "His Eminence" vs "the Teacher" (06BLK07J uses "the Teacher")
- [ ] 15MKR02E:e87 - 残念です "it's no use" too strong -> "it's a pity"
- [ ] 14YMM:7f6 - "Who the hell are you?!" slightly strong
