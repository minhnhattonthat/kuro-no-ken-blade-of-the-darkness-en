# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All of D1-D7 came with the owner's one-shot run brief (Orca coordinator, 2026-11-01), applied to every game.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-01 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order (given name first). |
| D2 | 2026-11-01 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-01 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-01 | Abbreviations | engine work first (default), abbreviate | Default: engine work first, abbreviate only as a flagged last resort. |
| D5 | 2026-11-01 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the Japanese logo only if no official English version exists. |
| D6 | 2026-11-01 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-01 | Existing saves / memory cards / savestates | use the user's, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-02 | Translation unit for field messages (controller, under D6) | per JP line (op), per page (box) | Per page: the English is one paragraph stored in the box's first entry, wrapped by tool at insert. JP lines are ~18 full-width chars and English needs ~2x, so line-by-line English would break mid-thought on every line. |
| D9 | 2026-11-02 | Name spellings with no official form (controller, under D2) | readers' proposals | 黒の剣 the Black Sword (not "Blade of Darkness": the sword is named in dialogue, the subtitle stays on the title); ライ・ベルン Leib-Bern (the game's own ［Ｌｅｉｂ－Ｂｅｒｎ］); ユーバウム Yubaum (バ, not ヴァ); ゼフュードル Zephudol ("the man with the wind's name"); ゲーツ Goetz (German naming, cf. Kreutz/Kreutzen); 波動 the Wave; 呪い師 Mystic. |
| D10 | 2026-11-02 | Pilot approval in-game (controller, under D6) | boot the pilot before wave 1, approve from text | Approved from text (style-reference); the in-game look of box English needs the phase-7 box distribution in insert, so the first boot of translated boxes is phase 7. |
