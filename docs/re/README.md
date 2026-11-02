# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [archives.md](archives.md) | disc layout, PSMG `.MPS`, EM containers, mkpsxiso identity | verified (roundtrip tests) |
| [text.md](text.md) | SJIS, SCN bytecode + op 0x3b, escapes, MES, SMX, EXE strings, SCN rebuild + relocation, insertion rules (in place vs relocate, data runs) | verified (roundtrip + rebuild tests, phases 4-5) |
| [font.md](font.md) | SYSTEM.FNT header + code list, full-width (base-6) and half-width (3 bpp) glyph formats, the two renderers, window metrics | verified (decoder + in-game dumps) |
| [graphics.md](graphics.md) | PAD30 format, static sweep, graphics-text list G1-G5 | verified format; G4/G5 guesses |
| [scenes.md](scenes.md) | script slots, vars/flags, area change, warp method, VIS, fights, shops | verified by the warp tour |

Prior work (2026-11-01 search): no English or other fan patch for the PS1 or PC-98 version found. Official names
from a review: Shinobu Ryudo (シノブ・リュード), Caius Neinturk (カイエス・ナインターク; EXE spelling).

Tools: `tools/mps.py`, `tools/pad.py`, `tools/re.py` (dis / imm / jt), `tools/fnt.py` (draft), `tools/scn.py`
(SCN codec: `dis`, `check`, `roundtrip`, plus `assemble`/`rebuild` for insertion and `tests/test_extract.py`
for the proof), `tools/sctext.py` (text codec), `tools/extract.py` (`dump` / `check`: every string of the game into
`script/`), `tools/debug/` (warp, tour, probes: dump_at, watch_pos,
trace_ops, probe_scene, ai_probe (BSX battle-talk records/handlers), cd_seeks (CD Setloc log, needs `--debugger`);
`gen_scenes.py` regenerates `scenes_data.lua`).
External tools (gitignored, fetch again into `tools/`): mkpsxiso/dumpsxiso 2.30 (github.com/Lameguy64/mkpsxiso
releases, win64 zip), armips 0.11.0 (github.com/Kingcom/armips releases). jPSXdec 2.1 (github.com/m35/jpsxdec)
for STR work: `tools/jpsxdec/` (the 2.1-beta zip unpacked; needs Java 8+), used by `tools/fmv.py` from the build.
