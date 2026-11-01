"""extract.py: dump every Japanese string of the game into script/*.json, and prove nothing is missed.

    python -X utf8 tools/extract.py dump [--force]   # write script/**/*.json (never clobbers a translation)
    python -X utf8 tools/extract.py check [-v]       # roundtrip + coverage over the original data, exit 1 on fail

Sources (docs/re/text.md):
  scn  SCN.MPS/*.SCN  - op 0x3b message strings. Walked from the script entry points, plus every `3b 02 <text> 00`
                        site the walk cannot reach (the conversation blocks hang off op 0x7b thread spawns and off
                        tables; docs/re/text.md §4).
  mes  VIS.MPS/*.MES  - visual-scene captions: u16 offset table, strings with 0x0d line breaks.
  smx  SYS.MPS/*.SMX  - item/skill names and descriptions in a NUL-separated pool with u16 offsets.
  exe  SLPS_010.30    - menu labels, battle results, save/memory-card messages (file 0x800-0x17c8 and
                        0x78c0c-0x79010, docs/re/text.md §4).

Entry fields: id, ptr, len, jp, en, max, lines, speaker, status, notes.
`len` is the byte length of the original payload and `max` the in-place budget; the width gate (phase 5) sets
the real limit, because text may be relocated out of the op stream.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import scn      # noqa: E402
import sctext   # noqa: E402

MPS = ROOT / "work" / "orig" / "mps"
SCRIPT = ROOT / "script"
EXE = ROOT / "work" / "orig" / "tree" / "SLPS_010.30"
EXE_RANGES = ((0x800, 0x17E0), (0x78C0C, 0x79030))
EXE_GLUED = (0x135C,)    # strings right after pointer words (no NUL between): カイエス, table 0x800804a4 (jp_left)


def has_jp(raw):
    """At least one real Japanese character: a lead byte alone also matches binary (`8a 01` in bytecode)."""
    if not any(0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC for c in raw):
        return False
    try:
        text = re.sub(r"\[[0-9A-Fa-f]{2,4}\]", "", sctext.decode(raw))
    except ValueError:
        return False
    if re.search("[-]", text):      # user-defined cp932 area: binary (25TOU 0x3e), never game text
        return False
    return bool(re.search("[　-鿿＀-ﾟ]", text))


def nl_of(kind):
    """Line-break byte of a source: MES strings break lines with 0x0d, the rest use the \\n escape."""
    return 0x0D if kind == "mes" else None


def roundtrip_ok(raw, kind=None):
    """The byte run decodes and re-encodes exactly (no judgement about whether it is text)."""
    if not raw:
        return False
    try:
        return sctext.encode(sctext.decode(raw, nl_of(kind)), nl_of(kind)) == raw
    except ValueError:
        return False


def good_string(raw, kind=None):
    """A byte run that is a real string: it roundtrips and carries at least one Japanese char."""
    return has_jp(raw) and roundtrip_ok(raw, kind)


def nul_string(b, off, limit=None):
    """(offset, payload) of the NUL-terminated string at off."""
    if not 0 <= off < len(b):
        return None
    e = b.find(b"\0", off)
    if e < 0 or (limit and e > limit):
        return None
    return off, b[off:e]


PAIR = re.compile(rb"(?:[\x81-\x9f\xe0-\xfc][\x40-\x7e\x80-\xfc]|[ -~])+")


def runs(data, start=0, end=None, minpairs=2):
    """[(offset, bytes)] of Japanese runs: a lazy survey for the report, not a gate."""
    end = len(data) if end is None else end
    out = []
    for m in PAIR.finditer(data, start, end):
        run = m.group(0)
        while run and (0x81 <= run[-1] <= 0x9F or 0xE0 <= run[-1] <= 0xFC):
            run = run[:-1]
        pairs = sum(1 for c in run if 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC)
        if pairs >= minpairs and good_string(run):
            out.append((m.start(), run))
    return out


def entry(name, ptr, raw, kind, notes="", speaker=None):
    text = sctext.decode(raw, nl_of(kind))
    return {
        "id": f"{name}:{ptr:x}", "ptr": f"0x{ptr:x}", "len": len(raw),
        "jp": text, "en": "", "max": len(raw), "lines": sctext.lines(text),
        "speaker": speaker or "", "kind": kind, "status": "todo", "notes": notes,
    }


# --------------------------------------------------------------------------------------------- SCN

def scn_files():
    return sorted((MPS / "SCN").glob("*.SCN"))


def sites(b):
    """Every `3b 02 <text> 00` message site in the file -> {payload offset: (payload, op offset)}."""
    out = {}
    i = 0
    while True:
        i = b.find(b"\x3b\x02", i)
        if i < 0:
            return out
        got = nul_string(b, i + 2)
        if got and good_string(got[1]):
            out[got[0]] = (got[1], i)
            i = got[0] + len(got[1])
        else:
            i += 2


KANA = re.compile("[\u3041-\u3096\u30a1-\u30fa]")


def spoken(raw):
    """Text the player reads: a string with kana in it (choice options, hint texts, banners)."""
    try:
        return bool(KANA.search(sctext.decode(raw)))
    except ValueError:
        return False


def scn_entries(name, b, base):
    msg = sites(b)
    # walk from the file's entry table plus every scanned message op: those blocks are conversation code the
    # entry table does not point at, and their non-message ops would otherwise show up as unexplained gaps
    ops, errs = scn.walk(b, base, extra=[base + opoff for _, opoff in msg.values()])
    found = {}

    # messages on the walked path; speaker = the bare name line just before
    last_name = None
    for a in sorted(ops):
        op, out, nxt, info = ops[a]
        if op == 0x3B and out and out[0][0] == "s" and info:
            off = info[0][1]                       # ("S", payload offset, length)
            e = entry(name, off, out[0][1], "scn", speaker=last_name)
            found[off] = e
            last_name = e["jp"].removesuffix("\\n") if sctext.name_line(e["jp"]) else None
        elif op != 0x3B:
            last_name = None

    # everything else the walk could not reach: the file is scanned for message ops
    for off, (raw, opoff) in msg.items():
        if off not in found:
            found[off] = entry(name, off, raw, "scn",
                               notes="not on a walked path: file scan found this message op")

    # and for text that no message op precedes at all: choice options (`7d` points at a table in the data),
    # sign/hint texts, place-name banners. Kana is the tell; a bare run of kanji in the data is not text.
    cov = bytearray(len(b))
    for off, e in found.items():
        for i in range(off, min(len(b), off + e["len"])):
            cov[i] = 1
    for off, run in runs(b):
        if any(cov[off:off + len(run)]) or not spoken(run):
            continue
        found[off] = entry(name, off, run, "scn",
                           notes="no message op: file scan found this text (choice option / sign / banner)")
        for i in range(off, min(len(b), off + len(run))):
            cov[i] = 1
    return found, ops, errs


# --------------------------------------------------------------------------------------------- MES / SMX

def pool_start(b, kind=None):
    """Start of the NUL-separated string pool at the end of a MES/SMX file."""
    if kind == "mes":       # u16 offset table at 0: growing absolute offsets, the first one is the first string
        vals, prev = [], 0
        while True:
            v = int.from_bytes(b[prev:prev + 2], "little") if prev + 2 <= len(b) else 0
            if v <= prev or v >= len(b):
                break
            vals.append(v)
            prev += 2
            if prev >= 0x400:
                break
        vals = [v for v in vals if v >= prev]      # skip the header fields, which point into the table
        return min(vals) if vals else None
    # SMX has no table: the pool is the tail from which every segment is a string. The codec writes any byte it
    # cannot read as a [XX] token, so "roundtrips" alone also accepts the binary records (E8 03 = 1000): a pool
    # segment must decode without byte tokens.
    def texty(s):
        return roundtrip_ok(s, kind) and not re.search(r"\[[0-9A-Fa-f]{2,4}\]", sctext.decode(s, nl_of(kind)))
    for start in range(0x100, len(b)):
        segs = [s for s in b[start:].split(b"\0") if s]
        if len(segs) < 4:
            return None
        if all((len(s) >= 2 and texty(s)) or (len(s) >= 4 and all(0x20 <= c < 0x7F for c in s)) for s in segs):
            return start
    return None


def pool_entries(path, kind):
    """Strings in the NUL-separated pool of a MES/SMX file (the tail after the tables)."""
    b = path.read_bytes()
    start = pool_start(b, kind)
    if start is None:
        return b, {}
    found = {}
    for m in re.finditer(rb"[^\0]+", b[start:]):
        raw = m.group(0)
        off = start + m.start()
        if good_string(raw, kind):
            found[off] = entry(path.stem, off, raw, kind)
    return b, found


# --------------------------------------------------------------------------------------------- EXE

def exe_entries():
    b = EXE.read_bytes()
    found = {}
    for lo, hi in EXE_RANGES:
        for m in re.finditer(rb"[^\0]+", b[lo:hi]):
            raw = m.group(0)
            label = re.fullmatch(rb"\xb1\xb2\xc3\xd1[12]", raw)   # ｱｲﾃﾑ1/2: status/equip slots, half-width only
            if not (label or good_string(raw)):
                continue
            text = sctext.decode(raw)
            tokens = len(re.findall(r"\[[0-9A-Fa-f]{2,4}\]", text))
            half = sum(1 for c in text if 0xFF61 <= ord(c) <= 0xFF9F)
            bare = re.sub(r"\[[0-9A-Fa-f]{2,4}\]", "", text)
            if (not re.search("[\u3000-\u9fff\uff00-\uffefA-Za-z0-9]", bare)
                    or tokens > 1 or (half > 2 and not label)
                    or any(0xE000 <= ord(c) <= 0xF8FF for c in text)):
                continue      # a table of codes, not a label: real labels carry no byte tokens
            off = lo + m.start()
            found[off] = entry("SLPS_010.30", off, raw, "exe")
    for off in EXE_GLUED:
        found[off] = entry("SLPS_010.30", off, b[off:b.index(b"\0", off)], "exe")
    return b, found


# --------------------------------------------------------------------------------------------- dump / check

def sources():
    """{script path: (bytes, base, {payload offset: entry})} for every source file."""
    out = {}
    for f in scn_files():
        b = f.read_bytes()
        base = scn.base_of(f.stem)
        found, ops, errs = scn_entries(f.stem, b, base)
        out[f"scn/{f.stem}.json"] = (b, base, found, ops, errs)
    for path in sorted((MPS / "VIS").glob("*.MES")):
        b, found = pool_entries(path, "mes")
        if found:
            out[f"mes/{path.name}.json"] = (b, 0, found, None, [])
    for path in sorted((MPS / "SYS").glob("*.SMX")):
        b, found = pool_entries(path, "smx")
        if found:
            out[f"smx/{path.name}.json"] = (b, 0, found, None, [])
    b, found = exe_entries()
    out["exe.json"] = (b, 0, found, None, [])
    return out


def dump(force=False):
    src = sources()
    written = 0
    for rel, (b, base, found, ops, errs) in sorted(src.items()):
        path = SCRIPT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            old = json.loads(path.read_text(encoding="utf-8"))
            keep = {e["id"]: e for e in old["entries"]}
            for e in found.values():
                o = keep.get(e["id"])
                if o:
                    for f in ("en", "status", "notes", "speaker"):
                        if o.get(f):
                            e[f] = o[f]
        meta = rel.replace("\\", "/").rsplit(".", 1)[0]
        if base:
            meta = f"{meta.split('/')[-1]} base 0x{base:x}"
        path.write_text(json.dumps({"file": meta, "entries": [found[k] for k in sorted(found)]},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        written += 1
    print(f"{written} files written to {SCRIPT.relative_to(ROOT)}/")


def check(verbose=False):
    src = sources()
    bad, total, gaps = [], 0, 0
    for rel, (b, base, found, ops, errs) in sorted(src.items()):
        total += len(found)
        for off, e in found.items():
            raw = b[off:off + e["len"]]
            if e["ptr"] != f"0x{off:x}":
                bad.append(f"{e['id']}: ptr/offset mismatch")
            try:
                if sctext.encode(e["jp"], nl_of(e["kind"])) != raw:
                    bad.append(f"{e['id']}: roundtrip mismatch")
            except ValueError as ex:
                bad.append(f"{e['id']}: {ex}")
        # coverage: no message site and no run of spoken text may be missing from the extraction
        if ops is not None:
            for off, (raw, opoff) in sites(b).items():
                if off not in found:
                    bad.append(f"{rel}: message op at 0x{opoff:x} not extracted")
            cov = bytearray(len(b))
            for off, e in found.items():
                for i in range(off, min(len(b), off + e["len"])):
                    cov[i] = 1
            for off, run in runs(b):
                if not any(cov[off:off + len(run)]) and spoken(run):
                    bad.append(f"{rel}: spoken text at 0x{off:x} not extracted: {run[:20]!r}")
            cv, gl = scn.coverage(b, base, ops)
            gaps += sum(n for _, n in gl)
            if verbose:
                print(f"  {rel}: {len(found)} strings, {len(ops)} ops, gap {sum(n for _, n in gl)} bytes"
                      + (f", errors {errs}" if errs else ""))
    print(f"{total} strings in {len(src)} files; uncovered bytes in SCN files: {gaps}; problems: {len(bad)}")
    for p in bad[:40]:
        print("  !", p)
    return bad


def gaps_report():
    """What the SCN bytes no op covers actually are: zero padding, or data that holds script addresses."""
    src = sources()
    total = {"zero": 0, "holds addresses": 0, "numbers": 0}
    numbers = []
    for rel, (b, base, found, ops, errs) in sorted(src.items()):
        if ops is None:
            continue
        cov, _ = scn.coverage(b, base, ops)
        for off, e in found.items():
            for i in range(off, min(len(b), off + e["len"])):
                cov[i] = 1
        i = 0
        while i < len(b):
            if cov[i]:
                i += 1
                continue
            j = i
            while j < len(b) and not cov[j]:
                j += 1
            run = b[i:j]
            if all(c == 0 for c in run):
                total["zero"] += len(run)
            elif any(base <= int.from_bytes(run[k:k + 2], "little") < base + len(b)
                     for k in range(0, len(run) - 1)):
                total["holds addresses"] += len(run)
            else:
                total["numbers"] += len(run)
                numbers.append((rel, i, len(run), run[:12].hex(" ")))
            i = j
    print("non-text gap bytes:", total, "total", sum(total.values()))
    if numbers:
        print("runs with no script address in them:", len(numbers))
        for rel, off, n, head in numbers[:8]:
            print(f"  {rel} 0x{off:x}+{n} {head}")
    return numbers


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "dump":
        dump("--force" in sys.argv)
    elif cmd == "check":
        sys.exit(1 if check("-v" in sys.argv or "--verbose" in sys.argv) else 0)
    elif cmd == "gaps":
        gaps_report()
    else:
        print(__doc__)
        sys.exit(2)
