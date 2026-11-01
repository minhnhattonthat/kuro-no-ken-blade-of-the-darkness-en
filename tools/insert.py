"""insert.py: write the English of script/**/*.json back into the game's data files.

    python -X utf8 tools/insert.py check             # every `en` fits its site (or can move) and encodes
    python -X utf8 tools/insert.py marker DIR        # write [id] marker text for EVERY entry into a tree copy the
                                                     # build made (build.py --marker does this for you)

Encoding (docs/re/font.md, docs/re/text.md): English is written as ASCII bytes; the message renderer draws
them with the half-width font in SYSTEM.FNT (36-byte entries from 0x10, code < 0x80) at 8 px per character.
A SCN message op is `3b 02 <text> 00`. The English insert never moves a byte of bytecode (scn_place): the
op that opens a unit becomes `3b 00 <address>` (the string reader 0x8002c33c takes an address for any type
but 2) plus a jump over its old bytes, the unit's other ops become jumps, and the English strings go into the
freed bytes and the file's tail (up to the slot size). So no pointer form the codec does not know can break.
The fixed-size pools (MES, SMX) and the EXE labels keep their original byte length: the text is cut there
and `check` reports it as a problem.
"""
import json
import re
import shutil
import struct
import textwrap
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
        plan.append((op_at.get(off), off, budget, raw, e["id"]))

    def in_place():
        out = bytearray(b)
        for a, off, budget, raw, eid in plan:
            if len(raw) > budget:
                notes.append(f"{eid}: {len(raw)} > {budget} bytes, cut")
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
        notes += [f"{eid}: data run (choice/banner), not written yet" for a, _o, _b, _r, eid in plan if a is None]
        plan = [p for p in plan if p[0] is not None]
        if not plan:
            return b, notes, 0
    elif any(p[0] is None for p in plan):       # a data run cannot move: the whole file stays in place
        return in_place(), notes, 0
    edits = {a - base: b"\x3b\x02" + raw + b"\0" for a, _o, _b, raw, _id in plan}
    out, problems = scn.rebuild(b, base, ops, edits)
    if set(scn.walk(out, base)[1]) - set(errs0):
        notes.append(f"{name}: relocation broke the walk, kept every string in place")
        return in_place(), notes, 0
    notes += [f"{name}: {p}" for p in problems]
    if skipped:
        notes.append(f"{name}: {len(skipped)} data runs left alone (inside the bytecode): "
                     + ", ".join(skipped[:6]) + ("..." if len(skipped) > 6 else ""))
    return out, notes, len(plan)


# bytes each script slot holds (docs/re/scenes.md); slot 2's end is not measured yet, so it gets slot 1's size
SLOT_CAP = {0x0000: 0x2000, 0x2000: 0x2000, 0x4000: 0x1000, 0x5000: 0x2000}
SKIP = set()                          # bisecting (build.py --skip exe,mes,smx,scn): those kinds keep the JP files
LEGACY = set()                     # bisecting (build.py --legacy mes,smx): those pools written in place (cut)
ONLY = None                       # bisecting (build.py --only A,B): SCN files that get English; the rest stay JP
GROW = True                         # False (build.py --no-grow): no SCN file grows; strings that need it are cut
MSG_W, MSG_LAST, PAGE = 28, 27, 4    # field box: chars a line, on a page's last line (page mark), lines a page
LEAD = re.compile(r"^(?:\\[a-zA-Z]\d*|\[[0-9A-Fa-f]{2,4}\])+")
TRAIL = re.compile(r"(?:\\[a-zA-Z]\d*|\[[0-9A-Fa-f]{2,4}\])+$")


def flow(text, line):
    """Lay English words out the way the field box shows them, starting on page line `line`.
    -> (text with \\n / \\f breaks, line the last word sits on)."""
    parts, cur = [], ""

    def room():
        return MSG_LAST if line == PAGE - 1 else MSG_W

    def brk():
        nonlocal line
        line += 1
        parts.append("\\n" if line < PAGE else "\\f")
        line %= PAGE

    for w in text.split():
        cand = f"{cur} {w}" if cur else w
        if len(cand) <= room():
            cur = cand
            continue
        if cur:
            parts.append(cur)
            brk()
        while len(w) > room():
            parts.append(w[:room()])
            brk()
            w = w[room():]
        cur = w
    parts.append(cur)
    # a leading space survives: the text follows an engine-printed name on the same line (99CMN "<item> obtained.")
    return (" " if text[:1] == " " else "") + "".join(parts), line


