import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

BIN = ROOT / "rom" / "Kuro no Ken - Blade of the Darkness (Japan).bin"


def test_rom_sha1_lists_the_bin():
    lines = [l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    assert len(lines) == 1 and len(lines[0].split(None, 1)[0]) == 40


@pytest.mark.skipif(not BIN.exists(), reason="no dump in rom/")
def test_dump_matches_pin():
    check_rom.check()
