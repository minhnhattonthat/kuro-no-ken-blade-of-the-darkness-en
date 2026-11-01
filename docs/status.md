# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (research and recon) done 2026-11-01. Next: phase 2 (debug tool). No build yet.
- **Done:**
  - Step 0: template, decisions D1-D7, dump pinned, PCSX-Redux + BIOS, hooks (see git history).
  - Phase 1: no earlier fan patch exists (PS1 or PC-98). Recon notes in `docs/re/` (index `README.md`):
    disc + PSMG/EM archives (verified, `tests/test_archives.py`), SCN bytecode interpreter + op 0x3b message +
    operand readers + escapes, MES and SMX formats, EXE string ranges, SYSTEM.FNT structure, PAD30 image format,
    static graphics sweep (472 images) with the graphics-text list G1-G5 in `docs/re/graphics.md`.
  - `mkpsxiso -y layout.xml` on the unedited dump already gives the pinned sha1 (phase 3 just wires it as a test).
  - Tools: `tools/mps.py`, `pad.py`, `re.py`, `sjstr.py`, `fnt.py` (draft). mkpsxiso/dumpsxiso 2.30 and armips
    0.11.0 in `tools/` (gitignored).
- **Next (phase 2, debug tool):** reach every scene from a cold boot. Leads: the script interpreter (pointer
  0x80088fd4, dispatch 0x8002c8c0) and the scene loader: find where a SCN name is chosen (scene ids like
  `02OLB01A`), then warp by writing the next-scene name/id before a load; story flags are the u16 variables
  read by value type 1 (0x8002c09c, base around 0x80094120, guess). `DBUGFON.TIM` hints at a leftover debug menu:
  find its users. Scene list = the 218 SCN names + VIS00-20 scenes + battle + ending (31END) + credits (KRED).
- **Later phases, known work:** SCN bytecode parser with address relocation (phase 4); font glyph format
  undecoded, no ASCII glyphs (phase 5); credits KRED00-15 and WIN02 as images; boot prologue probably in
  LOGO.STR (FMV).
- **Open bugs:** none.
- **Not verified:** GUI keyboard input in `tools/pcsx/`. Whether file growth (LBA shift) is safe (phase 3 test).
- **Waiting on the user:**
  - (non-blocking) Running the downloaded jPSXdec jar (`work/dl/jp/`) was refused by the auto-mode permission
    check; needed later to decode/re-encode LOGO.STR if the prologue is FMV. A permission rule for
    `java -jar tools/jpsxdec/jpsxdec.jar` would unblock it.
  - (non-blocking) Title logo 黒の剣: default keep (D5); the disc's volume id is BLADE_OF_THE_DARKNESS
    (official English subtitle), so an English subtitle line under the logo is the fallback plan.
