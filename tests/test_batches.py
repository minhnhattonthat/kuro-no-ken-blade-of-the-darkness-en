import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402


def test_units_cover_every_entry_once():
    seen = []
    for u in batches.units():
        seen += u["ids"]
    every = [e["id"] for p in sorted((ROOT / "script").rglob("*.json"))
             for e in json.loads(p.read_text(encoding="utf-8"))["entries"]]
    assert len(seen) == len(set(seen))
    assert set(seen) == set(every)


def test_box_members_hold_no_english():
    """English for a box lives in its first entry; the other entries are empty (status box)."""
    idx = {e["id"]: e for p in (ROOT / "script").rglob("*.json")
           for e in json.loads(p.read_text(encoding="utf-8"))["entries"]}
    for u in batches.units():
        for eid in u["ids"][1:]:
            assert not idx[eid]["en"], eid


def test_pages():
    pg = batches.pages("word " * 40, True)
    assert len(pg[0]) == 3 and all(len(p) <= 4 for p in pg)
    for p in pg:
        assert all(len(x) <= 28 for x in p) and len(p[-1]) <= 27 or p is pg[-1]


def test_check_unit():
    rows = [("Characters", "シノブ", "Shinobu", "Shinobi")]
    u = dict(id="x", speaker="", form="dlg", limit=2, jp="「シノブさん」")
    errs, _ = batches.check_unit(u, '"Shinobi-san"', rows)
    assert any("glossary" in e for e in errs) and any("honorific" in e for e in errs)
    errs, _ = batches.check_unit(u, '"Shinobu-san"', rows)
    assert not errs
    errs, _ = batches.check_unit(u, 'a\\nb  c', rows)
    assert len(errs) >= 2
