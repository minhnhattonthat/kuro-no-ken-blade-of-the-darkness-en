"""PSMG (.MPS) and PAD30 readers against the original disc's files (docs/re/archives.md, graphics.md)."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mps  # noqa: E402
import pad  # noqa: E402

BIN = ROOT / "rom" / "Kuro no Ken - Blade of the Darkness (Japan).bin"
TREE = ROOT / "work" / "orig" / "tree"


@pytest.fixture(scope="module")
def tree():
    if not BIN.exists():
        pytest.skip("no dump in rom/")
    if not (TREE / "SCN.MPS").exists():
        cue = subprocess.check_output([sys.executable, str(ROOT / "tools" / "orig_cue.py")], text=True).strip()
        subprocess.check_call([str(ROOT / "tools" / "mkpsxiso" / "dumpsxiso.exe"), "-x", "tree", "-s", "layout.xml",
                               cue], cwd=TREE.parent, stdout=subprocess.DEVNULL)
    return TREE


def test_every_mps_repacks_byte_identical(tree):
    files = sorted(tree.glob("*.MPS"))
    assert len(files) == 10
    for p in files:
        data = p.read_bytes()
        start, ents = mps.read(data)
        out = mps.write([(n, b) for n, _, b in ents], start, len(data))
        assert out + bytes(len(data) - len(out)) == data, p.name


def test_pad30_known_sizes(tree):
    _, ents = mps.read((tree / "SYS.MPS").read_bytes())
    files = {n: b for n, _, b in ents}
    h = pad.pad_info(files["KRED01.PAD"])
    assert (h["cols"] * h["ts"], h["rows"] * h["ts"], h["bpp"]) == (128, 112, 8)
    assert pad.render(files["WIN02.PAD"]).size[0] > 0
