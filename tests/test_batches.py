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


def test_glossary_gate():
    """Binding terms beyond names (phase-6 review): real misses fail, grammatical variants pass."""
    rows, _ = batches.glossary()
    def errs(jp, en, form="narration", uid="t"):
        u = dict(id=uid, speaker="", form=form, limit=336, jp=jp)
        return [e for e in batches.check_unit(u, en, rows)[0] if "glossary" in e or "honorific" in e]
    # a name split over a source line break keeps its honorific (07CSL01A:aeb)
    assert errs("領主ユーバ / ウム公爵様の、ご意志", "the will of the lord, Duke Yubaum himself.")
    assert not errs("領主ユーバ / ウム公爵様の、ご意志", "the will of our lord, Duke Yubaum-sama.")
    # the quoted concept needs the quoted form; "the demonic power" nearby does not satisfy it (25TOU00B:c51)
    assert errs("魔の力を受け取り『魔』 / そのものと化せ。", "take the demonic power and become a 'demon' yourself.")
    assert not errs("魔の力を受け取り『魔』 / そのものと化せ。", "take the demonic power and become 'the demonic' itself.")
    assert errs("《黒竜》以上の『魔』", "a 'demon' worse than the Black Dragon")   # was only a warning
    # legitimate variants: article, plural, kanji compound, the skill name inside a verb
    assert not errs("２つの古代都市。", "The two ancient cities.")
    assert not errs("ヒドラの骨を加工して作られた短剣", "A dagger crafted from hydra bone.", "desc")
    assert not errs("体から力が抜けてしまう！", "Just walking drains the strength out of me!")
    assert errs("《抜け》を習得した。", "Learned Nuke.")
    assert not errs("剣士の意志", "the swordsman's Will")


def test_glossary_ok_entries_still_needed():
    """Every reviewed exception in data/glossary_ok.tsv still masks a real miss (no stale lines)."""
    rows, _ = batches.glossary()
    by = {e["id"]: e for _p, d in batches.load_files() for e in d["entries"]}
    ok = dict(batches.GLOSSARY_OK)
    units = {u["id"]: u for u in batches.units()}
    try:
        batches.GLOSSARY_OK.clear()
        for uid, terms in ok.items():
            got = " ".join(batches.check_unit(units[uid], by[uid]["en"], rows)[0])
            for t in terms:
                assert f"glossary: {t} ->" in got, (uid, t)
    finally:
        batches.GLOSSARY_OK.update(ok)
