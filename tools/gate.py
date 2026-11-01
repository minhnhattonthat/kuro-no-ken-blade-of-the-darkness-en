"""gate.py: what the English build may change in the disc tree, checked against the clean original (phase 7
§Checks; the EXE also goes through romdiff.py with its write journal, see build.py).

    python -X utf8 tools/gate.py ORIG_TREE NEW_TREE

Fails on
  - a changed file the build does not edit, or a file added / removed;
  - an archive whose member list changed, or a changed member nothing in script/ or tools/gfx.py targets;
  - SCN: a walk error the original file did not have, a file past its slot;
  - MES: bytes changed before the u16 table, a table of another length, a pool with another string count;
  - SMX: bytes changed outside the records' u16 name/description slots, another string count;
  - BSX: bytes changed outside talk records and `03 01|02|03 <u16>` refs, a file past BSX_MAX;
  - a font of another length;
  - translated text whose Japanese is still in its file (EXE, SCN, MES, SMX, BSX), unless the English is there
    too: a rebuilt choice table (op 7d) leaves the old options unreferenced in place."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import gfx      # noqa: E402
import insert   # noqa: E402
import mps      # noqa: E402
import scn      # noqa: E402

EDITED = {"SLPS_010.30", "SCN.MPS", "VIS.MPS", "SYS.MPS", "BSX.MPS", "BOD.STR"}   # BOD.STR: tools/fmv.py
KIND = {"SCN.MPS": "scn", "VIS.MPS": "mes", "SYS.MPS": "smx", "BSX.MPS": "bsx"}
GRAPHICS = {"SYSTEM", "WIN02"} | set(gfx.CREDITS)      # SYS.MPS members redrawn (stems; fnt.py, gfx.py)


def changed_at(x, y):
    return [i for i in range(min(len(x), len(y))) if x[i] != y[i]]


def member(kind, name, x, y, names):
    """Structure errors for one changed archive member (x = original, y = built)."""
    errs = []
    if kind == "scn":
        base = scn.base_of(name[:-4])
        new = set(scn.walk(y, base)[1]) - set(scn.walk(x, base)[1])
        errs += [f"walk: {e}" for e in sorted(new)[:5]]
        if len(y) > max(len(x), insert.slot_cap(name, names)):
            errs.append(f"{len(y)} bytes, past its slot")
    elif kind == "mes":
        start, vals, pool = insert.mes_table(x)
        if y[:start] != x[:start] or insert.mes_table(y)[2] != pool:
            errs.append("header or u16 table length changed")
        if y[pool:].count(b"\0") != x[pool:].count(b"\0"):
            errs.append("string count changed")
    elif kind == "smx":
        pool = extract.pool_start(x, "smx")
        slots = {r + k for r in range(insert.SMX_REC, pool - 3, insert.SMX_STEP) for k in range(4)}
        bad = [i for i in changed_at(x[:pool], y[:pool]) if i not in slots]
        if bad:
            errs.append(f"record bytes changed outside the name/description slots ({len(bad)}, first {bad[:1]})")
        if y[pool:].count(b"\0") != x[pool:].count(b"\0"):
            errs.append("string count changed")
    elif kind == "bsx":
        spans = [(m.start(), m.end()) for m in extract.BSX_TAG.finditer(x)]
        ref = lambda i: (i >= 2 and x[i - 2] == 3 and 1 <= x[i - 1] <= 3) or (i >= 3 and x[i - 3] == 3 and
                                                                              1 <= x[i - 2] <= 3)
        bad = [i for i in changed_at(x, y) if not ref(i) and not any(s <= i < e for s, e in spans)]
        if bad:
            errs.append(f"bytes changed outside talk records and refs ({len(bad)}, first 0x{bad[0]:x})")
        if len(y) > insert.BSX_MAX:
            errs.append(f"{len(y)} bytes > 0x{insert.BSX_MAX:x}")
    return errs


def jp_left(kind, blob, entries):
    """Translated entries whose Japanese is still in `blob` with no English beside it."""
    out = []
    for e in entries:
        jp = insert.encode(e["jp"], kind)
        en = insert.text_of(e, False).split()
        # shortcut: the first English word stands for "the English is here too"; a full choice-table decode
        # would be exact (upgrade if a translated option ever shares its first word with an untouched line)
        if len(jp) >= 4 and jp in blob and not (en and insert.encode(en[0], kind) in blob):
            out.append(e["id"])
    return out


def check(orig, new):
    orig, new = Path(orig), Path(new)
    errs = []
    files = lambda t: {p.relative_to(t).as_posix() for p in t.rglob("*") if p.is_file()}
    fo, fn = files(orig), files(new)
    errs += [f"{f}: added" for f in sorted(fn - fo)] + [f"{f}: missing" for f in sorted(fo - fn)]
    errs += [f"{f}: changed, but the build does not edit it" for f in sorted(fo & fn)
             if f not in EDITED and (orig / f).read_bytes() != (new / f).read_bytes()]
    targets = {}
    for rel, es in insert.load():
        kind = rel.split("/")[0].replace(".json", "")
        es = [e for e in es if insert.text_of(e, False)]
        if kind == "exe":
            errs += [f"SLPS_010.30 {i}: Japanese still there" for i in jp_left("exe", (new / "SLPS_010.30").read_bytes(),
                                                                           [e for e in es if int(e["ptr"], 16)
                                                                            not in insert.EXE_KEEP])]
        elif kind in insert.ARCH:
            arch, ext = insert.ARCH[kind]
            targets[(arch, rel.split("/")[-1][:-5] + ext)] = es
    bsx = [e for (arch, _m), es in targets.items() if arch == "BSX.MPS" for e in es]
    for arch, kind in KIND.items():
        a, b = mps.read((orig / arch).read_bytes())[1], mps.read((new / arch).read_bytes())[1]
        if [n for n, _o, _b in a] != [n for n, _o, _b in b]:
            errs.append(f"{arch}: member list changed")
            continue
        names = [n for n, _o, _b in a]
        for (name, _o, x), (_n, _p, y) in zip(a, b):
            es = targets.get((arch, name), [])
            if arch == "BSX.MPS":               # one English per JP line, written into every battle that has it
                es = [e for e in bsx if insert.encode(e["jp"], "bsx") in x]
            if x == y:
                if es:
                    errs.append(f"{arch}/{name}: has English in script/ but did not change")
                continue
            if name.split(".")[0] in GRAPHICS and arch == "SYS.MPS":
                if name == "SYSTEM.FNT" and len(x) != len(y):       # PAD images are re-encoded, may change size
                    errs.append(f"{arch}/{name}: font changed length")
                continue
            if not es:
                errs.append(f"{arch}/{name}: changed, but nothing in script/ targets it")
                continue
            errs += [f"{arch}/{name}: {e}" for e in member(kind, name, x, y, names)]
            errs += [f"{arch}/{name} {i}: Japanese still there" for i in jp_left(kind, y, es)]
    return errs


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    errs = check(sys.argv[1], sys.argv[2])
    for e in errs[:50]:
        print("  -", e)
    print(f"gate: {len(errs)} problems")
    sys.exit(1 if errs else 0)
