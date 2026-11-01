# Kuro no Ken: Blade of the Darkness English translation

Unofficial English fan translation of **Kuro no Ken: Blade of the Darkness** (PlayStation, 1997, SLPS-01030): the
source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a memory
card file helps most.

## Translation status

| Part | Status |
|---|---|
| Field dialogue, story cutscenes, battle talk | Translated |
| Menus, items, equipment, magic and sword arts, battle and system messages | Translated |
| Opening prologue movie, staff credits, save/load prompts | Translated (re-encoded / redrawn) |
| Title logo | Left in Japanese (no official English logo) |
| Memory card file title (BIOS screen) | Left in Japanese |

Known issues: see [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched disc image

Needs Python 3.12+, mkpsxiso/dumpsxiso and armips (see `docs/re/README.md`), Java for the prologue movie, and your
own dump of the Japanese disc.

```sh
git clone https://github.com/minhnhattonthat/kuro-no-ken-blade-of-the-darkness-en
cd kuro-no-ken-blade-of-the-darkness-en
# copy your dump to: rom/Kuro no Ken - Blade of the Darkness (Japan).bin
#   (387,332,064 bytes, SHA-1 c25cc53906afe6c0bc6d1068b5f445862c540ddc; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/kuro_en.bin + .cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` belongs to the game's rights holders and
is included only so the translation can be checked against it. Kuro no Ken: Blade of the Darkness is (c) its rights
holders; this project is not affiliated with them. Do not share patched disc images.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
