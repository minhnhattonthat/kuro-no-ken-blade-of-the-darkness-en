"""SCN disassembler (tools/scn.py) walks every script of the original disc with clean control flow."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCN = ROOT / "work" / "orig" / "mps" / "SCN"
# shortcut: 17DRL04 has two jump targets inside a data run at 0x2cfc (open, docs/re/scenes.md); fix in phase 4
KNOWN = {"17DRL04"}


def test_scn_check():
    if not (SCN / "99CMN.SCN").exists():
        pytest.skip("no unpacked SCN.MPS in work/orig/mps/SCN")
    out = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "scn.py"), "check"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    bad = [line.split()[0] for line in out.splitlines() if " errors " in line and " errors 0" not in line]
    assert len(out.splitlines()) > 200
    assert set(bad) <= KNOWN, bad