def unit_text(u, by_id, line):
    """The English a SCN unit writes (JP lead/trail escapes re-attached) and the page line after it."""
    first, last = by_id[u["ids"][0]], by_id[u["ids"][-1]]
    lead, trail = LEAD.match(first["jp"]), TRAIL.search(last["jp"])
    lead, trail = lead.group(0) if lead else "", trail.group(0) if trail else ""
    body, line = flow(text_of(first, False), line)
    for code in re.findall(r"\\[nf]", trail):
        line = 0 if code == "\\f" else (line + 1) % PAGE
    return lead + body + trail, line


def msg_span(b, e):
    """(op start, op end) when the entry is the payload of a `3b 02 ... 00` message op, else None."""
    p, n = int(e["ptr"], 16), e["len"]
    if p >= 2 and b[p - 2:p] == b"\x3b\x02" and b[p + n:p + n + 1] == b"\0":
        return p - 2, p + n + 1
    return None


def walk_all(b, base, spans):
    """Ops reached from the entry points and from every message op."""
    return scn.walk(b, base, extra=[base + s for s, _e in spans])[0]


CHOICE_RIGHT, CHOICE_PAD = 280, 16      # choice window: right edge (x + w of every JP table), w = 8 px a char + pad


def choices(b, base, ops, by_ptr):
    """English choice tables: [(new table bytes, offset of the 7d op's u16 table address, ids)]. A table is
    x, y, w, h (u16) + NUL-terminated options + an empty one; w is re-sized for 8 px ASCII, right edge kept."""
    out = []
    for a, (op, o, _n, info) in sorted(ops.items()):
        if op != 0x7D or o[2][1][0] != 0:
            continue
        t = o[2][1][1] - base
        x, y, w, h = struct.unpack_from("<4H", b, t)
        p, opts, ids = t + 8, [], []
        while b[p]:
            e = b.index(b"\0", p)
            ent = by_ptr.get(p)
            en = text_of(ent, False) if ent else ""
            opts.append(encode(en, "scn") if en else b[p:e])
            ids += [ent["id"]] if en else []
            p = e + 1
        if not ids:
            continue
        w = 8 * max(len(s) for s in opts) + CHOICE_PAD
        at = next(p for k, p, v in info if k == "v" and v == base + t)
        out.append((struct.pack("<4H", max(8, CHOICE_RIGHT - w), y, w, h) + b"\0".join(opts) + b"\0\0", at, ids))
    return out


def refs(b, base, spans, extra=()):
    """Script addresses something in or around this file may hold: every u16 operand of the ops walked from
    the entry points and from every message op (the file scan found some that only 0x7c reaches), every u16 at
    any offset of the bytes no op covers (data tables), and `extra` (other files' addresses into 99CMN).
    Only exact hits on an op start (a jump target) or a payload start (a string taken by address) count."""
    ops = walk_all(b, base, spans)
    skip = bytearray(len(b))
    for s, e in spans:
        skip[s:e] = b"\1" * (e - s)
    vals = set(extra)
    for a, (op, _out, nxt, info) in ops.items():
        skip[a - base:nxt - base] = b"\1" * (nxt - a)
        vals |= {v for _k, _p, v in scn._addr_values(op, info)}
        sig = scn.OPS.get(op) if op < 0x100 else scn.XOPS.get(op & 0xFF)
        if sig and "S" in sig and info:         # a string operand given as an address
            k, _p, v = info[0] if sig.startswith("S") else info[-1]
            if k == "v":
                vals.add(v)
    vals |= {int.from_bytes(b[i:i + 2], "little") for i in range(len(b) - 1) if not skip[i] and not skip[i + 1]}
    return vals, ops


