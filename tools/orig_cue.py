"""orig_cue.py: write work/orig/kuro.cue pointing at the pinned rom/ .bin (the dump's own cue names another file).

    python tools/orig_cue.py   # then: emu.py work/orig/kuro.cue ..."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CUE = ROOT / "work" / "orig" / "kuro.cue"
CUE.parent.mkdir(parents=True, exist_ok=True)
CUE.write_text('FILE "../../rom/Kuro no Ken - Blade of the Darkness (Japan).bin" BINARY\n'
               "  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n", encoding="ascii")
print(CUE)
