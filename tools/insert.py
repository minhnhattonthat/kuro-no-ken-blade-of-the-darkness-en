"""insert.py: write the English of script/**/*.json back into the game's data files.

    python -X utf8 tools/insert.py check             # every `en` fits its site (or can move) and encodes
    python -X utf8 tools/insert.py marker DIR        # write [id] marker text for EVERY entry into a tree copy the
                                                     # build made (build.py --marker does this for you)

Encoding (docs/re/font.md, docs/re/text.md): English is written as ASCII bytes; the message renderer draws
them with the half-width font in SYSTEM.FNT (36-byte entries from 0x10, code < 0x80) at 8 px per character.
A SCN message op is `3b 02 <text> 00`. When the op is on the walked path the file is rebuilt with
tools/scn.rebuild(), which relocates every address operand, so English may be longer than the Japanese.
Strings with no op (found by scanning), the fixed-size pools (MES, SMX) and the EXE labels keep their
original byte length: the text is cut there and `check` reports it as a problem.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mps      # noqa: E402
import scn      # noqa: E402
import sctext   # noqa: E402

MPS = ROOT / "work" / "orig" / "mps"
SCRIPT = ROOT / "script"
NL = {"mes": 0x0D}          # MES breaks lines with 0x0d; the rest use the \n escape
ARCH = {"scn": ("SCN.MPS", ".SCN"), "mes": ("VIS.MPS", ""), "smx": ("SYS.MPS", "")}
DATA_RUNS = 0   # 0 = leave non-op text (choice lists, banners) alone: see scn_insert()


def load():
    """[(rel, entries)] for every script JSON, in path order."""
    out = []
    for path in sorted(SCRIPT.rglob("*.json")):
        out.append((path.relative_to(SCRIPT).as_posix(), json.loads(path.read_text(encoding="utf-8"))["entries"]))
    return out


def marker_text(e):
    """`[file:offset]` — the id, short enough to fit most sites, with the JP's own line breaks kept."""
    name = e["id"].split(":")[0]
    return f"[{name}:{e['ptr'][2:]}]"


QA = {}     # id -> text: one-line overrides for width tests (build.py --qa ID=TEXT)


def text_of(e, marker):
    if e["id"] in QA:
        return QA[e["id"]]
    if marker:
        return marker_text(e)
    return e.get("en") or ""


def encode(text, kind):
    return sctext.encode(text, NL.get(kind))


def fit(raw, budget, kind):
    """Cut encoded text to a byte budget, never leaving half an escape or a SJIS lead byte."""
    cut = raw[:budget]
    while cut and (cut[-1] == 0x5C or 0x81 <= cut[-1] <= 0x9F or 0xE0 <= cut[-1] <= 0xFC):
        cut = cut[:-1]
    return cut


def pool_start(b, kind):
    import extract
    return extract.pool_start(b, kind)


def scn_insert(b, base, entries, marker, name="", relocate=True):
    """(new bytes, notes, relocated count) for one SCN file.

    Message ops on the walked path are rebuilt through scn.rebuild(), which relocates every address operand
    and the data-table u16s that point at moved blocks. Some files hold a pointer form this codec does not
    know yet: the rebuild then makes the file stop walking cleanly (a jump lands inside an op), so those
    files fall back to keeping every string at its original byte length (`in_place`)."""
    ops, errs0 = scn.walk(b, base)
    op_at = {}
    for a, (op, outs, nxt, info) in ops.items():
        if op == 0x3B and info:
            op_at[info[0][1]] = a
    blocks = [(a - base, nxt - base) for a, (op, outs, nxt, info) in ops.items()]
    skipped = []

    def overlaps_code(off, ln):
        return any(s < off + ln and off < e for s, e in blocks)

    plan, notes = [], []
    for e in entries:
        text = text_of(e, marker)
        if not text:
            continue
        off, budget = int(e["ptr"], 16), e["len"]
        if op_at.get(off) is None and overlaps_code(off, budget):
            # bytes the file scan took for text but that sit inside the bytecode: writing here breaks the
            # script (an op or its operand), so it is data no translation may touch
            skipped.append(e["id"])
            continue
        raw = encode(text, "scn")
        if len(raw) > budget:
            notes.append(f"{e['id']}: {len(raw)} > {budget} bytes, cut")
        plan.append((op_at.get(off), off, budget, raw))

    def in_place():
        out = bytearray(b)
        for a, off, budget, raw in plan:
            out[off:off + budget] = pad(raw, budget, "scn")
        return bytes(out)

    # Marker mode writes each message in place (same byte count): the files keep their exact size, so nothing
    # moves and no pointer form can be missed. `relocate=True` (the English insert) may grow a message instead.
    if not relocate:
        return in_place(), notes, 0

    # A data run (choice list, banner) is referenced by tables this codec does not relocate; moving it shifts
    # every later byte, and even a same-length rewrite can lose a leading control byte (\x18 place-name banner).
    # DATA_RUNS=0 (the default for the marker build) leaves those runs alone and reports them.
    if not DATA_RUNS:
        plan = [p for p in plan if p[0] is not None]
        if not plan:
            return b, notes, 0
    elif any(a is None for a, _o, _b, _r in plan):
        notes.append(f"{name}: kept every string in place (a data run cannot move)")
        return in_place(), notes, 0
    edits = {a - base: b"\x3b\x02" + raw + b"\0" for a, _o, _b, raw in plan}
    out, problems = scn.rebuild(b, base, ops, edits)
    if set(scn.walk(out, base)[1]) - set(errs0):
        notes.append(f"{name}: relocation broke the walk, kept every string in place")
        return in_place(), notes, 0
    notes += [f"{name}: {p}" for p in problems]
    if skipped:
        notes.append(f"{name}: {len(skipped)} data runs left alone (inside the bytecode): "
                     + ", ".join(skipped[:6]) + ("..." if len(skipped) > 6 else ""))
    return out, notes, len(plan)


