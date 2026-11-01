"""Phase 5: insertion (marker build) — the SCN text path a build writes through, and the font codec."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fnt      # noqa: E402
import insert   # noqa: E402
import mps      # noqa: E402
import scn      # noqa: E402

TREE = ROOT / "work" / "orig" / "tree"
FNT = ROOT / "work" / "orig" / "mps" / "SYS" / "SYSTEM.FNT"
have_data = pytest.mark.skipif(not (TREE / "SCN.MPS").exists(), reason="no unpacked disc tree")


def members(name):
    _start, ents = mps.read((TREE / name).read_bytes())
    return {n: b for n, _o, b in ents}


@have_data
def test_marker_insert_keeps_every_file_the_same_size():
    """Marker mode rewrites text in place: no SCN file may change length, or moved blocks break pointers the
    codec does not relocate (the reason phase 5 first hung on "Now Loading")."""
    before, after = members("SCN.MPS"), {}
    entries = {rel.split("/")[-1][:-5]: e for rel, e in insert.load() if rel.startswith("scn/")}
    for name, blob in before.items():
        stem = name[:-4]
        new, _notes, _moved = insert.scn_insert(blob, scn.base_of(stem), entries.get(stem, []), True,
                                                name=name, relocate=False)
        after[name] = new
        assert len(new) == len(blob), f"{name} changed size in marker mode"
        assert not (set(scn.walk(new, scn.base_of(stem))[1]) - set(scn.walk(blob, scn.base_of(stem))[1])), \
            f"{name} no longer walks cleanly"
    assert sum(1 for n, b in before.items() if b != after[n]) > 100, "too few files got a marker"


@have_data
def test_relocation_grows_a_message_and_keeps_the_walk_clean():
    """A message op on the walked path may grow: the file is rebuilt and every address operand relocated."""
    blob = members("SCN.MPS")["02OLB01A.SCN"]
    base = scn.base_of("02OLB01A")
    entries = [e for rel, es in insert.load() if rel == "scn/02OLB01A.json" for e in es]
    longest = max(entries, key=lambda e: int(e["ptr"], 16))
    grow = longest["jp"] + " (a much longer English line goes here)"
    for e in entries:
        e["en"] = grow if e["id"] == longest["id"] else ""
    new, _notes, moved = insert.scn_insert(blob, base, entries, False, name="02OLB01A.SCN", relocate=True)
    assert moved >= 1
    assert len(new) > len(blob)
    assert not set(scn.walk(new, base)[1]) - set(scn.walk(blob, base)[1])


@have_data
def test_data_runs_inside_the_bytecode_are_not_written():
    """02OLB:159 is an op (and its jump) the file scan mistook for kana text: writing a marker there hangs the
    intro. The extractor no longer takes it (no real Japanese in it), and the marker insert leaves it alone."""
    blob = members("SCN.MPS")["02OLB.SCN"]
    base = scn.base_of("02OLB")
    entries = [e for rel, es in insert.load() if rel == "scn/02OLB.json" for e in es]
    assert "02OLB:159" not in {e["id"] for e in entries}
    for relocate in (True, False):
        new, _notes, _moved = insert.scn_insert(blob, base, entries, True, name="02OLB.SCN", relocate=relocate)
        assert new[0x159:0x160] == blob[0x159:0x160]


@have_data
@pytest.mark.skipif(not FNT.exists(), reason="no SYSTEM.FNT")
def test_font_codec_roundtrip():
    """The half-width rows decode and re-encode byte for byte; the full-width rows are 12 base-6 digits."""
    data = FNT.read_bytes()
    for code in range(0x20, 0x7F):
        rows = fnt.ascii_rows(data, code)
        assert fnt.ascii_bytes(rows) == data[fnt.ASCII + 36 * code:fnt.ASCII + 36 * code + 36]
    i = fnt.codes(data).index(0x88EA)          # 一: one bright row in the middle
    rows = fnt.sjis_rows(data, i)
    lit = [(y, x) for y in range(12) for x in range(12) if rows[y][x]]
    assert {y for y, _x in lit} == {6}, lit


def test_bsx_insert_ref_forms():
    """Battle talk records are reached by `03 01|02|03 <u16>` with any trailing byte; a longer English record
    moves past the end and its ref follows it; a record nothing references keeps its JP."""
    import struct
    jp1, jp2 = "「ああ」".encode("cp932"), "「いい」".encode("cp932")
    head = b"\x03\x02\x10\x00\x05" + b"\xff" * 11                  # ref to 0x10, trailing 05
    rec1 = b"\x01B00010\x00" + jp1 + b"\x00"
    rec2 = b"\x01B00020\x00" + jp2 + b"\x00"                       # no ref
    out, notes, n = insert.bsx_insert(head + rec1 + rec2, {jp1: b"Long English line", jp2: b"x"}, "T")
    assert n == 1 and any("no reference" in s for s in notes)
    at = struct.unpack_from("<H", out, 2)[0]
    assert out[at:at + 7] == b"\x01B00010" and b"Long English line\x00" in out[at:]
    assert rec2 in out
