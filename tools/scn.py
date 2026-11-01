"""scn.py: SCN bytecode codec (docs/re/text.md, docs/re/scenes.md).

    python -X utf8 tools/scn.py dis FILE.SCN [START [END]]   # one op per line: addr op operands
    python -X utf8 tools/scn.py check                        # walk every SCN from its entry points, report
                                                              # undecodable ops / jumps into op middles,
                                                              # and the bytes no op covers (gaps)
    python -X utf8 tools/scn.py roundtrip                    # parse -> assemble every SCN, byte-identical

Operand kinds (readers in SLPS_010.30, RAM addresses):
  w  u16 (0x8002bfdc; literals, variable indexes and jump targets)
  b  u8  (0x8002c5a8)
  d  u32 (two u16, 0x8002ebe8)
  v  value: type byte 0 -> u16 literal, 1 -> u16 variable, else nothing (0x8002c194)
  S  string: type 2 -> inline NUL-terminated SJIS, else a value = address of the string (0x8002c33c)
  K  switch: u16 var, value (default target), u8 N, N values (targets) (0x8002c60c)

Script addresses: a SCN in slot 0 starts at 0x0000, slot 1 at 0x2000, 99CMN at 0x4000, slot 2 at 0x5000
(RAM = 0x80168000 + address). Jump targets and every ADDR operand are absolute script addresses.

Call/return (disassembly of the handler table at RAM 0x800100ac): 0x01 0x06 0x07 set the script pointer
(jump, no return; 0x06/0x07 read a literal/variable), 0x04 pops the caller, 0x05 pops and yields.
0x7b stores "spawn a thread at this address" for the next yield - its operand is an address, so it is also a
control-flow edge for coverage (phase 4: that is where the conversation blocks hang off).
"""
import struct
import sys
from pathlib import Path

# main ops; None = undecoded. Ops that end a block (no fall-through): 04 05 06 07 08 (return/jump).
OPS = {
    0x00: "w", 0x01: "w", 0x02: "w", 0x03: "K", 0x04: "", 0x05: "v", 0x06: "w", 0x07: "w", 0x08: "K",
    0x09: "ww", 0x0a: "ww", 0x0b: "www", 0x0c: "www",
    **{op: "www" for op in range(0x0d, 0x19)},          # if var <cmp> (literal|var) goto
    0x19: "w", 0x1a: "w", 0x1b: "ww", 0x1c: "w", 0x1d: "ww", 0x1e: "ww", 0x1f: "w", 0x20: "w", 0x21: "w",
    0x22: "w", 0x23: "ww", 0x24: "ww",
    **{op: "ww" for op in range(0x25, 0x35)},          # var <arith>= (literal|var)
    0x35: "S", 0x36: "vS", 0x37: "", 0x38: "", 0x39: "", 0x3a: "v", 0x3b: "S", 0x3c: "S", 0x3d: "b", 0x3e: "v",
    0x3f: "", 0x40: "v", 0x41: "", 0x42: "S", 0x43: "v", 0x44: "", 0x45: "vvvv", 0x46: "46", 0x47: "wwvv",
    0x48: "vv", 0x49: "w", 0x4a: "wvw", 0x4b: "wvw", 0x4c: "wvw", 0x4d: "w", 0x4e: "w", 0x4f: "w", 0x50: "",
    0x51: "", 0x52: "vvv", 0x53: "v", 0x54: "v", 0x55: "", 0x56: "",
    0x57: "wb", 0x58: "wb", 0x59: "bw", 0x5a: "bw", 0x5b: "bb", 0x5c: "bw",
    0x5d: "Svvvv", 0x5e: "5e", 0x5f: "S", 0x60: "vv", 0x61: "vv", 0x62: "vv", 0x63: "vvw",
    0x64: "vv", 0x65: "v", 0x66: "v", 0x67: "v", 0x68: "v",
    0x69: "vvv", 0x6a: "vvvv", 0x6b: "vvv", 0x6c: "vvv", 0x6d: "vvvv",
    0x6e: "v", 0x6f: "vv", 0x70: "vv", 0x71: "vvv",
    0x72: "vvvvvvv", 0x73: "wv", 0x74: "wv", 0x75: "v", 0x76: "v", 0x77: "v", 0x78: "ww", 0x79: "vv", 0x7a: "vv",
    0x7b: "v", 0x7c: "v", 0x7d: "bwv", 0x7e: "S", 0x7f: "S", 0x80: "vvvvvvvvv", 0x81: "w", 0x82: "", 0x83: "",
    0x84: "", 0x85: "w", 0x86: "vv",
    0x87: "vvv", 0x88: "vv", 0x89: "vv", 0x8a: "vv", 0x8b: "vv",          # 64-68 on an object (value first)
    0x8c: "wvb", 0x8d: "wvb", 0x8e: "vbw", 0x8f: "vbw", 0x90: "vbb", 0x91: "vbw",  # 57-5c on an object
    0x92: "w", 0x93: "v", 0x94: "v", 0x95: "vv", 0x96: "vv", 0x97: "", 0x98: "vv",
    0xff: "X",
}
# extended ops (0xff <sub>)
XOPS = {
    0x00: "", 0x01: "w", 0x02: "w", 0x03: "", 0x04: "vv", 0x05: "vv", 0x06: "", 0x07: "", 0x08: "v", 0x09: "v",
    0x0a: "vv", 0x0b: "vv", 0x0c: "vv", 0x0d: "d", 0x0e: "vd", 0x0f: "vd", 0x10: "vvS", 0x11: "", 0x12: "b",
    0x13: "", 0x14: "vvvv", 0x15: "vv", 0x16: "", 0x17: "v", 0x18: "vv", 0x19: "", 0x1a: "b", 0x1b: "vvv",
    0x1c: "vd", 0x1d: "vd", 0x1e: "b", 0x1f: "", 0x20: "20", 0x21: "b", 0x22: "ww", 0x23: "23", 0x24: "vv",
    0x25: "vvv", 0x26: "w", 0x27: "vv", 0x28: "vvvv", 0x29: "vvvv", 0x2a: "b", 0x2b: "bb", 0x2c: "b",
    0x2d: "w", 0x2e: "2e", 0x2f: "2f", 0x30: "",
}
# ext 0x2e: picture sub-interpreter (0x80065f40, credits/ending), sub-op byte then:
X2E = {0: "b", 1: "", 2: "wwS", 3: "wwwwwww", 4: "wwwwwww", 5: "www", 6: "", 7: ""}
JUMPS = {0x01: 0, 0x06: 0, 0x07: 0, 0x09: 1, 0x0a: 1, 0x0b: 2, 0x0c: 2,
         **{op: 2 for op in range(0x0d, 0x19)}}
