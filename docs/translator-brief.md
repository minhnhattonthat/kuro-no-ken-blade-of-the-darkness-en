# Translator brief - Kuro no Ken: Blade of the Darkness (PS1, 1997)

You translate part of the Japanese script of Kuro no Ken, a dark-fantasy RPG, into English for a fan patch. Shinobu,
a reserved young sorceress, carries the cursed Black Sword and looks for a swordsman to entrust it to; Caius, a
laid-back but sharp swordsman, crosses her path. Work only on the batches named in your dispatch, one at a time in
the order given, each to a passing check before the next. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (`JP<TAB>EN<TAB>section[<TAB>AVOID ...]`; full
   table in `glossary.md` if you need more).
3. `docs/synopsis.md` - plot, who is who and the late reveals. Don't give a reveal away early; keep early lines
   consistent with what comes later. Read the part that covers your batch's files (area code = file prefix).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`, in story order (use neighbours for context).
- `/` separates the JP's lines; JP breaks lines mid-word (`注意 / を`), so read the unit as one text.
- form:
  - `dlg` - one message page with a name label above it (the speaker column). Translate the page as one utterance.
  - `cont` - the next page of the same speech, no name label shown (the JP sentence runs over the page break; the
    speaker column is the speaker of the previous page). Read it together with the unit before it. You may move
    words between a `dlg` and its `cont` pages so each page ends at a natural point; the order of ideas must hold.
  - `narration` - a page with no name label: narration, signs, item messages, and unnamed NPCs (shopkeepers,
    townsfolk) speaking in 「」.
  - `vis` - a caption of a visual (cutscene) scene; the speaker is shown separately. Up to 4 lines of 62 chars.
  - `choice` - a choice option or a short text the game stores at a fixed size: hard limit `Nch` characters.
  - `banner` - a place-name banner, hard limit `Nch`.
  - `item` (item/skill name, max 18), `desc` (item/skill description, 2 lines of 22), `menu` (menu label, max 6),
    `sys` (system/battle message, max 26).
- limit: `2pg` = aim for at most 2 pages (hard limit 3); the others are hard limits.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain printable ASCII: straight quotes, `...`, `--`; no
tabs inside the English, no Japanese or full-width characters, no `\uXXXX`, no `@`, no double spaces. Never write
`\n` or other backslash codes in dlg/cont/narration/vis text: the insert tool wraps lines and pages itself. In `menu`,
`sys`, `item`, `desc`, `choice`, `banner` units copy any backslash code in the JP (`\e`, `\x48`) exactly, in place.

## Page geometry (field message box)
28 characters a line (27 on a page's last line), 4 lines a page; on a `dlg` page the name label takes the first line,
so the first page holds 3 lines (~80 chars), later pages 4 (~110). Text past a page continues on a new page
automatically. Preview any unit with
`python -X utf8 tools/batches.py fit dlg "your text"` (or `cont`, `narration`, `vis`, `desc`). Avoid a last page that
holds one short line (the check warns "stub page"): rephrase tighter, or move words to the neighbouring `cont` unit.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every ERROR until it prints OK. Fix the
`stub page` warnings too unless tightening would lose meaning.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Keep the speaker audible. JP register markers carry voice and must turn into English devices, not vanish:
  old men's じゃ/のう/わし ("eh?", "my boy", "back in my day"), rough men's ぜ/ねぇ/っス ("ain't", "ya", "dammit",
  clipped grammar), feminine かしら/わよ/のね ("I wonder...", "you know"), merchants' patter, soldiers' stiffness.
  A line any speaker could have said is a mistake. Voices per character: `docs/style-reference.md`.
- Names and terms exactly as in the glossary. Never abbreviate a name or term to fit; if a unit can't fit its hard
  limit without losing meaning, keep the meaning and report it as `LONG: id`.
- Honorifics are kept, hyphenated (`Caius-san`, `Shinobu-sama`); Western name order (given name first).
- Punctuation: 「...」 -> "..." (keep the quotes; a `cont` page has no opening quote if the JP has none, and closes
  the quote only where the JP does). 『...』 -> '...' for a quote inside speech or a written notice, 《X》 (item, spell,
  art names) -> plain name with capitals, no brackets: 《通行証》 -> the Pass. ・・・ -> `...`, a silent
  「・・・・・・」 -> `"......"`, ！？ -> `?!`, ～ (drawn-out sound) -> repeat the vowel or use an exclamation, not `~`.
- Item messages: 《X》を受け取った。 -> `Received the X.`; 〜を手に入れた -> `Obtained ...`; keep them short and
  uniform across the game.
- Numbers: write digits as the JP does (５割引き -> "half off" is fine when idiomatic).
- Repeated NPC lines (the same JP in several town states) get the same English each time.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Notes from earlier batches
- (pilot) Most `dlg` pages run over one page in English; that is fine. Keep a page from ending on a 1-2 word stub.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
