# Kuro no Ken: Blade of the Darkness (PS1, SLPS-01030) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/kuro_en.cue/.bin (checks the dump against `rom.sha1`, unpacks to `work/orig/tree` once, edits a copy in `work/build/tree`, mkpsxiso; ~2 s)
- Text:     `python -X utf8 tools/extract.py dump` (script/ JSON; never clobbers `en`), `... check` (roundtrip + coverage gate), `... gaps` (what the untouched SCN bytes are); SCN codec `python -X utf8 tools/scn.py check|roundtrip|dis FILE [start end]`
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/kuro_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke` (original: `python tools/orig_cue.py`, then the same on `work/orig/kuro.cue`)
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/kuro_en.cue --out work/qa/warp --route tools/routes/boot.txt --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 40000` (cold boot, plays the intro, ~20000 frames; ends at the proof shot). Faster: `--state-in work/states/base_kuro_en.sstate` instead of `--route` (made by the tour). Scenes: `tools/debug/scenes.lua`, notes `docs/re/scenes.md`. Never ask the user to play to a scene.
- Tour:     `python -X utf8 tools/debug/tour.py --cue build/kuro_en.cue --jobs 4` (every scene; cold boot once, then the base state; proofs + sheets in `work/qa/tour/`)
- Release:  `python -X utf8 tools/release.py` (xdelta vs the .bin + verify; phase 9; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)
- Hooks:    `git config core.hooksPath tools/hooks` once per clone.

## Paths
- Original disc: `rom/Kuro no Ken - Blade of the Darkness (Japan).bin` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Its .cue names a different .bin, so use `tools/orig_cue.py`.
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 30141.20261101.10 x64, via `fetch_emu.py pcsx` from distrib.app; gitignored; emu.py sets its settings per run). BIOS: `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Savestates: `work/states/`.
- Disc/asm tools (gitignored, sources in `docs/re/README.md`): `tools/mkpsxiso/` (dumpsxiso, mkpsxiso 2.30), `tools/armips/`. Unpacked original: `work/orig/tree/` (+ `layout.xml`), archives `work/orig/mps/` (`tools/mps.py`), images `work/orig/gfx/` (`tools/pad.py sweep`).
- Text: `script/` (format: phase 4). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Japanese game: confirm is circle (`--mash-key circle`). Title appears ~frame 2700 from cold boot; Start there begins a new game.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