# 08 / ff 20 = switch-goto (default when out of range); 35 = area change (resets the script pointer)
ENDS = {0x04, 0x05, 0x06, 0x07, 0x08, 0x35, 0xff20}

HANDLER_OPS = {0x52}
# operand indexes (into decode()'s `out` list) that hold a script address -> relocate when the file moves.
# Only ops whose operands are all w/v entries: keep it consistent with _addr_values()'s filtered list.
ADDR_FIELDS = {
    0x01: (0,), 0x06: (0,), 0x07: (0,),
    0x09: (1,), 0x0a: (1,), 0x0b: (2,), 0x0c: (2,),
    **{op: (2,) for op in range(0x0d, 0x19)},
    0x4a: (2,), 0x4b: (2,), 0x4c: (2,),
    0x52: (2,), 0x60: (0, 1), 0x69: (2,), 0x6a: (2,), 0x6b: (2,), 0x6c: (2,), 0x6d: (2,),
    0x73: (1,), 0x7b: (0,), 0x7c: (0,), 0x7d: (1,),
}
# ops whose address operand is followed as control flow. Only 0x7b (the thread spawn of the conversation
# blocks) and 0x52 (zone handler): following the rest of ADDR_FIELDS produced bogus decodes in 20 files
# (tools/scn.py check) - they take a runtime value or point at data. They are still relocated.
FOLLOW = {0x52, 0x7B}


class Bad(Exception):
    pass


def value(b, p, info=None):
    t = b[p]
    if t in (0, 1):
        return (t, struct.unpack_from("<H", b, p + 1)[0]), p + 3
    return (t, None), p + 1


