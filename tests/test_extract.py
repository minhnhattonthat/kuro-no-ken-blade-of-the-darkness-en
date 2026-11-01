"""Phase 4: extraction roundtrip and coverage over the original data, and the SCN rebuild/relocation machinery."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import scn      # noqa: E402
import sctext   # noqa: E402

SCN = ROOT / "work" / "orig" / "mps" / "SCN"
have_data = pytest.mark.skipif(not (SCN / "99CMN.SCN").exists(), reason="no unpacked SCN.MPS")


@have_data
def test_extract_roundtrip_and_coverage():
    """Every extracted string re-encodes to its original bytes, and no message op or spoken run is left out."""
    assert extract.check() == []


@have_data
def test_scn_reassemble_identical():
    assert scn.roundtrip() == 0


@have_data
def test_codec_byte_exact():
    """The codec is byte-exact for every string of every SCN file, escapes and raw control bytes included."""
    bad = []
    for f in sorted(SCN.glob("*.SCN")):
        b = f.read_bytes()
        base = scn.base_of(f.stem)
        ops, _ = scn.walk(b, base)
        for a, (op, out, nxt, info) in ops.items():
            for kind, x in out:
                if kind != "s":
                    continue
                if sctext.encode(sctext.decode(x)) != x:
                    bad.append(f"{f.stem}:{a - base:x}")
    assert bad == []


@have_data
@pytest.mark.parametrize("name", ["02OLB01", "03YSK690", "29KNT", "99CMN", "02OLB"])
def test_rebuild_relocates(name):
    """Grow a message, rebuild the file: it still walks cleanly and the jump targets keep landing on ops."""
    b = (SCN / f"{name}.SCN").read_bytes()
    base = scn.base_of(name)
    ops, errs = scn.walk(b, base)
    assert errs == []
    target = next(a for a in sorted(ops) if ops[a][0] == 0x3B and ops[a][1][0][0] == "s")
    op, out, nxt, info = ops[target]
    off = info[0][1]
    text = sctext.decode(out[0][1])
    grown = b"\x3b\x02" + sctext.encode("A" + text) + b"\x00"
    new, problems = scn.rebuild(b, base, ops, edits={off - 2: grown})
    assert problems == []
    assert len(new) == len(b) + 1

    ops2, errs2 = scn.walk(new, base)
    assert errs2 == []
    # the edited message reads back as the grown text
    assert sctext.decode(new[off:off + len(grown) - 3]) == "A" + text
    # every op that was behind the edit moved by one byte, and each jump still lands on an op
    for a in ops:
        if a <= target:
            continue
        assert a + 1 in ops2, f"op {a:#x} did not move"
    for a, (op2, out2, nxt2, info2) in ops2.items():
        for t in scn.targets(op2, out2):
            if base <= t < base + len(new):
                assert t in ops2, f"jump target {t:#x} of op {a:#x} is not an op start"


@have_data
def test_rebuild_all_files():
    """Every SCN file can be re-laid after an edit: three do not, all of them a 0x52 handler value that points
    into data (the form tests/test_scn.py already tolerates). Insertion (phase 7) has to decode that form before
    it may grow text in those files."""
    known = {"15MKR02A", "15MKR02C", "24UMB57"}
    broken = []
    for path in sorted(SCN.glob("*.SCN")):
        b = path.read_bytes()
        base = scn.base_of(path.stem)
        ops, errs = scn.walk(b, base)
        target = next((a for a in sorted(ops) if ops[a][0] == 0x3B and ops[a][1] and ops[a][1][0][0] == "s"), None)
        if target is None:
            continue
        off = ops[target][3][0][1]
        text = sctext.decode(ops[target][1][0][1])
        new, _ = scn.rebuild(b, base, ops, edits={off - 2: b"\x3b\x02" + sctext.encode("A" + text) + b"\x00"})
        if scn.walk(new, base)[1]:
            broken.append(path.stem)
    assert set(broken) <= known, broken


@have_data
def test_mes_line_breaks_are_not_escapes():
    """MES captions break lines with a raw 0x0d; the codec must not read them as the \\n escape."""
    raw = "　はい\rいいえ".encode("cp932")
    assert sctext.decode(raw, nl=0x0D) == "　はい\\nいいえ"
    assert sctext.encode("　はい\\nいいえ", nl=0x0D) == raw
