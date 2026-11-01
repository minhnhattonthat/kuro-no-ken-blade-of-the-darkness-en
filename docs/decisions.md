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
| D11 | 2026-11-02 | Text over today's fixed sizes (banners, choices, menu labels, item names, system lines) (controller, under D4) | shorten to fit now, write full forms and widen/relocate in phase 7 | Full forms: the check only warns over the JP byte length or window width (hard caps: banner 30, choice 32, item 22, menu 12, sys 40); phase 7 relocates the data runs/pools and widens the windows, else those lines go to a flagged fit pass. Wave 1's first shortened banners were restored. |
| D13 | 2026-11-02 | Credits names and save prompts (controller, under D2/D3/D5) | romanize, keep JP | Credits cards redrawn in English at their own sizes (`tools/gfx.py`, Liberation Sans): cast in Western order (Takehito Koyasu...), roles translated. Staff handles with no known reading are best guesses: 縦線6翠 Tatesen Rokusui, 忍斗丸 Shinotomaru, 圧可冒津 Akka Botsu, アーパーキングA Arper King A, はいぱわーあんなF Hi-Power Anna F, 樹 和 Kazu Itsuki, 軒崎太郎 Taro Nokizaki, 夏生 Natsuki; 妣虎 is Hiko. Save prompts (WIN02) in the game's own font: "Save to which file?" etc.; words start on a tile column because the image may not grow past its 120 tiles (more froze the boot). |
| D12 | 2026-11-02 | Menu labels that no widening can hold (controller, under D4/D11) | widen everything, flagged short forms | Widened where the layout allows (main menu 17 units, shop menus, `tools/asm/menus.asm`). Battle command column: the status box sits left of it, so 6 units = 5 chars: Fight, Magic, Guard, Item, Arms, Flee, Skill. Config: Text Speed / Text Display, Slow/Med/Fast at the JP columns (the renderer colours options by column). The battle short forms carry a note in script/exe.json. |
| D14 | 2026-11-02 | BSX files' non-talk Japanese (enemy AI action labels) | translate in place, leave and document | Leave Japanese: proven never read and never drawn (a complete fight with `slot_reads.lua` + `text_draws.lua`; `docs/re/scenes.md`), the player-facing names come from EXE/SMX/SCN, and the archive gate only allows BSX changes inside talk records and `03 01|02|03` refs. The 1,983 runs are 124 distinct AI labels plus `CB 90` record fill, not text. |