def decode(b, p, info=None):
    """-> (op, operands, next). Operands: ('w', n) ('b', n) ('d', n) ('v', (type, n)) ('s', bytes) ...
    info, when given, collects (kind, file_offset_of_value, n) for every scalar operand (relocation)."""
    start = p
    op = b[p]
    p += 1
    sig = OPS.get(op)
    if sig is None:
        raise Bad(f"op {op:02x} at {start:04x}")
    if sig == "X":
        sub = b[p]
        p += 1
        sig = XOPS.get(sub)
        if sig is None:
            raise Bad(f"xop {sub:02x} at {start:04x}")
        op = 0xff00 | sub
    out = []
    for k in {"46": None, "5e": None, "23": None, "2e": None, "2f": None, "20": None}.get(sig, sig) or "":
        p = operand(b, p, k, out, info)
    if sig == "20":                     # jump table: u8 N, var, default target, N x u16 targets
        p = operand(b, p, "b", out, info)
        p = operand(b, p, "w", out, info)
        p = operand(b, p, "w", out, info)
        for _ in range(out[0][1]):
            p = operand(b, p, "w", out, info)
    elif sig == "2e":
        s = b[p]; p += 1; out.append(("b", s))
        if s not in X2E:
            raise Bad(f"ff 2e sub {s:02x} at {start:04x}")
        for k in X2E[s]:
            p = operand(b, p, k, out, info)
    elif sig == "2f":                   # u8; nonzero -> u16 (wait frames)
        s = b[p]; p += 1; out.append(("b", s))
        if s:
            p = operand(b, p, "w", out, info)
    if sig == "46":                     # b mode; 0 -> v, else v v
        mode = b[p]; p += 1; out.append(("b", mode))
        for _ in range(1 if mode == 0 else 2):
            p = operand(b, p, "v", out, info)
    elif sig == "5e":                   # v, u8 N, N x w
        p = operand(b, p, "v", out, info)
        n = b[p]; p += 1; out.append(("b", n))
        for _ in range(n):
            p = operand(b, p, "w", out, info)
    elif sig == "23":                   # u8 sub: 0/1 -> u8, 2 -> u32
        s = b[p]; p += 1; out.append(("b", s))
        if s in (0, 1):
            p = operand(b, p, "b", out, info)
        elif s == 2:
            p = operand(b, p, "d", out, info)
    return op, out, p


def operand(b, p, k, out, info=None):
    if k == "w":
        if info is not None:
            info.append(("w", p, struct.unpack_from("<H", b, p)[0]))
        out.append(("w", struct.unpack_from("<H", b, p)[0])); return p + 2
    if k == "b":
        if info is not None:
            info.append(("b", p, b[p]))
        out.append(("b", b[p])); return p + 1
    if k == "d":
        if info is not None:
            info.append(("d", p, struct.unpack_from("<I", b, p)[0]))
        out.append(("d", struct.unpack_from("<I", b, p)[0])); return p + 4
    if k == "v":
        if info is not None and b[p] in (0, 1):
            info.append(("v", p + 1, struct.unpack_from("<H", b, p + 1)[0]))
        v, p = value(b, p); out.append(("v", v)); return p
    if k == "S":
        if b[p] == 2:
            e = b.index(b"\0", p + 1)
            if info is not None:
                info.append(("S", p + 1, e - p - 1))       # inline string payload
            out.append(("s", b[p + 1:e])); return e + 1
        if info is not None and b[p] in (0, 1):
            info.append(("v", p + 1, struct.unpack_from("<H", b, p + 1)[0]))
        v, p = value(b, p); out.append(("v", v)); return p
    if k == "K":
        p = operand(b, p, "w", out, info)
        p = operand(b, p, "v", out, info)
        n = b[p]; p += 1; out.append(("b", n))
        for _ in range(n):
            p = operand(b, p, "v", out, info)
        return p
    raise ValueError(k)


def fmt(op, out):
    parts = []
    for k, x in out:
        if k == "v":
            parts.append(f"#{x[1]:x}" if x[0] == 0 else f"var{x[1]:x}" if x[0] == 1 else f"t{x[0]}")
        elif k == "s":
            parts.append(repr(x.decode("cp932", "replace")))
        else:
            parts.append(f"{x:x}")
    name = f"{op:02x}" if op < 0x100 else f"ff.{op & 0xff:02x}"
    return name + " " + " ".join(parts)


def targets(op, out):
    """Script addresses this op may jump/call to."""
    t = []
    if op in JUMPS:
        t.append(out[JUMPS[op]][1])
    if op in (0x03, 0x08):
        for k, x in out[1:]:
            if k == "v" and x[0] == 0 and x[1] != 0xFFFF:
                t.append(x[1])
    if op == 0xff20:
        t += [x for _, x in out[2:]]
    if op == 0x5e:                      # registered zone handlers: value, u8 N, N x handler
        t += [x for k, x in out[2:]]
    if op in FOLLOW:                    # 0x52 zone handler, 0x7b thread spawn
        v = out[ADDR_FIELDS[op][-1]][1]
        if v[0] == 0:
            t.append(v[1])
    return t