def runs(spans, vals, base):
    """Contiguous message ops merged into runs [(start, end, [spans])]. A run breaks where an op start is a jump
    target. Ops whose payload is taken by address (`pinned`) stay runs of their own and are flagged."""
    out, pinned = [], set()
    for s, e in sorted(spans):
        pin = base + s + 2 in vals
        if pin:
            pinned.add((s, e))
        if out and out[-1][1] == s and base + s not in vals and not pin and out[-1][2][-1] not in pinned:
            out[-1][1] = e
            out[-1][2].append((s, e))
        else:
            out.append([s, e, [(s, e)]])
    return out, pinned


def slot_cap(name, names):
    """Bytes the file's slot holds. An area script whose area has no map script (slot 1) may run on into
    slot 1's space, as 25TOU (12,923 bytes) does on the original disc."""
    base = scn.base_of(name[:-4])
    if base == 0 and not any(n != name and n[:5] == name[:5] and scn.base_of(n[:-4]) == 0x2000 for n in names):
        return 0x4000
    return SLOT_CAP.get(base, 0x2000)


def scn_place(b, base, units, by_id, name, extra_refs=(), cap=None):
    """English insert for one SCN file without moving any bytecode. -> (new bytes, notes, units written).

    Each unit's English (laid out in pages, the page line carried over units that end mid-page) is given to its
    first message op; the unit's other ops print nothing. Contiguous ops form a run: the run's text goes inline
    (`3b 02 text 00`, then a jump over the rest) when it fits, else the run starts with `3b 00 <address>` + the
    jump and the text goes into the bytes freed by other runs or the file tail (up to the slot size)."""
    notes = []
    spans, text_at, line, n = {}, {}, 0, 0
    for u in units:
        ops = [msg_span(b, by_id[i]) for i in u["ids"]]
        ops = [sp for sp in ops if sp]
        for sp in ops:
            spans[sp] = b""
        if not ops or not text_of(by_id[u["ids"][0]], False):
            continue                    # data runs (choice options): choices(); empty JP
        text, line = unit_text(u, by_id, line)
        spans[ops[0]] = encode(text, "scn")
        text_at[ops[0]] = u["id"]
        n += 1
    vals, walked = refs(b, base, list(spans), extra_refs)
    out = bytearray(b)
    free, want = [], []                 # free: [start, end); want: (string bytes, offset of its u16 address)
    by_ptr = {int(by_id[i]["ptr"], 16): by_id[i] for u in units for i in u["ids"]}
    for tbl, at, ids in choices(b, base, walked, by_ptr):
        want.append((tbl, at))
        n += len(ids)
    blocks, pinned = runs(spans, vals, base)
    for s, e, ops in blocks:
        raw = b"".join(spans[sp] for sp in ops)
        R = e - s
        if (s, e) in pinned and len(raw) + 3 > R and R >= 11:
            # the payload start must stay a string: its first part inline, then `3b 00 <rest>` (0x3b appends to
            # the message buffer, so two ops print the same) and a jump over the rest of the run
            head = fit(raw, R - 10, "scn")
            k = s + 2 + len(head)
            out[s:k + 1] = b"\x3b\x02" + head + b"\0"
            out[k + 1:k + 8] = b"\x3b\x00\0\0\x06" + (base + e).to_bytes(2, "little")
            want.append((raw[len(head):] + b"\0", k + 3))
            free.append([k + 8, e])
        elif (s, e) in pinned:
            if len(raw) + 3 > R:
                notes.append(f"{text_at.get((s, e), hex(s))}: payload taken by address, English cut to {R - 3} bytes")
            out[s:e] = b"\x3b\x02" + pad(raw, R - 3, "scn") + b"\0"
        elif len(raw) + 3 == R:
            out[s:e] = b"\x3b\x02" + raw + b"\0"
        elif not raw:
            out[s:s + 3] = b"\x06" + (base + e).to_bytes(2, "little")
            free.append([s + 3, e])
        elif len(raw) + 6 <= R:
            out[s:s + len(raw) + 6] = b"\x3b\x02" + raw + b"\0\x06" + (base + e).to_bytes(2, "little")
            free.append([s + len(raw) + 6, e])
        elif R == 4 or R >= 7:
            out[s:s + 4] = b"\x3b\x00\0\0"
            want.append((raw + b"\0", s + 2))
            if R > 4:
                out[s + 4:s + 7] = b"\x06" + (base + e).to_bytes(2, "little")
                free.append([s + 7, e])
        else:
            notes.append(f"{text_at.get(ops[0], hex(s))}: a {R}-byte run cannot hold {len(raw)} bytes or an address")
            out[s:e] = b"\x3b\x02" + pad(raw, R - 3, "scn") + b"\0"
    cap = cap or SLOT_CAP.get(base, 0x2000)
    if not GROW:
        cap = len(b)
    tail = [len(b), max(cap, len(b))]
    for blk in free:
        out[blk[0]:blk[1]] = bytes(blk[1] - blk[0])
    placed = {}
    for raw, at in sorted(want, key=lambda w: -len(w[0])):
        if raw not in placed:
            fits = [blk for blk in free if blk[1] - blk[0] >= len(raw)]
            blk = min(fits, key=lambda x: x[1] - x[0]) if fits else tail
            if blk[1] - blk[0] < len(raw):
                notes.append(f"{name}: out of room for {len(raw)} bytes (slot holds {cap:#x})")
                continue
            placed[raw] = blk[0]
            if blk is tail and len(out) < blk[0] + len(raw):
                out += bytes(blk[0] + len(raw) - len(out))
            out[blk[0]:blk[0] + len(raw)] = raw
            blk[0] += len(raw)
        out[at:at + 2] = (base + placed[raw]).to_bytes(2, "little")
    return bytes(out), notes, n


