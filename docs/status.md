# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** Step 0 (repo setup) done 2026-11-01. Next: phase 1 (research and recon). No build yet.
- **Done:**
  - Template files in place; AGENTS.md filled; decisions D1-D7 recorded from the owner's run brief; glossary rulings set.
  - Dump pinned in `rom.sha1` (bin only; the dump's cue names `... [SLPS-01030].bin`, so `tools/orig_cue.py` writes `work/orig/kuro.cue`).
  - PCSX-Redux nightly 30141 in `tools/pcsx/`, SCPH-5500 BIOS in `tools/bios/`. Original cold-boots (CD BROS. logo, prologue text, title with NEW GAME/LOAD GAME/OPTION at ~frame 2700); Start on title -> "Now Loading" (scripted input ok); a `--script` probe's `L.log` lands in log.txt.
  - Guard hook (plugin) blocks `sed -i` canary. Pre-commit (`tools/hooks/`, `core.hooksPath`) runs `tools/check.py` and rejected a commit with a failing test.
  - `tools/`: tbl.py, bps.py, romdiff.py copied from the skill; skill.py; check.py; tests/test_rom.py.
- **Next (phase 1):** recon per skill `references/pipeline.md` §Recon + `platform-ps1.md`: list the ISO9660 files (no mkpsxiso/dumpsxiso installed yet: fetch from github.com/Lameguy64/mkpsxiso releases into `tools/mkpsxiso/`; armips too for phase 5), find SLPS_010.30 EXE, archive formats, text encoding (title prologue is SJIS-looking kana/kanji, white text), pointer tables, font, graphics-text survey (title logo 黒の剣, menu NEW GAME/LOAD GAME/OPTION already English, "Now Loading" English). Look for earlier fan patches first.
- **Open bugs:** none.
- **Not verified:** GUI keyboard input in `tools/pcsx/` (headless-only run, no person to press keys). The Japanese title logo image text and prologue are graphics/text to survey.
- **Waiting on the user:** nothing.