def dis(b, base, start, end=None):
    p = start
    while p < (end or len(b)):
        try:
            op, out, n = decode(b, p)
        except (Bad, IndexError) as e:
            print(f"{base + p:04x}  ?? {e}")
            return
        print(f"{base + p:04x}  {fmt(op, out)}")
        p = n


_SLOTS = {}


def load_slots(folder="work/orig/mps/SCN"):
    """{NAME: slot} from every op 0x36 (load script into slot) with a literal slot and an inline name."""
    if not _SLOTS:
        for f in Path(folder).glob("*.SCN"):
            b = f.read_bytes()
            ops, _ = walk(b, base_guess(f.stem))
            for op, out, _, _ in ops.values():
                if op == 0x36 and out[0][1][0] == 0 and out[1][0] == "s":
                    name = out[1][1].decode("latin1").upper().split(".")[0]
                    _SLOTS.setdefault(name, set()).add(out[0][1][1])
    return _SLOTS


def base_guess(name):
    s = name.upper()
    if s == "99CMN":
        return 0x4000
    if len(s) == 5:
        return 0
    if len(s) == 7 and s[5:].isdigit():
        return 0x2000
    return 0x5000


def base_of(name):
    """Slot base of a SCN: where an op 0x36 loads it (0x2000 map script, 0x5000 event script), else by name:
    area dispatcher (2 digits + 3 letters) 0, 99CMN 0x4000, area + 2 digits 0x2000, others 0x5000."""
    slots = load_slots().get(name.upper())
    if slots and len(slots) == 1:
        return next(iter(slots))
    return base_guess(name)


def walk(b, base, entries=None, extra=()):
    """Follow control flow from the entry points. -> (ops {addr: (op, out, next, info)}, errors [str]).
    extra: more script addresses to start from (message ops found by scanning a file the walk cannot reach)."""
    ops, errs = {}, []
    if entries is None:   # a script starts with a table of entry jumps (06 w), callers use base + 3*i
        entries, p = [base], 0
        while p + 3 <= len(b) and b[p] == 0x06:
            entries.append(base + p)
            p += 3
    todo = list(entries) + list(extra)
    while todo:
        a = todo.pop()
        while True:
            if a in ops:
                break
            p = a - base
            if not 0 <= p < len(b):
                break
            info = []
            try:
                op, out, n = decode(b, p, info)
            except (Bad, IndexError, struct.error, ValueError) as e:
                if not isinstance(e, Bad) and p >= len(b) - 8:
                    break   # a yield (55) as the file's last byte: the script never resumes past it
                errs.append(f"{a:04x}: {e}")
                break
            ops[a] = (op, out, base + n, info)
            for t in targets(op, out):
                if base <= t < base + len(b):
                    todo.append(t)
            if op in ENDS:
                break
            a = base + n
    starts = set(ops)
    for a, (op, out, n, info) in ops.items():
        for x in range(a + 1, n):
            if x in starts:
                errs.append(f"{x:04x}: op start inside op at {a:04x}")
    return ops, errs


def assemble(b, base, ops, edits=None, relocs=None):
    """Rebuild the file from the walk: ops in address order, every gap copied verbatim.

    edits: {file offset of an op: its new bytes}.
    relocs: {old address: new address} patch every address operand (see _addr_values).
    Returns the new bytes. Without edits and relocs it is byte-identical to b."""
    edits = edits or {}
    items = sorted(ops.items())
    out = bytearray()
    prev_end = 0
    for a, (op, operands, nxt, info) in items:
        start, end = a - base, nxt - base
        if start < prev_end:         # an op inside another op (only while errors remain)
            continue
        if start > prev_end:
            out += b[prev_end:start]
        bad = b[start:end]
        if start in edits:
            bad = edits[start]
        elif relocs:
            bad = bytearray(bad)
            for kind, pos, val in _addr_values(op, info):
                new = relocs.get(val)
                if new is not None:
                    struct.pack_into("<H", bad, pos - start, new)
            bad = bytes(bad)
        out += bad
        prev_end = end
    if prev_end < len(b):
        out += b[prev_end:]
    return bytes(out)


def _addr_values(op, info):
    """(kind, file_offset, value) of this op's address operands.

    `info` lists the scalar operands in read order, so the indexes below are into that filtered list (u8 and
    u32 operands are not in it). Switch and jump-table ops carry one address per entry, handled explicitly."""
    vals = [(k, p, v) for k, p, v in info if k in ("w", "v")]
    if op in (0x03, 0x08):
        return [x for x in vals[1:] if x[2] != 0xFFFF]
    if op == 0xff20:
        return vals[1:]
    if op == 0x5e:
        return vals[1:]
    return [vals[i] for i in ADDR_FIELDS.get(op, ()) if i < len(vals)]


