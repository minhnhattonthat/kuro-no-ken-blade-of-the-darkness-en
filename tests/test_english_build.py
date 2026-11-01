"""Phase 7: the English build from the current script/, into a temp tree (never build/ or work/build/).

build.edit() raises on any string that does not fit, on an EXE byte outside the allowed ranges or the write
journal (romdiff.py --writes), and on a tools/gate.py problem in the archives; the tests below also show the gate
catching what it claims to."""
import shutil
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build    # noqa: E402
import gate     # noqa: E402
import insert   # noqa: E402
import mps      # noqa: E402

TREE = build.ORIG / "tree"
pytestmark = pytest.mark.skipif(not (TREE / "SCN.MPS").is_file() or not build.ARMIPS.is_file(),
                                reason="no unpacked dump (run tools/build.py once) or no armips")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tree = tmp_path_factory.mktemp("en") / "tree"
    shutil.copytree(TREE, tree)
    argv, sys.argv = sys.argv, ["build.py"]          # edit() reads its flags from argv
    try:
        build.edit(tree)
    finally:
        sys.argv = argv
    return tree


def members(path):
    return {n: b for n, _o, b in mps.read(Path(path).read_bytes())[1]}


def test_english_build_passes_every_gate(built):
    assert gate.check(TREE, built) == []
    assert len(insert.EXE_WRITES) > 100              # the EXE strings and their pointers went through the journal
    assert insert.WIDOWS == [], "field paragraphs ending in a stub line (< insert.STUB chars): rephrase them"


def test_flow_pulls_a_word_down_onto_a_stub_last_line():
    """02OLB01:90d ended `...was\\nI?"` (greedy wrap); same line count, so the page breaks do not move."""
    text, line = insert.flow('"...So I was your decoy, was I?"', 1)
    assert text == '"...So I was your decoy,\\nwas I?"' and line == 2


def test_gate_flags_a_file_the_build_does_not_edit(built):
    p = built / "SYSTEM.CNF"
    keep = p.read_bytes()
    try:
        p.write_bytes(keep + b" ")
        assert any("SYSTEM.CNF: changed" in e for e in gate.check(TREE, built))
    finally:
        p.write_bytes(keep)


def test_gate_flags_member_damage(built):
    orig, new = members(TREE / "SYS.MPS"), members(built / "SYS.MPS")
    x, y = orig["ITEM.SMX"], bytearray(new["ITEM.SMX"])
    y[insert.SMX_REC + 8] ^= 1                       # a record byte that is not a string slot
    assert gate.member("smx", "ITEM.SMX", x, bytes(y), []), "SMX record damage not seen"
    b = members(built / "BSX.MPS")
    name = next(n for n, blob in members(TREE / "BSX.MPS").items() if blob != b[n])
    x, y = members(TREE / "BSX.MPS")[name], bytearray(b[name])
    y[0] ^= 1                                        # the file header, outside every talk record
    assert gate.member("bsx", name, x, bytes(y), []), "BSX damage outside talk records not seen"
    x = members(TREE / "VIS.MPS")
    name = next(iter(x))
    y = bytearray(x[name])
    struct.pack_into("<H", y, 0, struct.unpack_from("<H", y, 0)[0] + 2)
    assert gate.member("mes", name, x[name], bytes(y), []), "MES header change not seen"


def test_gate_flags_japanese_left_behind():
    """An entry whose Japanese is still in its file, with no English beside it, is reported."""
    e = next(e for rel, es in insert.load() if rel.startswith("scn/") for e in es
             if insert.text_of(e, False) and len(insert.encode(e["jp"], "scn")) >= 8)
    jp = insert.encode(e["jp"], "scn")
    assert gate.jp_left("scn", b"\0" + jp + b"\0", [e]) == [e["id"]]
    assert gate.jp_left("scn", b"\0", [e]) == []