def common_refs(ents):
    """Every u16 operand value in the other SCN files' walked ops that lands in 99CMN (0x4000-0x4fff): a
    string or jump another script takes from the resident library."""
    refs = set()
    for name, _o, blob in ents:
        if name == "99CMN.SCN":
            continue
        ops, _ = scn.walk(blob, scn.base_of(name[:-4]))
        refs |= {v for _a, (_op, _out, _n, info) in ops.items() for k, _p, v in info
                 if k in ("w", "v") and 0x4000 <= v < 0x5000}
    return refs


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


VIS_W, VIS_LINES = 62, 5


def balanced(text, width, indent=""):
    """Wrap into as few lines as greedy wrapping needs, but with the narrowest width that still gives that
    count, so the last line is not a one-word widow."""
    n = len(textwrap.wrap(text, width, subsequent_indent=indent))
    for w in range(max(1, len(text) // max(n, 1)), width + 1):
        lines = textwrap.wrap(text, w, subsequent_indent=indent)
        if len(lines) <= n:
            return lines
    return textwrap.wrap(text, width, subsequent_indent=indent)


def vis_text(u, e, speakers):
    """A VIS caption page: the speaker's name line (as the JP has it), then the English wrapped at 62. Pages the
    JP centres with full-width spaces are centred; quoted speech hangs under its opening quote."""
    en = text_of(e, False)
    trail = TRAIL.search(e["jp"])
    trail = trail.group(0) if trail else ""
    sp = u["speaker"] or ("???" if e["jp"].startswith("？？？\\n") else "")   # unit split drops the ？？？ label
    if sp:
        lines = balanced(en, VIS_W, " " if en.startswith('"') else "")
        lines.insert(0, speakers.get(sp, sp))
    else:
        lines = balanced(en, VIS_W)
        if e["jp"].startswith("　"):
            lines = [" " * ((VIS_W - len(x)) // 2) + x for x in lines]
    return "\\n".join(lines) + trail, len(lines)


def mes_insert(b, entries, units, speakers):
    """VIS/MES: rebuild the string pool with the English and remap the u16 tables that point into it (header
    u16 0/1 = the page table and the directive table; directive pointers may land 1 byte into a string)."""
    start = struct.unpack_from("<H", b, 0)[0]
    vals, q = [], start
    while not any(v >= q for v in vals) or q < min(v for v in vals if v >= q):
        vals.append(struct.unpack_from("<H", b, q)[0])
        q += 2
    pool = q
    notes, new, where = [], bytearray(b[:pool]), {}
    by_ptr = {int(e["ptr"], 16): e for e in entries}
    unit = {u["id"]: u for u in units}
    p = pool
    for seg in b[pool:].split(b"\0")[:-1] if b.endswith(b"\0") else b[pool:].split(b"\0"):
        e = by_ptr.get(p)
        if e and text_of(e, False):
            text, n = vis_text(unit[e["id"]], e, speakers)
            if n > VIS_LINES or any(len(x) > VIS_W for x in text.split("\\n")):
                notes.append(f"{e['id']}: {n} lines (VIS shows {VIS_LINES} x {VIS_W})")
            where[p] = len(new)
            new += encode(text, "mes") + b"\0"
        else:
            for i in range(len(seg) + 1):
                where[p + i] = len(new) + i
            new += seg + b"\0"
        p += len(seg) + 1
    if not b.endswith(b"\0"):
        del new[-1]
    for i, v in enumerate(vals):
        at = start + 2 * i
        if v >= pool:
            if v not in where:
                notes.append(f"table {at:#x} points into a rewritten string ({v:#x})")
                continue
            struct.pack_into("<H", new, at, where[v])
    return bytes(new), notes, 0


SMX_REC, SMX_STEP = 0x58, 0x50      # SMX records: 0x50 bytes from 0x58, u16 name / description offsets at +0 / +2


def smx_insert(b, entries):
    """SMX (items, techniques): rebuild the string pool with the English and remap the records' u16 offsets."""
    import extract
    pool = extract.pool_start(b, "smx")
    by_ptr = {int(e["ptr"], 16): e for e in entries}
    new, where, p = bytearray(b[:pool]), {}, pool
    for seg in b[pool:].split(b"\0"):
        e = by_ptr.get(p)
        where[p] = len(new)
        new += (encode(text_of(e, False), "smx") if e and text_of(e, False) else seg) + b"\0"
        p += len(seg) + 1
    del new[-1]                         # split() gave one segment after the pool's last NUL
    notes = []
    refs = 0
    for r in range(SMX_REC, pool - 3, SMX_STEP):
        for at in (r, r + 2):
            v = struct.unpack_from("<H", b, at)[0]
            if v in where and v >= pool:
                struct.pack_into("<H", new, at, where[v])
                refs += 1
    missing = [e["id"] for e in entries if text_of(e, False) and not any(
        struct.unpack_from("<H", b, at)[0] == int(e["ptr"], 16)
        for r in range(SMX_REC, pool - 3, SMX_STEP) for at in (r, r + 2))]
    notes += [f"{i}: no record points at this string" for i in missing]
    return bytes(new), notes, 0


EXE_RAM = 0x80010000 - 0x800       # RAM = file offset + EXE_RAM (t_addr 0x80010000, text from file 0x800)
EXE_KEEP = {0x800, 0x810}           # save-slot line and its time: the code writes digits at fixed offsets
EXE_WRITES = []                     # file offsets of the pointer words exe_insert rewrote (build.py's romdiff)


def exe_refs(b):
    """{ram: [(word_off,) | (lui_off, lo_off)]}: every data word, and lui + addiu/ori/load pairs (lo within 16
    instructions of the lui on the same register; gp-relative loads reach no string, checked)."""
    refs, lui = {}, {}
    for off in range(0x800, 0x800 + struct.unpack_from("<I", b, 0x1c)[0], 4):
        w = struct.unpack_from("<I", b, off)[0]
        refs.setdefault(w, []).append((off,))
        op, rs, rt, imm = w >> 26, (w >> 21) & 31, (w >> 16) & 31, w & 0xFFFF
        if op == 0x0F:
            lui[rt] = (imm << 16, off)
        elif op in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25) and rs in lui and off - lui[rs][1] < 0x40:
            a = lui[rs][0] | imm if op == 0x0D else (lui[rs][0] + imm - (imm & 0x8000) * 2) & 0xFFFFFFFF
            refs.setdefault(a, []).append((lui[rs][1], off))
    return refs


def exe_insert(b, entries, marker):
    """Marker build / EXE_KEEP: in place, space-padded to the JP bytes. English: every other string is repacked,
    in order, into its run of adjacent slots (string + NUL + zero padding; the runs are the two string areas),
    and every pointer to it is rewritten (data words, lui+lo pairs; a lui can be shared, so a string must keep
    its 64 KB half, which packing in order inside its own run does)."""
    out = bytearray(b)
    notes, pack = [], []
    for e in entries:
        text = text_of(e, marker)
        if not text:
            continue
        off, budget = int(e["ptr"], 16), e["len"]
        raw = encode(text, "exe")
        if not marker and off not in EXE_KEEP:
            end = off + budget + 1
            while end % 4 and b[end] == 0:
                end += 1
            pack.append((off, end, raw, e))
            continue
        if len(raw) > budget:
            notes.append(f"{e['id']}: {len(raw)} > {budget} bytes, cut")
            raw = fit(raw, budget, "exe")
        out[off:off + budget] = raw + b" " * (budget - len(raw))
    runs = []                                       # [start, end] of adjacent slots
    for off, end, _r, _e in sorted(pack, key=lambda p: p[0]):
        out[off:end] = bytes(end - off)
        if runs and runs[-1][1] == off:
            runs[-1][1] = end
        else:
            runs.append([off, end])
    refs = exe_refs(b) if pack else {}
    hi = lambda a: (a + 0x8000) >> 16
    cur = [r[0] for r in runs]                      # next free byte of each run

    def put(i, off, raw):
        if cur[i] + len(raw) + 1 > runs[i][1]:
            return False
        if any(len(r) == 2 for r in refs.get(off + EXE_RAM, [])) and hi(cur[i] + EXE_RAM) != hi(off + EXE_RAM):
            return False
        at, new = cur[i], cur[i] + EXE_RAM
        out[at:at + len(raw) + 1] = raw + b"\0"
        for r in refs.get(off + EXE_RAM, []):
            if len(r) == 1:
                struct.pack_into("<I", out, r[0], new)
            else:
                lo = struct.unpack_from("<I", out, r[1])[0]
                struct.pack_into("<I", out, r[1], lo & 0xFFFF0000 | new & 0xFFFF)
            EXE_WRITES.append(r[-1])
        cur[i] = (at + len(raw) + 2) & ~1
        return True

    # lui-referenced strings first (they can't leave their 64 KB), each in order into its own run, else into any
    # run with room
    pinned = lambda off: any(len(r) == 2 for r in refs.get(off + EXE_RAM, []))
    for first in (True, False):
        spill = []
        for off, end, raw, e in sorted(pack, key=lambda p: p[0]):
            if pinned(off) == first and not put(next(i for i, r in enumerate(runs) if r[0] <= off < r[1]), off, raw):
                spill.append((off, raw, e))
        for off, raw, e in sorted(spill, key=lambda s: -len(s[1])):
            if not any(put(i, off, raw) for i in sorted(range(len(runs)), key=lambda i: cur[i] - runs[i][1])):
                notes.append(f"{e['id']}: no room in the EXE string areas ({len(raw)} bytes), left out")
    return bytes(out), notes, len(pack)


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
        if kind in SKIP:
            continue
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
        if not marker:
            import batches
            by_file, by_id = {}, {}
            for u in batches.units():
                by_file.setdefault(u["file"], []).append(u)
            for _m, _k, es in items:
                by_id.update((e["id"], e) for e in es)
            speakers = batches.glossary()[1]
        if arch == "SCN.MPS" and not marker:
            cmn = common_refs(ents)
        out = []
        for name, _off, blob in ents:
            if name in tables and (ONLY is None or tables[name][0] not in ("scn", "mes") or name[:-4] in ONLY):
                kind, entries = tables[name]
                if kind == "scn" and not marker:
                    rel = f"scn/{name[:-4]}.json"
                    blob, n, m = scn_place(blob, scn.base_of(name[:-4]), by_file.get(rel, []), by_id, name,
                                           cmn if name == "99CMN.SCN" else (),
                                           slot_cap(name, [x for x, _o, _b in ents]))
                    moved += m
                elif kind == "scn":
                    blob, n, m = scn_insert(blob, scn.base_of(name[:-4]), entries, marker, name=name, relocate=relocate)
                    moved += m
                elif kind in LEGACY:
                    blob, n, _ = pool_insert(blob, entries, kind, marker)
                elif kind == "mes" and not marker:
                    blob, n, _ = mes_insert(blob, entries, by_file.get(f"mes/{name}.json", []), speakers)
                elif kind == "mes":
                    blob, n, _ = pool_insert(blob, entries, "mes", marker)
                elif not marker:
                    blob, n, _ = smx_insert(blob, entries)
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