def _segments(b, base, ops):
    """(old_start, old_end, occupies) for every piece of the file in order: op blocks and the gaps between."""
    segs, prev = [], 0
    for a in sorted(ops):
        op, out, nxt, info = ops[a]
        start, end = a - base, nxt - base
        if start < prev:
            continue
        if start > prev:
            segs.append((prev, start, False))
        segs.append((start, end, True))
        prev = end
    if prev < len(b):
        segs.append((prev, len(b), False))
    return segs


def rebuild(b, base, ops, edits=None):
    """Reassemble with edited ops of a new size, relocating every address operand and every data-table u16
    that points at a moved block. edits: {file offset: new bytes for that op}.

    Returns (new bytes, problems). Problems list u16 values in the data that point somewhere the map does not
    explain; a non-empty list means the file has a pointer form this codec does not know yet."""
    edits = edits or {}
    segs = _segments(b, base, ops)
    newpos, layout = {}, {}
    pos = 0
    for start, end, is_op in segs:
        layout[(start, end)] = pos
        for i in range(start, end):
            newpos[i] = pos + (i - start)
        pos += len(edits.get(start, b[start:end])) if is_op else end - start

    def move(addr):
        """old script address -> new script address (or None when it points outside the file)."""
        off = addr - base
        return base + newpos[off] if off in newpos else None

    # every address operand value, so assemble() can patch them
    relocs = {}
    wants = []
    for a, (op, operands, nxt, info) in ops.items():
        for kind, p, val in _addr_values(op, info):
            wants.append(val)
    for v in wants:
        nv = move(v)
        if nv is not None:
            relocs[v] = nv
    new = assemble(b, base, ops, edits=edits, relocs=relocs)

    # data tables inside the gaps hold addresses too (choice-option tables, jump tables). Patch every u16 that
    # equals a moved address; report any that point at a block start we failed to map.
    problems = []
    out = bytearray(new)
    for start, end, is_op in segs:
        if is_op or end - start < 2:
            continue
        base_new = layout[(start, end)]
        delta = base_new - start
        if delta == 0:
            continue
        for i in range(start, end - 1):
            v = int.from_bytes(b[i:i + 2], "little")
            nv = relocs.get(v)
            if nv is not None and nv != v:
                struct.pack_into("<H", out, delta + i, nv)
    return bytes(out), problems


def coverage(b, base, ops):
    """-> (covered bytearray, [(offset, length)]) of the bytes no op covers."""
    cov = bytearray(len(b))
    for a, (op, out, n, info) in ops.items():
        for i in range(max(0, a - base), min(len(b), n - base)):
            cov[i] = 1
    gaps, i = [], 0
    while i < len(b):
        if not cov[i]:
            j = i
            while j < len(b) and not cov[j]:
                j += 1
            gaps.append((i, j - i))
            i = j
        else:
            i += 1
    return cov, gaps


def check(folder="work/orig/mps/SCN"):
    bad = 0
    for f in sorted(Path(folder).glob("*.SCN")):
        b = f.read_bytes()
        base = base_of(f.stem)
        ops, errs = walk(b, base)
        cov, gaps = coverage(b, base, ops)
        gap = sum(n for _, n in gaps)
        print(f"{f.stem:9s} base {base:04x} size {len(b):5d} ops {len(ops):5d} gap {gap:5d} errors {len(errs)}"
              + ("  " + "; ".join(errs[:3]) if errs else ""))
        bad += bool(errs)
    print("files with errors:", bad)
    return bad


def roundtrip(folder="work/orig/mps/SCN"):
    bad = 0
    for f in sorted(Path(folder).glob("*.SCN")):
        b = f.read_bytes()
        base = base_of(f.stem)
        ops, errs = walk(b, base)
        if assemble(b, base, ops) != b:
            print(f"{f.stem}: NOT identical")
            bad += 1
    print("files not identical:", bad)
    return bad


if __name__ == "__main__":
    if sys.argv[1] == "check":
        sys.exit(1 if check() else 0)
    if sys.argv[1] == "roundtrip":
        sys.exit(1 if roundtrip() else 0)
    if sys.argv[1] == "dis":
        f = Path(sys.argv[2])
        b = f.read_bytes()
        base = 0x4000 if f.stem.upper() == "99CMN" else 0
        dis(b, base, int(sys.argv[3], 16) if len(sys.argv) > 3 else 0, int(sys.argv[4], 16) if len(sys.argv) > 4 else None)
