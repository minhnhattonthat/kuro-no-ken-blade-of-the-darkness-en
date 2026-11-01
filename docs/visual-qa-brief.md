# Visual-QA reviewer brief - Kuro no Ken: Blade of the Darkness (PS1)

You review screenshots from the English build's QA tour (one proof PNG per scene, 320x240 or 640x480) and give
each one a verdict. Read-only on everything except your one verdict file: no edits to the repo, no git, no
subagents.

## Inputs (in your dispatch)
- A chunk file: one line per screenshot (its path). Read every one; none may be skipped. The id of a shot is its
  file name without `.png` (e.g. `work/qa/v8/scenes/02olb_1.png` -> `02olb_1`).
- Your verdict file: `work/qa/v8/verdicts/<chunk>.tsv`.
- The original Japanese disc's shots of the same scenes: `work/qa/tour/<id>.png` (same names; the new scenes
  `save_slot`, `load_slot`, `ending_credits` have none). `glossary.md` for names.

## How to look
- Read each shot whole first. Where text is small, zoom into it:
  `python -X utf8 "$(python tools/skill.py)/scripts/sheet.py" SHOT.png --crop x,y,w,h --zoom 3 --out <scratch>.png`
  and read that (scratch = a file under your session's temp/scratchpad dir, never inside the repo).
- When something looks wrong, compare with the original: `sheet.py EN.png --compare work/qa/tour/<id>.png --out ...`.
  If the original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible (kana/kanji in a box, menu, banner or caption);
- text overflowing a box, clipped by a frame, or running off screen;
- garbage glyphs, wrong or missing letters, stray pixels across letters;
- broken line breaks: a word split mid-line, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map still loading after a warp, a black or empty screen in an area scene (warps use entrance 0, so some open
  on an empty corner or black: 02OLB dock, 05SKS);
- the ending / credits scenes showing tile garbage over their backdrops (a warp limit, also on the original);
- anything identical in the original's shot;
- the title logo 黒の剣 (kept Japanese by decision D5); the copyright lines and "END", already English on the disc.
- English using the game's 8 px fixed-width font with wide gaps around narrow letters (i, l): that is the font.

## Verdicts
Write your verdict file once you have read every shot, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which part of the screen, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
