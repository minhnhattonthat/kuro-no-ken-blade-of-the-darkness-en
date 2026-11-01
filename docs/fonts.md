# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/LiberationSans-Bold.ttf (+ Regular, licence `fonts/LiberationSans-LICENSE.txt`) | github.com/liberationfonts/liberation-fonts, 2.1.5 | SIL OFL 1.1 | yes, as rendered glyphs | credits cards KRED00-14 (`tools/gfx.py`, Bold); prologue FMV text (`tools/fmv.py`, Regular 15 px) | none |
| SYSTEM.FNT half-width glyphs (the disc's own) | the game | the game's | ships as the game's own bytes; the patch adds punctuation drawn for this project | field/menu ASCII, VIS captions, WIN02 save prompts | `fnt.PATTERNS` punctuation added |