def pad(raw, budget, kind):
    """Exactly `budget` bytes holding `raw`, space padded: the site keeps its length and its own NUL terminator."""
    cut = fit(raw, budget, kind)
    return cut + b" " * (budget - len(cut))


def pool_insert(b, entries, kind, marker):
    """MES/SMX: one NUL-separated pool with u16 offsets, so each string keeps its byte length (space padded)."""
    out = bytearray(b)
    notes = []
    start = pool_start(b, kind)
    for e in entries:
        text = text_of(e, marker)
        if not text:
            continue
        off, budget = int(e["ptr"], 16), e["len"]
        raw = encode(text, kind)
        if len(raw) > budget:
            notes.append(f"{e['id']}: {len(raw)} > {budget} bytes, cut")
        out[off:off + budget] = (fit(raw, budget, kind) + b" " * (budget - min(len(raw), budget)))
    return bytes(out), notes, 0


def exe_insert(b, entries, marker):
    out = bytearray(b)
    notes = []
    for e in entries:
        text = text_of(e, marker)
        if not text:
            continue
        off, budget = int(e["ptr"], 16), e["len"]
        raw = encode(text, "exe")
        if len(raw) > budget:
            notes.append(f"{e['id']}: {len(raw)} > {budget} bytes, cut")
            raw = fit(raw, budget, "exe")
        out[off:off + budget] = raw + b" " * (budget - len(raw))
    return bytes(out), notes, 0


def apply(tree, marker=False, relocate=None):
    """Write the English (or the [id] markers) into the build tree. Returns (notes, strings written, moved).

    relocate=False keeps every SCN file at its own size (the marker build); the English insert relocates."""
    tree = Path(tree)
    notes, written, moved = [], 0, 0
    if relocate is None:
        relocate = not marker
    members = {}
    for rel, entries in load():
        kind = rel.split("/")[0].replace(".json", "")
        if kind == "exe":
            p = tree / "SLPS_010.30"
            new, n, _ = exe_insert(p.read_bytes(), entries, marker)
            p.write_bytes(new)
            notes += n
            written += sum(1 for e in entries if text_of(e, marker))
            continue
        if kind not in ARCH:
            continue
        arch, ext = ARCH[kind]
        member = rel.split("/")[-1].replace(".json", "") + ext
        members.setdefault(arch, []).append((member, kind, entries))
    for arch, items in members.items():
        p = tree / arch
        start, ents = mps.read(p.read_bytes())
        tables = {m: (k, e) for m, k, e in items}
        out = []
        for name, _off, blob in ents:
            if name in tables:
                kind, entries = tables[name]
                if kind == "scn":
                    blob, n, m = scn_insert(blob, scn.base_of(name[:-4]), entries, marker, name=name, relocate=relocate)
                    moved += m
                elif kind == "mes":
                    blob, n, _ = pool_insert(blob, entries, "mes", marker)
                else:
                    blob, n, _ = pool_insert(blob, entries, "smx", marker)
                notes += n
                written += sum(1 for e in entries if text_of(e, marker))
            out.append((name, blob))
        p.write_bytes(mps.write(out, start))
    return notes, written, moved


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td) / "tree"
            shutil.copytree(ROOT / "work" / "orig" / "tree", tree)
            notes, written, moved = apply(tree, marker=True)
        for n in notes[:20]:
            print("  -", n)
        print(f"{written} marker strings, {moved} message ops relocated, {len(notes)} sites too small")
        sys.exit(1 if moved == 0 else 0)
    elif cmd == "marker":
        notes, written, moved = apply(Path(sys.argv[2]), marker=True)
        print(f"marker: {written} strings, {moved} relocated, {len(notes)} cut")
        for n in notes[:10]:
            print("  -", n)
    else:
        print(__doc__)
        sys.exit(2)
