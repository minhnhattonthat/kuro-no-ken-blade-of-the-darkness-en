# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/LiberationSans-Bold.ttf (+ Regular, licence `fonts/LiberationSans-LICENSE.txt`) | github.com/liberationfonts/liberation-fonts, 2.1.5 | SIL OFL 1.1 | yes, as rendered glyphs | credits cards KRED00-14 (`tools/gfx.py`, Bold); prologue FMV text (`tools/fmv.py`, Regular 15 px) | none |
| fonts/terminus-u12b.bdf (licence `fonts/terminus-LICENSE.txt`) | terminus-font.sourceforge.net, 4.49.1 (ter-u12b) | SIL OFL 1.1 | yes, as rendered glyphs | SYSTEM.FNT half-width 0x21-0x7e: field/menu, VIS captions, WIN02 save prompts (`fnt.patch_ascii`, D15) | drawn at x 1-6 of the 8 px cell, ink value 1 + black shadow 6 to the right |
| SYSTEM.FNT (the disc's own) | the game | the game's | ships as the game's own bytes | full-width glyphs, half-width space | half-width 0x21-0x7e replaced (row above) |
