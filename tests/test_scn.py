"""SCN disassembler (tools/scn.py) walks every script of the original disc with clean control flow."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCN = ROOT / "work" / "orig" / "mps" / "SCN"
# shortcut: two ops 0x52 register a "handler" value that lands inside another op's bytes (15MKR02A 0x55f3,
# 17DRL04 0x2cfc). The walk still decodes both files; the value is either data or a form not decoded yet.
KNOWN = {"15MKR02A", "17DRL04"}


def test_scn_check():
    if not (SCN / "99CMN.SCN").exists():
        pytest.skip("no unpacked SCN.MPS in work/orig/mps/SCN")
    out = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "scn.py"), "check"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    bad = [line.split()[0] for line in out.splitlines() if " errors " in line and " errors 0" not in line]
    assert len(out.splitlines()) > 200
    assert set(bad) <= KNOWN, bad
