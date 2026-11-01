"""Identity build: repacking the unedited dump's tree gives the pinned sha1 (keep green forever)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402


@pytest.mark.skipif(not (build.ORIG / "tree" / "SLPS_010.30").is_file() or not build.MKPSXISO.is_file(),
                    reason="no unpacked dump (run tools/build.py once) or no mkpsxiso")
def test_identity_repack(tmp_path):
    want = next(l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")).split()[0].lower()
    assert build.sha1(build.repack(build.ORIG, tmp_path / "id.bin")) == want
