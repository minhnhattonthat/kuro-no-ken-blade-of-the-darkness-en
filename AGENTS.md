# Kuro no Ken: Blade of the Darkness (PS1, SLPS-01030) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/kuro_en.cue/.bin (checks the dump against `rom.sha1` first; not written yet, phase 3)
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/kuro_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke` (original: `python tools/orig_cue.py`, then the same on `work/orig/kuro.cue`)
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/kuro_en.cue --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.lua`; phase 2; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py` (xdelta vs the .bin + verify; phase 9; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)
- Hooks:    `git config core.hooksPath tools/hooks` once per clone.

## Paths
- Original disc: `rom/Kuro no Ken - Blade of the Darkness (Japan).bin` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Its .cue names a different .bin, so use `tools/orig_cue.py`.
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 30141.20261101.10 x64, via `fetch_emu.py pcsx` from distrib.app; gitignored; emu.py sets its settings per run). BIOS: `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Savestates: `work/states/`.
- Text: `script/` (format: phase 4). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Japanese game: confirm is circle (`--mash-key circle`). Title appears ~frame 2700 from cold boot; Start there begins a new game.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
